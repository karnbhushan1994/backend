from datetime import datetime
import logging
from turtle import mode
import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz
from rest_framework.authtoken.models import Token
import django.utils.timezone

from .common.constants import BIO_MAX_LENGTH, GENDER_MAX_LENGTH, UNIVERSITY_MAX_LENGTH


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kargs):
    if created:
        Token.objects.create(user=instance)


class TaggUserManager(BaseUserManager):
    def __init__(self, *args, **kwargs):
        super(TaggUserManager, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create_user(
        self,
        first_name,
        last_name,
        email,
        phone_number,
        username,
        password,
        gender,
        birthday,
        instagram_handle,
        tiktok_handle,
    ):

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            username=username,
            password_log="",
            dob=birthday,
            instagram_handle=instagram_handle,
            gender=gender,
            tiktok_handle=tiktok_handle,
            profile_visit_count=0,
        )
        user.clean()
        user.set_password(password)
        user.password_log = user.password
        user.save()
        return user


class ProfileTutorialStage(models.IntegerChoices):
    """
    Three stages
    SHOW_TUTORIAL_VIDEOS: User has not seen profile video tutorials
    SHOW_STEWIE_GRIFFIN: User has viewed video tutorial, User must click Explore and view TaggShop
    SHOW_POST_MOMENT_1: User has viewed TaggShop [COMPLETE]
    SHOW_POST_MOMENT_2: [COMPLETE]
    """

    SHOW_TUTORIAL_VIDEOS = 0
    SHOW_STEWIE_GRIFFIN = 1
    SHOW_POST_MOMENT_1 = 2
    TRACK_LOGIN_AFTER_POST_MOMENT_1 = 3
    SHOW_POST_MOMENT_2 = 4
    COMPLETE = 5


class DMViewStage(models.IntegerChoices):
    """
    Three stages
    NOT_VIEWED_ALL_MOMENTS: User has not viewed all moments on DM, provided for the day
    VIEWED_ALL_MOMENTS: User has reached the last moment provided for the day
    REVISITING_DM: User has watched all moments and logged back into the app for second session
    """

    NOT_VIEWED_ALL_MOMENTS = 0
    VIEWED_ALL_MOMENTS = 1
    REVISITING_DM = 2


# legacy
class SuggestedPeopleLinked(models.IntegerChoices):
    """
    Three stages :
        Stage 1 : suggested_people_linked == 0 [Hasn't attempted linking suggested people]
        Stage 2 : suggested_people_linked == 1 [Uploaded picture]
        Stage 3 : suggested_people_linked == 2 [Watched swipe tutorial]
    """

    INITIAL = 0
    PICTURE_UPLOADED = 1
    FINAL_TUTORIAL = 2


class TrueOrFalse(models.IntegerChoices):
    FALSE = (0,)
    TRUE = 1


class rewardBlock(models.TextChoices):
    BLOCKED = "BLOCKED"
    UNBLOCKED = "UNBLOCKED"

class invitedStatus(models.TextChoices):
    INVITE = "INVITE"
    INVITED = "INVITED"
    JOINED =  "JOINED"

class TaggUser(AbstractUser):
    # Account information fields.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=60, unique=True, default="")
    phone_number = models.CharField(max_length=12, unique=True, default="")
    username = models.CharField(max_length=30, unique=True)
    password_log = models.CharField(max_length=128, default="")

    # Profile information fields.
    biography = models.CharField(max_length=BIO_MAX_LENGTH, blank=True)
    website = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(default=None, null=True)
    gender = models.CharField(max_length=GENDER_MAX_LENGTH, blank=True)
    dob = models.CharField(max_length=15, blank=True)
    instagram_handle = models.CharField(max_length=64, blank=True)
    tiktok_handle = models.CharField(max_length=8192, blank=True)
    reward = models.CharField(
        choices=rewardBlock.choices, null=True, max_length=50, blank=True
    )
    thumbnail_enable = models.CharField(
        choices=rewardBlock.choices, default="BLOCKED",
        null=True, max_length=50, blank=True
    )
    # Possible choices for university. We're currently storing "XXXX University"
    # in the field, which is space-consuming. TODO: create a University model, &
    # relate it to TaggUser using a foreign key, or make shorter abbreviations &
    # store it as a field, as for suggested_people_linked.
    BROWN = "Brown University"
    CORNELL = "Cornell University"
    HARVARD = "Harvard University"
    SCHOOLS = [BROWN, CORNELL, HARVARD]
    SCHOOL_CHOICES = [(school, school) for school in SCHOOLS]
    university = models.CharField(
        max_length=UNIVERSITY_MAX_LENGTH, choices=SCHOOL_CHOICES, blank=True
    )
    university_class = models.IntegerField(default=2021, blank=False)
    profile_visit_count = models.IntegerField(default=0)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = TaggUserManager()

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["username"]),
            models.Index(fields=["phone_number"]),
        ]


class TaggUserMeta(models.Model):
    user = models.OneToOneField(
        TaggUser,
        related_name="taggusermeta",
        on_delete=models.CASCADE,
        primary_key=True,
    )

    # Waitlist information fields.
    is_onboarded = models.BooleanField(default=False)
    waitlist_invited = models.BooleanField(default=False)
    #background_permission = models.BooleanField(default=False)
    profile_tutorial_stage = models.IntegerField(
        choices=ProfileTutorialStage.choices,
        default=ProfileTutorialStage.SHOW_TUTORIAL_VIDEOS,
    )
    
    # legacy, not used
    suggested_people_linked = models.IntegerField(
        choices=SuggestedPeopleLinked.choices, default=SuggestedPeopleLinked.INITIAL
    )

    last_seen_notifications = models.DateTimeField(auto_now_add=True)
    permission_completed=models.BooleanField(default=False)
    contact_permission=models.BooleanField(default=False)
    location_permission=models.BooleanField(default=False)
    notification_permission=models.BooleanField(default=False)
    # To track user's viewing stage on discover moments
    dm_view_stage = models.IntegerField(
        choices=DMViewStage.choices, default=DMViewStage.NOT_VIEWED_ALL_MOMENTS
    )
    timestamp_dm_view_stage = models.DateTimeField(
        default=django.utils.timezone.now
    )
    background_gradient_permission = models.BooleanField(default=False)
    tab_permission = models.BooleanField(default=False)
    class Meta:
        indexes = [models.Index(fields=["user"])]


@receiver(post_save, sender=TaggUser)
def create_tagg_user_meta(sender, instance, created, **kwargs):
    if created:
        TaggUserMeta.objects.create(user=instance)


@receiver(post_save, sender=TaggUser)
def save_tagg_user_meta(sender, instance, **kwargs):
    instance.taggusermeta.save()


class BlockedUserManager(BaseUserManager):
    def validate_data(self, body):
        errors = {}
        if not "blocked" in body or len(body["blocked"]) == 0:
            errors["blocked"] = "Blocker Id is required"

        return errors


class BlockedUser(models.Model):
    blocked = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="blocked"
    )
    blocker = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="blocker"
    )

    objects = BlockedUserManager()

    class Meta:
        unique_together = ("blocked", "blocker")


class WaitlistUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=12, unique=True, default="")


class InviteFriends(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitee_phone_number = models.CharField(max_length=12, unique=True, default="")
    invitee_first_name = models.CharField(max_length=50)
    invitee_last_name = models.CharField(max_length=50)
    inviter_fullname = models.CharField(max_length=110, default="")
    inviter = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    invited = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["invitee_phone_number"])]


class CustomPushNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.CharField(max_length=256)


class VIPUser(models.Model):
    phone_number = models.CharField(max_length=12, unique=True, primary_key=True)

class InvitedUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=12, unique=True, default="")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    fullname = models.CharField(max_length=110, default="",blank=True)
    inviter = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    status=models.CharField(
        max_length=256, choices=invitedStatus.choices, blank=True
    )    
    created_date = models.DateTimeField(auto_now_add=True)