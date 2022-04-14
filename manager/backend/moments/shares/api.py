import logging

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...profile.utils import allow_to_view_private_content
from ..models import Moment
from .models import MomentShares
from .utils import record_moment_share


class MomentShareViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentShareViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        """
        Record share on moment

        Args:
            moment_id: Moment Id for which share must be added

        Returns:
            Share count after user has shared the moment
        """
        try:
            data = request.data

            if "moment_id" not in data:
                return Response("moment is required", 400)

            moment = Moment.objects.get(moment_id=data.get("moment_id"))

            if not allow_to_view_private_content(request.user, moment.user_id):
                return Response(
                    "User unauthorized to view content",
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Add view if requester is not the moment poster themselves
            # if not request.user == moment.user_id:
            record_moment_share(moment, request.user)

            share_count = MomentShares.objects.filter(moment_shared=moment).count()

            # self.logger.info("test TOTAL: {}".format(share_count))

            return Response({"share_count": share_count}, status=status.HTTP_200_OK)

        except Moment.DoesNotExist as err:
            self.logger.error(err)
            return Response("Moment id not found", 400)

        except Exception as error:

            self.logger.exception(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
