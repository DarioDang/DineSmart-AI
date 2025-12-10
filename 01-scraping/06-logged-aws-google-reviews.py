import boto3
from botocore.exceptions import NoCredentialsError, ClientError 
import os 

# Configuration 
bucket_name = "dario-ai-agent-reviews"
folder = "google-reviews"
files_to_upload = [
    "data/google-reviews/final/chc-google-reviews.json",
    "data/google-reviews/final/chc-google-reviews.parquet"
]

# Initalize S3 client
s3 = boto3.client('s3')

for file_name in files_to_upload:
    try:
        # Construct S3 object key (path inside bucket)
        s3_key = f"{folder}/{os.path.basename(file_name)}"

        # Upload file
        s3.upload_file(file_name, bucket_name, s3_key)
        print(f"Uploaded: {file_name} → s3://{bucket_name}/{s3_key}")

    except FileNotFoundError:
        print(f"File not found: {file_name}")
    except NoCredentialsError:
        print("AWS credentials not found. Please configure them with `aws configure`.")
    except ClientError as e:
        print(f"Upload failed for {file_name}: {e}")