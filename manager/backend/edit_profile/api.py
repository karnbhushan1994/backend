import logging

from PIL import Image
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.image_manager import ImageUploadException, upload_image
from ..common.image_validator import IllegalImageException, legal_image
from ..common.validator import FieldException, get_response, validate_field
from ..models import TaggUser
from ..serializers import TaggUserSerializer
from ..social_linking.models import SocialLink
from .utils import VALID_IMAGE_KEYS, VALID_PROFILE_KEYS, update_field


class EditProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(EditProfileViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def partial_update(self, request, pk=None):
        try:
            user = TaggUser.objects.filter(id=pk)
            social = SocialLink.objects.filter(user_id=pk)

            if not user:
                self.logger.error("Unable to find the user")
                return get_response("Unable to find the user", type=500)

            if str(user[0].id) != pk:
                self.logger.error("Unauthorized request")
                return get_response("Unauthorized", type=401)

            # initialize response dict with default value
            response_dict = {}
            for key in VALID_IMAGE_KEYS + VALID_PROFILE_KEYS:
                response_dict[key] = "Not updated"

            # handle profile image update requests
            files = request.FILES
            for image_name in files:
                if image_name not in VALID_IMAGE_KEYS:
                    continue
                try:
                    image = Image.open(files.get(image_name), "r")
                    legal_image(image)
                    upload_image(
                        image,
                        filename=f"{image_name}/{image_name[0]}pp-{pk}.jpeg",
                        upload_thumbnail=(True),
                    )
                    response_dict[image_name] = "Updated"
                except IllegalImageException as e:
                    self.logger.exception("Illegal Image")
                    return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
                except ImageUploadException as e:
                    self.logger.exception("Image Upload Exception")
                    return Response(
                        str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                except Exception:
                    self.logger.exception("Some problem while uploading image")
                    return Response(
                        "Image error", status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # handle profile info update requests
            form = request.POST

            for field in form:
                if field not in VALID_PROFILE_KEYS:
                    continue
                try:
                    validate_field(field)(form[field])
                    update_field(field, user, social)(form[field])
                    response_dict[field] = "Updated"
                except FieldException as error:
                    self.logger.error(error)
                    response_dict["error"] = str(error)
                    break
                except Exception:
                    self.logger.exception(
                        "Something went wrong with your profile info!"
                    )
                    response_dict[
                        "error"
                    ] = "Something went wrong with your profile info!"
                    break

            if "error" in response_dict:
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

            s = (
                status.HTTP_400_BAD_REQUEST
                if "error" in response_dict
                else status.HTTP_200_OK
            )

            return Response(response_dict, status=s)

        except Exception as error:
            self.logger.exception(error)
            return get_response("Request failed with unknown reason", type=500)

    serializer_class = TaggUserSerializer
