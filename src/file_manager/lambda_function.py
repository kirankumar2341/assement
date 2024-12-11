import json

from assement.src.file_manager.file_handler import FileHandler
from assement.src.file_manager.file_search import FileSearch

BUCKET_NAME = "image-bucket"
table_name = "ImageMetadata"
end_point ="http://localhost:4566"
imageHandler = FileHandler(bucket_name=BUCKET_NAME,table_name = table_name,endpoint_url=end_point)
file_search = FileSearch(bucket_name=BUCKET_NAME,endpoint_url=end_point)

def lambda_handler(event, context):
    # log event
    print("Event: ", json.dumps(event))

    http_method = event.get('httpMethod', '')
    query_params = event.get('queryStringParameters', {})
    action = query_params.get('action', '')

    if http_method == "POST" and action == "upload":
        return handle_upload(event)
    elif http_method == "GET" and action == "download":
        return handle_download(query_params)
    elif http_method == "GET" and action == "list":
        return handle_list_images(query_params)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid request. Use 'upload', 'download', or 'list'."})
        }

def handle_upload(event):
    """
    Handles file upload via API Gateway.
    """
    return imageHandler.upload(event)

def handle_download(query_params):
    """
    Handles file download via API Gateway.
    """
    return imageHandler.download(query_params)

def handle_list_images(query_params):
    """
    Lists all images in the S3 bucket with filters for prefix and size range.
    """
    prefix = query_params.get('prefix', '')  # Filter by prefix (e.g., folder or name pattern)
    min_size = int(query_params.get('minSize', '0'))  # Minimum file size in bytes
    max_size = int(query_params.get('maxSize', '0'))  # Maximum file size in bytes (0 means no max size)

    if prefix != '':
        return file_search.prefix_search(prefix)
    if int(min_size) != 0 or int(max_size)!=0 :
        return file_search.size_search(min_size, max_size)
    else:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str("Invalid search request.")})
        }

