import json
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..common.validator import check_is_valid_parameter, get_response
from ..serializers import TaggUserSerializer


class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(ReportViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            body = json.loads(request.body)

            if not check_is_valid_parameter("resource_id", body):
                return get_response(data="resource_id is required", type=404)
            if not check_is_valid_parameter("type", body):
                return get_response(data="type is required", type=404)
            if not check_is_valid_parameter("reason", body):
                return get_response(data="reason is required", type=404)

            report_data = {
                "reporter_id": request.user.id,
                "resource_id": body["resource_id"],
                "report_type": body["type"],
                "report_reason": body["reason"],
            }

            mail_subject = "User Reported a Content"
            mail_body = """
            Reporter: {reporter_id}
            Resource ID: {resource_id}
            Type: {report_type}
            Reason: {report_reason}
            """.format(
                **report_data
            )

            email = EmailMessage(
                mail_subject, mail_body, to=[settings.REPORT_RECIPIENT]
            )
            email.send()

            return get_response(data="", type=200)
        except Exception:
            msg = "There was a problem sending a report"
            self.logger.exception(msg)
            return get_response(data=msg, type=500)

    serializer_class = TaggUserSerializer
