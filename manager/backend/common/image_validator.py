from math import isclose
from django.conf import settings


def check_image_dimensions(image, max_width, max_height):
    """Checks if an image's dimensions fall within a certain width and height
    Args:
        im (Image): An Image object whose dimensions are to be checked
        max_width (int): The maximum width allowed for the image
        max_height (int): The maximum height allowed for the image
    Returns:
        bool: True if the image passes width and height checks, False otherwise
    """

    return image.width <= max_width and image.height <= max_height


def check_image_ratio(image, target_ratio, tolerance=0.01):
    """Checks if an image's aspect ratio is close to a target aspect ratio
    Args:
        im (Image): An Image object whose aspect ratio is to be checked
        target_ratio (float): The target aspect ratio, specified by "width / height" e.g. 4/3 for a 4:3 aspect ratio
        tolerance (float): Optional; the relative tolerance for discrepancies between the image and target aspect ratios (default is 0.01)
    Returns:
        bool: True if the image ratio is close enough to the target ratio, False otherwise
    """
    image_ratio = image.width / image.height
    return isclose(image_ratio, target_ratio, rel_tol=tolerance)


def legal_image(image):
    """Checks if the image follows our guidelines
    Args:
        image (Image): The image object
    Raises:
        IllegalImageException: If it fails any check, reason in message
    """
    if not check_image_dimensions(image, settings.MAX_WIDTH, settings.MAX_HEIGHT):
        raise IllegalImageException(
            f"Image dimensions exceed limits of {settings.MAX_WIDTH} x {settings.MAX_HEIGHT}"
        )
    if not check_image_ratio(image, settings.RATIO_WIDTH / settings.RATIO_HEIGHT):
        raise IllegalImageException(
            f"Image must have {settings.RATIO_WIDTH}:{settings.RATIO_HEIGHT} ratio."
        )


class IllegalImageException(Exception):
    pass
