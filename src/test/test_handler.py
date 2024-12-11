import json
import base64

# Assuming lambda_handler is the function being tested
from assement.src.file_manager.lambda_function import lambda_handler  # Adjust the import according to your actual Lambda code

# Test for Uploading a file
def test_upload():
    # Sample file content and metadata
    file_name = "example_image.jpg"
    file_content = b"example file content"  # Simulating the file content as bytes
    file_metadata = {
        "format": "JPEG",
        "size": 2048,
        "dimensions": {
            "width": 1920,
            "height": 1080
        },
        "uploaded_at": "2024-12-01T10:00:00Z"
    }

    # Encoding file content to base64
    file_content_base64 = base64.b64encode(file_content).decode('utf-8')

    # Event for the file upload
    event = {
        "httpMethod": "POST",
        "queryStringParameters": {
            "action": "upload",
            "fileName": file_name,
            "metadata": json.dumps(file_metadata)  # Passing metadata as a JSON string
        },
        "body": file_content_base64,  # Base64 encoded file content
        "headers": {
            "Content-Type": "application/json"
        }
    }

    # Simulate invoking the lambda_handler
    context = {}  # Empty context for this example, extend if needed
    response = lambda_handler(event, context)
    assert response["statusCode"] == 200

# Test for Downloading a file
def test_download():
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "action": "download",
            "imageName": "example_image.jpg"
        },
        "headers": {
            "Content-Type": "application/json"
        }
    }

    # Simulate invoking the lambda_handler function call
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200

# Test for Listing files with a prefix
def test_list_files():
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "action": "list",
            "prefix": "example"  # Prefix to search in S3 bucket
        },
        "headers": {
            "Content-Type": "application/json"
        }
    }

    # Simulating the lambda_handler function call
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200


# Call the test functions
test_upload()
test_download()
test_list_files()
