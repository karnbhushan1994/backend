import logging
import random
import re
from io import BytesIO

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from django.conf import settings
from linkpreview import link_preview
from PIL import Image

from ..common import hash_manager
from ..common.image_manager import upload_image


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
        config=Config(s3={"addressing_style": "virtual"}),
        aws_access_key_id=settings.S3_PATH_ACCESS,
        aws_secret_access_key=settings.S3_PATH_SECRET,
    )
    # TODO: want to have the bucket_key be a video_hash not filename, for POC we can leave this.
    bucket_key = filename
    try:
        # see documentation for parameters and response
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.generate_presigned_post
        response = s3.generate_presigned_post(
            settings.S3_BUCKET,
            bucket_key,
            Fields=None,
            Conditions=None,
            ExpiresIn=expiration,
        )

    except ClientError as e:
        logging.error(e)
        return None
    return response


def uploadThumbnail(url, uid, link_type):
    # link_preview can throw large file exception
    try:
        image_url = getImageUrl(url, link_type)
        if link_type == "AMAZON" or image_url == None:
            logging.info("Image not found in preview")
            return ""

        # img_content in bytes
        img_content = getImageContent(image_url)
        if img_content == "":
            logging.info("Could not retrieve img from img_url")
            return ""
        # pil_image = Image object
        pil_image = Image.open(BytesIO(img_content))

        # temp filename to use when saving file in local mem
        image_name = "tmp_img.jpeg"

        # Filepath into s3 including appended filename
        filepath = generateFilePath(url, uid)

        upload_image(pil_image, filepath, image_name, False)
        # grab object url and return
        return getThumbnailUrl(url, uid)
    except Exception as e:
        logging.info(e)
        return ""


# Fuction determines how to retrieve image url and returns it
def getImageUrl(url, link_type):
    url = unShortenUrl(url)
    if link_type == "YOUTUBE":
        image_url = handleYoutube(url)
    elif link_type == "TIKTOK":
        image_url = getImageManually(url)
    else:
        previewObj = link_preview(url)
        image_url = previewObj.image
    return image_url


# Fetches img from img_url and returns img in bytes
def getImageContent(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return ""


# Generates the filepath including the filename that will be saved in s3
def generateFilePath(url, uid):
    prepath = hashPrePath(url, uid)
    filename = f"{settings.S3_WIDGETS_FOLDER}/{prepath}"
    filename = "thumbnails/" + filename + "-thumbnail.jpg"
    return filename


# Generates a hash of the combination of a prepath defined by url and uid
def hashPrePath(url, uid):
    hm = hash_manager.HashManager(16, settings.S3_PATH_SECRET.encode("utf-8"))

    def hash_str(x):
        return hm.sign(x.encode()).decode()

    prepath = f"{uid}/{url}/"
    return hash_str(prepath)


# function that retrieves the resource location in s3
def getThumbnailUrl(url, uid):
    """
    Example location url resource location
    https://tagg-dev.s3.us-east-2.amazonaws.com/thumbnails//widgets/{prepath}-thumbnail.jpg
    """
    prepath = hashPrePath(url, uid)
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{settings.S3_THUMBNAILS_FOLDER}/{settings.S3_WIDGETS_FOLDER}/{prepath}-thumbnail.jpg"


# Youtube handler utilizng noembed
def handleYoutube(url):
    if re.match(
        "^(http|https)?:\/\/(?:www\.)?youtube\.com(?:.*|\/)\?(?=.*=((\w|-){3}))(?:\S+)?$",
        url,
        re.IGNORECASE,
    ):
        data = requests.get(f"https://noembed.com/embed?url={url}").json()
        return data["thumbnail_url"]
    elif re.search("channel", url) or re.search("user", url):
        return ""
    else:
        uri = url.replace("youtu", "youtube").replace(".be/", ".com/watch?v=")
        data = requests.get(f"https://noembed.com/embed?url={uri}").json()
        return data["thumbnail_url"]


# Handler which fetches the html content of the url and parses for the image meta data
def getImageManually(url):
    userAgents = settings.USER_AGENTS
    ua = userAgents.copy()
    random.shuffle(ua)
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
        "User-Agent": ua[0],
    }
    req = requests.get(url, headers)
    html = BeautifulSoup(req.content, "html.parser")
    image = get_image(html)
    return image


# Parses html for image
def get_image(html):
    """Scrape share image."""
    image = None
    if html.find("meta", property="image"):
        image = html.find("meta", property="image").get("content")
    elif html.find("meta", property="og:image"):
        image = html.find("meta", property="og:image").get("content")
    elif html.find("meta", property="twitter:image"):
        image = html.find("meta", property="twitter:image").get("content")
    elif html.find("img", src=True):
        image = html.find("img").get("src")
    return image


# Returns the unshortened url if applicable
def unShortenUrl(url):
    session = requests.Session()  # so connections are recycled
    resp = session.head(url, allow_redirects=True)
    if resp.url:
        return resp.url
    return url
