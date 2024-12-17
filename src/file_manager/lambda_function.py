import json
from assement.src.file_manager.file_handler import FileHandler
from assement.src.file_manager.file_search import FileSearch

BUCKET_NAME = "image-bucket"
TABLE_NAME = "ImageMetadata"
ENDPOINT_URL = "http://localhost:4566"

# Initialize the FileHandler and FileSearch globally for reuse
image_handler = FileHandler(bucket_name=BUCKET_NAME, table_name=TABLE_NAME, endpoint_url=ENDPOINT_URL)
file_search = FileSearch(bucket_name=BUCKET_NAME, endpoint_url=ENDPOINT_URL)

def lambda_handler(event, context):
    """
    AWS Lambda function handler for managing image uploads, downloads, and searches.
    """
    try:
        # Log the incoming event
        print("Received event:", json.dumps(event))

        http_method = event.get('httpMethod', '').upper()
        query_params = event.get('queryStringParameters', {}) or {}
        action = query_params.get('action', '').lower()

        # Route the request based on HTTP method and action
        if http_method == "POST" and action == "upload":
            return handle_upload(event)
        elif http_method == "GET" and action == "download":
            return handle_download(query_params)
        elif http_method == "GET" and action == "list":
            return handle_list_images(query_params)
        elif http_method == "GET" and action == "delete":
            return handle_delete_file(query_params)
        else:
            return create_response(400, {"error": "Invalid request. Use 'upload', 'download', or 'list'."})
    except Exception as e:
        print(f"Error occurred: {e}")
        return create_response(500, {"error": str(e)})

def handle_upload(event):
    """
    Handles file upload via API Gateway.
    """
    try:
        return image_handler.upload(event)
    except Exception as e:
        print(f"Upload error: {e}")
        return create_response(500, {"error": "Image upload failed.", "details": str(e)})

def handle_download(query_params):
    """
    Handles file download via API Gateway.
    """
    try:
        return image_handler.download(query_params)
    except Exception as e:
        print(f"Download error: {e}")
        return create_response(500, {"error": "Image download failed.", "details": str(e)})

def handle_delete_file(query_params):
    """
    Handles file deletion via API Gateway.
    """
    return image_handler.delete_file(query_params)

def handle_list_images(query_params):
    """
    Lists all images in the S3 bucket with filters for prefix and size range.
    """
    try:
        prefix = query_params.get('prefix', '')  # Filter by prefix (e.g., folder or name pattern)
        min_size = query_params.get('minSize', '0')
        max_size = query_params.get('maxSize', '0')

        # Validate size parameters
        try:
            min_size = int(min_size)
            max_size = int(max_size)
        except ValueError:
            return create_response(400, {"error": "minSize and maxSize must be integers."})

        # Execute the appropriate search
        if prefix:
            return file_search.prefix_search(prefix)
        elif min_size > 0 or max_size > 0:
            return file_search.size_search(min_size, max_size)
        else:
            return create_response(400, {"error": "Invalid search request. Provide a prefix or size range."})
    except Exception as e:
        print(f"List images error: {e}")
        return create_response(500, {"error": "Image listing failed.", "details": str(e)})

def create_response(status_code, body):
    """
    Utility function to create HTTP responses.
    """
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"}
    }
