import json
import boto3

class FileSearch:
    def __init__(self, bucket_name, endpoint_url=None, aws_access_key_id=None, aws_secret_access_key=None, region_name='us-east-1'):
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,

        )

    def prefix_search(self, prefix,limit = 30):
        """

        :param prefix:  image prefix
        :param limit:  limit the search results
        :return:
        """

        try:
            # List objects in the bucket
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = response.get('Contents', [])

            filtered_files = [
                {
                    "key": file['Key'],
                    "size": file['Size'],
                    "last_modified": file['LastModified'].isoformat()
                }
                for file in files
            ]

            return {
                "statusCode": 200,
                "body": json.dumps({"files": filtered_files[:limit]})
            }
        except Exception as e:
            print(str(e)) # log
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
    def size_search(self,min_size,max_size,prefix,limit = 30):
            """
            Lists all images in the S3 bucket with filters for prefix and size range.
            """
            min_size = int(query_params.get('minSize', '0'))  # Minimum file size in bytes
            max_size = int(query_params.get('maxSize', '0'))  # Maximum file size in bytes (0 means no max size)

            try:
                # List objects in the bucket
                response = self.s3.list_objects_v2(Bucket=self.bucket_name)
                files = response.get('Contents', [])

                # Apply size filters
                filtered_files = [
                    {
                        "key": file['Key'],
                        "size": file['Size'],
                        "last_modified": file['LastModified'].isoformat()
                    }
                    for file in files
                    if file['Size'] >= min_size and (max_size == 0 or file['Size'] <= max_size)
                ]

                return {
                    "statusCode": 200,
                    "body": json.dumps({"files": filtered_files[:30]})
                }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)})
                }

