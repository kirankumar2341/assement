"""
Note this code to take from difference sources
"""

import boto3
import json
import zipfile
import os
import boto3
from botocore.exceptions import ClientError

# LocalStack endpoint
LOCALSTACK_ENDPOINT = "http://localhost:4566"

# Initialize clients
s3 = boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT, region_name='us-east-1')
dynamodb = boto3.client('dynamodb', endpoint_url=LOCALSTACK_ENDPOINT, region_name='us-east-1')
lambda_client = boto3.client('lambda', endpoint_url=LOCALSTACK_ENDPOINT, region_name='us-east-1')
api_gateway = boto3.client('apigateway', endpoint_url=LOCALSTACK_ENDPOINT)



# S3 Bucket Setup
def create_s3_bucket(bucket_name):
    s3.create_bucket(Bucket=bucket_name)
    print(f"S3 bucket '{bucket_name}' created.")


# DynamoDB Table Setup
def create_dynamodb_table(table_name):
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
    )
    print(f"DynamoDB table '{table_name}' created.")


# Lambda Function Setup
def create_lambda_function(function_name, bucket_name, key_name):
    # Create a ZIP file for the Lambda function
    function_code = """
import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    print("Event Received:", json.dumps(event))
    return {"statusCode": 200, "body": "Lambda Executed Successfully!"}
"""
    zip_file = "lambda_function.zip"
    with zipfile.ZipFile(zip_file, 'w') as zf:
        zf.writestr("lambda_function.py", function_code)

    # Upload the ZIP to S3
    with open(zip_file, "rb") as f:
        s3.put_object(Bucket=bucket_name, Key=key_name, Body=f)
    os.remove(zip_file)
    print(f"Uploaded Lambda code to S3 bucket '{bucket_name}' with key '{key_name}'.")

    # Create the Lambda function
    lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.9',
        Role='arn:aws:iam::123456789012:role/lambda-role',
        Handler='lambda_function.lambda_handler',
        Code={'S3Bucket': bucket_name, 'S3Key': key_name},
        Timeout=15,
        MemorySize=128,
    )
    print(f"Lambda function '{function_name}' created.")




def create_table_localstack(table_name):
    # Create a DynamoDB client that points to LocalStack
    dynamodb = boto3.resource(
        'dynamodb',
        region_name='us-east-1',
        endpoint_url='http://localhost:4566'  # LocalStack endpoint for DynamoDB
    )

    try:
        # Create the ImageStorage table in LocalStack
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'image_id',
                    'KeyType': 'HASH'  # Partition key
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'image_id',
                    'AttributeType': 'S'  # String type for image_id
                },
                {
                    'AttributeName': 'meta_data',
                    'AttributeType': 'M'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TagsIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'tags',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'upload_timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'FileFormatIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'file_format',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'upload_timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ]
        )
        print("Table created successfully.")
        return table
    except ClientError as e:
        print(f"Error creating table: {e}")
        return None

def create_api_gateway(api_name, lambda_function_arn):
    try:
        # Create the API
        api_response = api_gateway.create_rest_api(
            name=api_name,
            description='API for Image Upload',
            version='v1'
        )
        api_id = api_response['id']
        print(f"API Gateway '{api_name}' created.")

        # Get the root resource
        resources = api_gateway.get_resources(restApiId=api_id)
        root_resource_id = resources['items'][0]['id']

        # Create the resource
        resource_response = api_gateway.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='upload-image'
        )
        resource_id = resource_response['id']
        print(f"Resource 'upload-image' created.")

        # Create the POST method for the resource
        api_gateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE'
        )
        print(f"POST method created for 'upload-image'.")

        # Integrate API Gateway with Lambda
        api_gateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            integrationHttpMethod='POST',
            type='AWS_PROXY',
            uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations'
        )
        print(f"API Gateway integrated with Lambda.")

        # Grant permission to API Gateway to invoke Lambda
        lambda_client.add_permission(
            FunctionName=lambda_function_arn,
            StatementId='api-gateway-permission',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com'
        )
        print(f"Lambda permission granted to API Gateway.")

        # Deploy the API
        api_gateway.create_deployment(
            restApiId=api_id,
            stageName='dev'
        )
        print(f"API Gateway deployed to stage 'dev'.")

    except ClientError as e:
        print(f"Error creating API Gateway: {e}")




def main():
    # Resource names
    bucket_name = "image-bucket"
    table_name = "Metadata"
    lambda_function_name = "ImageLambdaFunction"
    lambda_code_key = "1lambda_function.zip"

    # Create resources
    create_s3_bucket(bucket_name)
    create_dynamodb_table(table_name)
    create_lambda_function(lambda_function_name, bucket_name, lambda_code_key)
    create_table_localstack(table_name)


if __name__ == "__main__":
    main()
