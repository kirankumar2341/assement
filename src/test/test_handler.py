import json
import base64
import pytest
from unittest.mock import patch
from assement.src.file_manager.lambda_function import lambda_handler  # Adjust the import as needed

@pytest.fixture
def mock_context():
    """Mock Lambda context."""
    return {}

@pytest.fixture
def upload_event():
    """Fixture for the file upload event."""
    file_name = "example_image.jpg"
    file_content = b"example file content"
    file_metadata = {
        "format": "JPEG",
        "size": 2048,
        "dimensions": {"width": 1920, "height": 1080},
        "uploaded_at": "2024-12-01T10:00:00Z"
    }
    file_content_base64 = base64.b64encode(file_content).decode('utf-8')
    return {
        "httpMethod": "POST",
        "queryStringParameters": {
            "action": "upload",
            "fileName": file_name,
            "metadata": json.dumps(file_metadata)
        },
        "body": file_content_base64,
        "headers": {"Content-Type": "application/json"}
    }

@pytest.fixture
def download_event():
    """Fixture for the file download event."""
    return {
        "httpMethod": "GET",
        "queryStringParameters": {
            "action": "download",
            "imageName": "example_image.jpg"
        },
        "headers": {"Content-Type": "application/json"}
    }

@pytest.fixture
def list_files_event():
    """Fixture for listing files event."""
    return {
        "httpMethod": "GET",
        "queryStringParameters": {
            "action": "list",
            "prefix": "example"
        },
        "headers": {"Content-Type": "application/json"}
    }

@pytest.fixture
def delete_event():
    """Fixture for deleting a file event."""
    return {
        "httpMethod": "GET",
        "queryStringParameters": {
            "action": "delete",
            "imageName": "example_image.jpg"
        },
        "headers": {"Content-Type": "application/json"}
    }

@patch("assement.src.file_manager.lambda_function.FileHandler.upload")
def test_upload(mock_upload, upload_event, mock_context):
    """Test file upload."""
    mock_upload.return_value = {"statusCode": 200, "body": json.dumps({"message": "File uploaded successfully."})}
    response = lambda_handler(upload_event, mock_context)
    assert response["statusCode"] == 200
    mock_upload.assert_called_once()

@patch("assement.src.file_manager.lambda_function.FileHandler.download")
def test_download(mock_download, download_event, mock_context):
    """Test file download."""
    mock_download.return_value = {"statusCode": 200, "body": json.dumps({"downloadUrl": "http://example.com/file.jpg", "metadata": {}})}
    response = lambda_handler(download_event, mock_context)
    assert response["statusCode"] == 200

@patch("assement.src.file_manager.lambda_function.FileSearch.prefix_search")
def test_list_files(mock_list_files, list_files_event, mock_context):
    """Test listing files."""
    mock_list_files.return_value = {"statusCode": 200, "body": json.dumps({"files": ["example1.jpg", "example2.jpg"]})}
    response = lambda_handler(list_files_event, mock_context)
    assert response["statusCode"] == 200

@patch("assement.src.file_manager.lambda_function.FileHandler.delete_file")
def test_delete_file(mock_delete_file, delete_event, mock_context):
    """Test deleting a file."""
    mock_delete_file.return_value = {"statusCode": 200, "body": json.dumps({"message": "File deleted successfully."})}
    response = lambda_handler(delete_event, mock_context)
    assert response["statusCode"] == 200
    mock_delete_file.assert_called_once()
