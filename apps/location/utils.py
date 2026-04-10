import boto3
from botocore.exceptions import ClientError
from django.conf import settings


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",  
    )


def ensure_bucket_exists():
    """
    Bucket mavjud bo'lmasa avtomatik yaratadi
    va public-read policy qo'yadi
    """
    client = get_minio_client()
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    try:
        client.head_bucket(Bucket=bucket)
        print(f"✓ Bucket '{bucket}' allaqachon mavjud")
    except ClientError:
        client.create_bucket(Bucket=bucket)

        policy = f'''{{
            "Version": "2012-10-17",
            "Statement": [{{
                "Effect": "Allow",
                "Principal": {{"AWS": ["*"]}},
                "Action": ["s3:GetObject"],
                "Resource": ["arn:aws:s3:::{bucket}/*"]
            }}]
        }}'''
        client.put_bucket_policy(Bucket=bucket, Policy=policy)
        print(f"✓ Bucket '{bucket}' yaratildi va public qilindi")