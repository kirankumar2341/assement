import boto3
import json
import os
from botocore.exceptions import ClientError

# AWS Config for LocalStack
aws_config = {
    "endpoint_url": "http://localhost:4566",
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
    "region_name": "us-east-1"
}

# Initialize clients
s3 = boto3.client("s3", **aws_config)
dynamodb = boto3.client("dynamodb", **aws_config)
lambda_client = boto3.client("lambda", **aws_config)
iam = boto3.client("iam", **aws_config)
api_gateway = boto3.client("apigateway", **aws_config)

lambda_client.add_permission(
    FunctionName="ImageLambdaFunction",
    StatementId="api-gateway-permission",
    Action="lambda:InvokeFunction",
    Principal="apigateway.amazonaws.com"
)

# S3 Bucket Setup
def create_s3_bucket(bucket_name):
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"S3 bucket '{bucket_name}' created.")
    except ClientError as e:
        print(f"Error creating S3 bucket: {e}")


# DynamoDB Table Setup
def create_dynamodb_table(table_name):
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
        )
        print(f"DynamoDB table '{table_name}' created.")
    except ClientError as e:
        print(f"Error creating DynamoDB table: {e}")


# IAM Role Setup for Lambda
def create_lambda_role():
    try:
        role_name = "lambda-execution-role"
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
        )
        print(f"Created IAM role '{role_name}' with ARN: {role_response['Role']['Arn']}")
        return role_response['Role']['Arn']
    except ClientError as e:
        print(f"Error creating IAM role: {e}")
        return None


# Lambda Function Setup
def create_lambda_function(function_name, role_arn, bucket_name, key_name):
    try:
        zip_file = "/Users/kiranin/Downloads/monty/assement/src/file_manager/lambda_function_zip.zip"

        # Check if the zip file exists
        if not os.path.exists(zip_file):
            print(f"Error: The file '{zip_file}' does not exist.")
            return

        # Upload the ZIP to S3
        with open(zip_file, "rb") as f:
            s3.put_object(Bucket=bucket_name, Key=key_name, Body=f)
        print(f"Uploaded Lambda code to S3 bucket '{bucket_name}' with key '{key_name}'.")

        # Create the Lambda function
        lambda_response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,  # Use the IAM role ARN
            Handler='lambda_function.lambda_handler',
            Code={'S3Bucket': bucket_name, 'S3Key': key_name},
            Timeout=15,
            MemorySize=128,
        )
        print(f"Lambda function '{function_name}' created. Response: {lambda_response}")
    except ClientError as e:
        print(f"Error creating Lambda function: {e}")


# API Gateway Setup
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


# Main setup function
def main():
    # Resource names
    bucket_name = "image-bucket"
    table_name = "Metadata"
    lambda_function_name = "ImageLambdaFunction"
    lambda_code_key = "lambda_function.zip"

    # Create resources
    create_s3_bucket(bucket_name)
    create_dynamodb_table(table_name)

    # Create Lambda role and use it to create the Lambda function
    role_arn = create_lambda_role()
    if role_arn:
        create_lambda_function(lambda_function_name, role_arn, bucket_name, lambda_code_key)

    # Create API Gateway and link it to Lambda function
    create_api_gateway("image_store", lambda_function_name)


if __name__ == "__main__":
    main()
