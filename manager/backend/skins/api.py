import logging

from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..gamification.constants import TAGG_SCORE_ALLOTMENT

from ..gamification.utils import increase_tagg_score

from .models import Skin, TemplateType
from .serializers import SkinSerializer
from .utils import ActiveSkinException, create_default_skin


class SkinViewSet(ModelViewSet):
    serializer_class = SkinSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "patch", "get", "delete"]
    queryset = Skin.objects.all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        request.data["owner"] = request.user.id

        # Increment tagg score if a profile color is being changed
        active_skin = Skin.objects.filter(active=True, owner=request.user).first()
        if (
            active_skin.primary_color != request.data["primary_color"]
            or active_skin.secondary_color != request.data["secondary_color"]
        ) and (
            ("template_type" not in request.data)
            or active_skin.template_type == request.data["template_type"]
        ):
            increase_tagg_score(
                request.user, TAGG_SCORE_ALLOTMENT["PROFILE_EDIT_COLOR"]
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if "owner" in request.data:
            raise ValidationError({"owner": "Not allowed to update"})
        if "active" in request.data and not request.data["active"]:
            raise ValidationError(
                {"active": "Not allowed to set active to false, only true"}
            )
        return super().update(request, *args, **kwargs)

    def list(self, request):
        skins = Skin.objects.filter(owner=request.user)
        return Response(SkinSerializer(skins, many=True).data, 200)

    def destroy(self, request, pk):
        skin = Skin.objects.get(id=pk)
        if skin.active is True:
            raise ActiveSkinException
        return super().destroy(request, pk)

    @action(detail=False, methods=["get"])
    def skin_count(self, request):
        if "user_id" not in request.GET:
            raise ValidationError({"user_id": "This field is required."})
        skins = Skin.objects.filter(owner=request.GET.get("user_id"))
        uniqueTemplates = len(skins)
        return Response({"count": uniqueTemplates})

    @action(detail=False, methods=["get"])
    def active_skin(self, request):
        if "user_id" not in request.GET:
            raise ValidationError({"user_id": "This field is required."})
        create_default_skin(request.user)
        active_skin = Skin.objects.filter(
            owner=request.GET.get("user_id"), active=True
        )[0]
        return Response(SkinSerializer(active_skin).data)

    @receiver(pre_save, sender=Skin)
    def keep_single_active_skin(sender, instance, **kwargs):
        if instance.active:
            # Retrieve all current profile skins for the user
            current_skins = Skin.objects.filter(owner=instance.owner, active=True)

            # Make current skins inactive
            for skin in current_skins:
                skin.active = 0
                skin.save()
