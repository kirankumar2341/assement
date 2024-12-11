import boto3
from botocore.exceptions import ClientError
import json

class DynamoDBClient:
    def __init__(self, table_name, region_name='us-east-1', aws_access_key_id="test", aws_secret_access_key="test"):
        self.table_name = table_name
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url="http://localhost:4566"
        )
        self.table = self.dynamodb.Table(table_name)

    def write_item(self, item):
        """
        :param item: Dictionary containing the item
        :return: response
        """
        try:
            response = self.table.put_item(Item=item)
            return {"statusCode": 200, "body": json.dumps({"message": "Item successfully written to DynamoDB", "response": response})}
        except ClientError as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    def read_item(self, key):
        """
        Reads an item from the DynamoDB table using the primary key.
        :param key: Dictionary containing the key to look up the item.
        :return: response
        """
        try:
            response = self.table.get_item(Key=key)
            if 'Item' in response:
                return {"statusCode": 200, "body": json.dumps({"message": "Item found", "data": response['Item']})}
            else:
                return {"statusCode": 404, "body": json.dumps({"error": "Item not found"})}
        except ClientError as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    def delete_item(self, key):
        """
        Deletes an item from the DynamoDB table.
        :param key: Dictionary containing the key to delete the item.
        :return: response from DynamoDB
        """
        try:
            response = self.table.delete_item(Key=key)
            return {"statusCode": 200, "body": json.dumps({"message": "Item successfully deleted", "response": response})}
        except ClientError as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
