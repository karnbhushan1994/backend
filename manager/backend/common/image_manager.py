import asyncio
import logging

from ..skins.models import Skin, TemplateType
from ..common import hash_manager
import os
from collections import defaultdict

import boto3
from django.conf import settings
from PIL import Image

from .image_validator import IllegalImageException, legal_image

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (120, 120)


def upload_to_s3(bucket_name, bucket_file_path, file_path):
    """Uploads a file to an S3 bucket using boto3

    Args:
        bucket_name (str): Name of S3 bucket
        bucket_file_path (str): Path to file in the bucket, including file name
        file_path (str): Local path to file, including file name

    Returns:
        bool: True if upload was succesful, False otherwise
    """
    try:
        s3 = boto3.resource("s3")
        s3.Object(bucket_name, bucket_file_path).upload_file(Filename=file_path)
        return True
    except Exception:
        logging.exception("Problem uploading to S3")
        return False


def remove_from_s3(filepath):
    try:
        s3 = boto3.resource("s3")
        s3.Object(settings.S3_BUCKET, filepath).delete()
        return True
    except Exception as error:
        logging.exception(error)
        return False


def upload_image(image, filename, image_name="tmp_im", upload_thumbnail=False):
    """Uploads image to cloud
    Args:
        image (Image): The image object
        filename (str): Filename of the image
        upload_thumbnail (boolean): Whether to upload a thumbnail for the image or not

    Raises:
        ImageUploadException: If fails to upload, reason in message
    """
    # If image name is not passed in then use tmp_im as the name
    # When trying to use multiple threads to save different images, we cannot use the same image name and hence had to bring in the image_name field
    # If image name is not passed in then use tmp_im as the name
    # When trying to use multiple threads to save different images, we cannot use the same image name and hence had to bring in the image_name field
    # Tested for PNG, JPG, JPEG and HEIC image formats

    try:
        image = image.convert("RGB")
        if image_name == "tmp_im":
            image.save(image_name, format="JPEG")
        else:
            image.save(image_name)

        if not upload_to_s3(settings.S3_BUCKET, filename, image_name):
            raise ImageUploadException("An upload error has occurred")

        if upload_thumbnail:
            filename, ext = os.path.splitext(filename)
            filename = "thumbnails/" + filename + "-thumbnail.jpg"
            if image.width < image.height:
                box_width = image.width
                box = (0, image.height / 2 - (box_width / 2), box_width, box_width)
            else:
                box_width = image.height
                box = (image.width / 2 - (box_width / 2), 0, box_width, box_width)
            image = image.resize(THUMBNAIL_SIZE, box=box)

            if image_name == "tmp_im":
                image.save(image_name, format="JPEG")
            else:
                image.save(image_name)

            if not upload_to_s3(settings.S3_BUCKET, filename, image_name):
                raise ImageUploadException("An upload error has occurred")
    finally:
        os.remove(image_name)
    return


def upload_images_async(data, upload_thumbnail=False):
    """Uploads image to cloud asynchronously

    Args: (A list of lists with the following as expected values for each list)
        image_name (str) : The image name
        image (Image): The image object
        filename (str): Folder structure to be followed on S3

    Returns:
        A list of images expected to be uploaded with upload status
    """
    image_upload_status = defaultdict(lambda: "Failed")
    try:

        queue = (upload_image_helper(d, upload_thumbnail) for d in data)

        image_upload_status = dict(asyncio.run(async_requests(*queue)))
    except Exception:
        logging.exception("Problem uploading to S3")
    finally:
        return image_upload_status


async def async_requests(*args):
    return await asyncio.gather(*args)


async def upload_image_helper(data, upload_thumbnail=False):
    """Helper that provides an abstraction to the actual upload_image method

    Args: (A list of arguments with the following as expected values)
       image_name (str) : The image name
       image (Image): The image object
       filename (str): Folder structure to be followed on S3

    Returns:
       Image name with upload status
    """
    image_name, image_content, filename = data
    try:
        image = Image.open(image_content)
        upload_image(
            image=image,
            filename=filename,
            image_name=image_content.name,
            upload_thumbnail=upload_thumbnail,
        )
        return image_name, "Success"
    except IllegalImageException:
        logging.exception("Illegal Image")
        return image_name, exception_response[IllegalImageException]
    except ImageUploadException:
        logging.exception("Image upload exception")
        return image_name, exception_response[ImageUploadException]
    except Exception as err:
        logging.exception("Some problem uploading the image")
        return image_name, exception_response["default"]


def generate_s3_image_filepaths(images, prepath):
    """Generate s3 filepaths for a given list of image object.
    * E.g. s3://bucket/folder/hash
    * hash is derived from prepath + filename + ext

    Args:
        images : (dict {key(str) : InMemoryUploadedFile}) Image files
        prepath : (str)

    Returns:
        dict {key(str) : hashes(str)} the full filepath of image for s3
    """
    hashes = {}
    # The HashManager object was brought in to deal with creating a hash for the image path
    # If we do so we can keep web_crawlers from leveraging any patterns in the way we structure image_storage.
    hm = hash_manager.HashManager(16, settings.S3_PATH_SECRET.encode("utf-8"))

    def hash_str(x):
        return hm.sign(x.encode()).decode()

    for image_key, image_object in images.items():
        filename = prepath + str(image_object.name)
        name_splits = image_object.name.split(".")
        ext = name_splits[1] if len(name_splits) > 1 else "jpg"
        hashes[image_key] = f"{settings.S3_MOMENTS_FOLDER}/{hash_str(filename)}.{ext}"

    return hashes


def moment_thumbnail_url(resource_id):
    """
    https://tagg-dev.s3.us-east-2.amazonaws.com/thumbnails/moments/{resource_id}-thumbnail.jpg
    """
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{settings.S3_THUMBNAILS_FOLDER}/{settings.S3_MOMENTS_FOLDER}/{resource_id}-thumbnail.jpg"


def profile_pic_url(resource_id):
    """
    https://tagg-dev.s3.us-east-2.amazonaws.com/smallProfilePicture/{resource_id}-thumbnail.jpg
    """
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{settings.S3_SMALL_PROFILE_PIC_FOLDER}/spp-{resource_id}.jpeg"


def profile_thumbnail_url(resource_id):
    """
    https://tagg-dev.s3.us-east-2.amazonaws.com/thumbnails/smallProfilePicture/{resource_id}-thumbnail.jpg
    """
    # logger.info("Trying to get skin for user: {}".format(resource_id))
    active_skin = Skin.objects.filter(owner__id=resource_id, active=True).first()
    if active_skin:
        subfolder = f"{settings.S3_LARGE_PROFILE_PIC_FOLDER if active_skin.template_type == TemplateType.THREE else settings.S3_SMALL_PROFILE_PIC_FOLDER}"
        filename_prefix = (
            f"{'lpp' if active_skin.template_type == TemplateType.THREE else 'spp'}"
        )
        return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{settings.S3_THUMBNAILS_FOLDER}/{subfolder}/{filename_prefix}-{resource_id}-thumbnail.jpg"
    subfolder = f"{settings.S3_SMALL_PROFILE_PIC_FOLDER}"
    filename_prefix = (
        f"{'spp'}"
    )
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{settings.S3_THUMBNAILS_FOLDER}/{subfolder}/{filename_prefix}-{resource_id}-thumbnail.jpg"


def header_pic_url(resource_id):
    """
    https://tagg-dev.s3.us-east-2.amazonaws.com/largeProfilePicture/{resource_id}-thumbnail.jpg
    """
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/largeProfilePicture/lpp-{resource_id}.jpeg"


class ImageUploadException(Exception):
    pass


exception_response = {
    IllegalImageException: "Bad Image",
    ImageUploadException: "Image Upload Failed",
    "default": "Unknown Error",
}
