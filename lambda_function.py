import boto3
import os
import tempfile
import subprocess
from PIL import Image

s3_client = boto3.client('s3')

# Define file extensions for images and videos
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv']


def lambda_handler(event, context):
    # Get S3 bucket and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # If 'my-pictures' is NOT in the key, skip this object
    if 'pictures' not in object_key:
        print(f"Skipping: {object_key} — doesn't contain 'pictures'")
        return {'statusCode': 200, 'body': 'Skipped: key does not contain pictures'}

    # Skip thumbnails folder to avoid recursion
    if object_key.startswith('thumbnails/'):
        print(f"Skipping thumbnail generation for {object_key}")
        return {'statusCode': 200, 'body': 'Skipped thumbnail generation'}

    _, ext = os.path.splitext(object_key.lower())

    with tempfile.TemporaryDirectory() as tmpdirname:
        download_path = os.path.join(tmpdirname, os.path.basename(object_key))
        s3_client.download_file(bucket_name, object_key, download_path)

        if ext in IMAGE_EXTENSIONS:
            generate_image_thumbnail(download_path, bucket_name, object_key, tmpdirname)
        elif ext in VIDEO_EXTENSIONS:
            generate_video_thumbnail(download_path, bucket_name, object_key, tmpdirname)
        else:
            print(f"Unsupported file type for {object_key}")
            return {'statusCode': 400, 'body': f"Unsupported file type: {ext}"}

    return {'statusCode': 200, 'body': f"Thumbnail generated for {object_key}"}


def generate_image_thumbnail(input_path, bucket_name, object_key, tmpdirname):
    with Image.open(input_path) as img:
        img.thumbnail((1280, 720))
        thumbnail_path = os.path.join(tmpdirname, f"thumbnail-{os.path.basename(object_key)}")
        img.save(thumbnail_path)

        thumbnail_key = f"thumbnails/{os.path.basename(object_key)}"
        s3_client.upload_file(thumbnail_path, bucket_name, thumbnail_key)
        print(f"Image thumbnail uploaded to {thumbnail_key}")


def generate_video_thumbnail(input_path, bucket_name, object_key, tmpdirname):
    # Output thumbnail file (PNG)
    thumbnail_filename = f"thumbnail-{os.path.basename(object_key)}.png"
    thumbnail_path = os.path.join(tmpdirname, thumbnail_filename)

    # Use FFmpeg to extract a frame at 1 second (adjust as needed)
    ffmpeg_cmd = [
        './opt/ffmpeg/ffmpeg',  # Path to FFmpeg binary in the Lambda Layer
        '-i', input_path,
        '-ss', '00:00:01.000',
        '-vframes', '1',
        '-vf', 'scale=720:-1',  # Scale width to 720px, maintain aspect ratio
        thumbnail_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating video thumbnail: {e}")
        return

    # Upload the thumbnail
    thumbnail_key = f"thumbnails/{os.path.basename(object_key)}.png"
    s3_client.upload_file(thumbnail_path, bucket_name, thumbnail_key)
    print(f"Video thumbnail uploaded to {thumbnail_key}")
