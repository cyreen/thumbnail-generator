# Thumbnail Generator Lambda

AWS Lambda function that generates a thumbnail for a visual (such as picture or clip) from an S3 folder and uploads it on a separate thumbnail folder.

## How It Works

1. A new image or video file is uploaded to the content S3 bucket as normally.
2. An S3 event triggers the Lambda function.
3. The Lambda function:
   - Downloads the uploaded file.
   - Generates a thumbnail (resizing or compressing the image).
   - Uploads the thumbnail to the `thumbnails/` folder in the same bucket.
