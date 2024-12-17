This code addresses the following scenarios:

File Upload

File Download

File Search

Design Improvements:

File Upload Limitations:

The current implementation has a limitation with the API Gateway's 10 MB payload size limit. For image files larger than 10 MB, we need to implement S3 Multipart Upload to handle the upload efficiently.

DynamoDB Schema Optimization:

The current DynamoDB design includes only two columns. To enhance query flexibility and enable faster searches, we plan to add new Global Secondary Indexes (GSIs) based on query patterns.


