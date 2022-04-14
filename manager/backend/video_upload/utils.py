import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings


def create_presigned_post(filename):
    """Generate a presigned URL S3 POST request to upload a file

    :param filename: string
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """
    expiration = 3600
    s3 = boto3.client(
        "s3",
        region_name="us-east-2",
        config=Config(signature_version="s3v4"),
    )
    # TODO: want to have the bucket_key be a video_hash not filename, for POC we can leave this.
    bucket_key = filename
    try:
        # see documentation for parameters and response
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.generate_presigned_post
        response = s3.generate_presigned_post(
            settings.S3_VIDEO_QUEUE_BUCKET,
            bucket_key,
            Fields=None,
            Conditions=None,
            ExpiresIn=expiration,
        )

    except ClientError as e:
        logging.error(e)
        return None
    return response
