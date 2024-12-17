import boto3
import json
import base64
from assement.src.file_manager.db_client import DynamoDBClient


class FileHandler:
    def __init__(self, bucket_name, endpoint_url=None, table_name=None, aws_access_key_id="test",
                 aws_secret_access_key="test", region_name='us-east-1'):
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.db_client = DynamoDBClient(table_name=table_name)

    def upload(self, event):
        """
        Handles file upload via API Gateway.
        """
        query_params = event.get('queryStringParameters', {})
        image_name = query_params.get('fileName', '')
        metadata = query_params.get('metadata', {})
        if not image_name:
            return {"statusCode": 400, "body": json.dumps({"error": "Imagename is requir."})}

        # Decode the base64-encoded file content
        file_content = base64.b64decode(event['body'])

        # Upload to S3
        try:
            self.s3.put_object(Bucket=self.bucket_name, Key=image_name, Body=file_content)
            self.db_client.write_item(item={"image_id": image_name, "metadata": metadata})
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"File '{image_name}' uploaded successfully."})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

    def download(self, query_params):
        """
        Handles file download via API Gateway.
        """
        image_name = query_params.get('imageName', '')
        if not image_name:
            return {"statusCode": 400, "body": json.dumps({"error": "imageName is required."})}

        try:
            # Generate pre-signed URL for downloading the file
            pre_signed_url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': image_name},
                ExpiresIn=3600  # URL valid for 1 hour
            )
            response = self.db_client.read_item(key={
                'image_id': image_name
            })
            if response['statusCode'] == 404:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": f"Image '{image_name}' not found in metadata storage."})
                }

            response_json = json.loads(response['body'])
            metadata_str = response_json['data']['metadata']

            return {
                "statusCode": 200,
                "body": json.dumps({"downloadUrl": pre_signed_url, "metadata": metadata_str})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error while image download": str(e)})
            }

    def delete_file(self, query_params):
        """
        Handles file deletion from S3 and associated metadata from DynamoDB.
        """
        image_name = query_params.get('imageName', '')
        if not image_name:
            return {"statusCode": 400, "body": json.dumps({"error": "imageName is required."})}

        try:
            # Delete file from S3
            self.s3.delete_object(Bucket=self.bucket_name, Key=image_name)

            # Delete metadata from DynamoDB
            self.db_client.delete_item(key={'image_id': image_name})

            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"File '{image_name}' deleted successfully."})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to delete file '{image_name}': {str(e)}"})
            }
