from .models import Skin, TemplateType


class ActiveSkinException(Exception):
    pass


def create_default_skin(user):
    if not Skin.objects.filter(owner=user, active=True).exists():
        Skin.objects.create(
            owner=user,
            primary_color="#FFFFFF",
            secondary_color="#698DD3",
            template_type=TemplateType.TWO,
            active=True,
        )
