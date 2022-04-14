import json
from datetime import datetime
from json.decoder import JSONDecodeError

from django.conf import settings
from django.contrib import admin, messages
from django.db.models.query_utils import Q
from stream_chat import StreamChat

from .gamification.models import GameProfile

from .widget.models import (
    Widget,
    VideoLinkWidget,
    ApplicationLinkWidget,
)

from .common.constants import (
    APP_STORE_LINK,
    HOMEPAGE,
    INVITE_FRIEND_RESET_DATE,
    SMS_WAITLIST_APPROVED,
)
from .common.notification_manager import handle_notification
from .common.sms_manager import send_sms
from .common.utils import chunks, create_chat_token, update_stream_user_profile
from .discover.models import DiscoverCategory
from .messaging.models import Chat
from .models import (
    BlockedUser,
    CustomPushNotification,
    InviteFriends,
    TaggUser,
    TaggUserMeta,
    InvitedUser,
    VIPUser,
)
from .moments.comments.models import MomentComments
from .moments.models import Moment
from .moments.moment_category.models import MomentCategory
from .moments.moment_category.utils import create_single_moment_category
from .notifications.models import Notification, NotificationType
from .notifications.utils import moment_posted_friend, moments_posted_reminder
from .profile.utils import send_notification_profile_visits
from .serializers import TaggUserSerializer
from .skins.models import Skin
from .skins.utils import create_default_skin
from .social_linking.utils import regenerate_fb_token, regenerate_ig_token
from .suggested_people.models import Badge
from .suggested_people.utils import (
    compute_recommender_feature_values,
    insert_recommender_missing_rows,
)


def regenerate_facebook_token(modeladmin, request, queryset):
    regenerate_fb_token(queryset)


def regenerate_instagram_token(modeladmin, request, queryset):
    regenerate_ig_token(queryset)


def send_notification_moments_posted_reminder_url(modeladmin, request, queryset):
    moments_posted_reminder()


def send_notification_moment_posted_friend_url(modeladmin, request, queryset):
    moment_posted_friend()


def send_notification_custom(modeladmin, request, queryset):
    actor = TaggUser.objects.filter(username="Tagg").first()
    if actor:
        for custom_notification in queryset:
            for user in TaggUser.objects.all():
                handle_notification(
                    NotificationType.DEFAULT, actor, user, custom_notification.message
                )


def populate_badges(modeladmin, request, queryset):
    """
    Populates the list of badges according to BADGES in setting.py
    """

    try:
        new_badges = settings.BADGES
        badges_to_keep = set({})

        # First, store which badges we want to keep (prevents id field issues).
        for badge in new_badges:
            o = Badge.objects.filter(name=badge)
            if o.exists():
                print("Keeping badge: ", o[0].name)
                badges_to_keep.add(o[0].name)

        # Next, delete all the badge entries in the database we wish to remove.
        for badge in Badge.objects.all():
            if badge.name not in badges_to_keep:
                print("Removing badge: ", badge.name)
                badge.delete()

        # Lastly, populate the database with all the new badges.
        for badge in new_badges:
            if f"{badge}" not in badges_to_keep:
                o = Badge.objects.create(name=badge)
                print(f"Added badge: ", o.name)

    except Exception as err:
        print("Error populating badges: ", err)


def populate_discover_categories(modeladmin, request, queryset):
    """
    Populates the list of discover categories according to DISCOVER_CATEGORIES in settings.py.
    """
    try:
        categories = settings.DISCOVER_CATEGORIES.values()
        DiscoverCategory.objects.all().delete()
        for name, category in categories:
            DiscoverCategory.objects.create(name=name, category=category)
            print(f"Added discover category: {name}")
    except Exception as err:
        print("Problem occurred", err)


def send_sms_invite_friends(modeladmin, request, queryset):
    try:
        for invite in queryset:
            try:
                invitation_code = generate_token()
                body = f"""
Hey!

You've been tagged by {invite.inviter_fullname}. Follow the instructions below to skip the line and join them on Tagg!

Sign up and use this code to get in: {invitation_code.hexcode}

{APP_STORE_LINK}
"""
                send_sms(invite.invitee_phone_number, body)
                invite.invited = True
                invite.save()
                print("Sent message to ", invite.invitee_phone_number)
            except Exception as error:
                print(error)
                print("Failed to send message to ", invite.invitee_phone_number)
    except Exception as error:
        print(error)
        print("Something went wrong")


def send_sms_waitlist(modeladmin, request, queryset):
    try:
        for user in queryset:
            try:
                invitation_code = generate_token()
                body = f"""
Hi {user.first_name}, 

Tagg, you’re it!!! Here is your chance to leave the waitlist!
Log in with your username: {user.username} and enter this Invite Code: {invitation_code.hexcode}
If any trouble Dm us on IG @taggapp or email us at support@tagg.id with any questions!

Welcome to T@gg 😊
                """
                send_sms(user.phone_number, body)
                user.taggusermeta.waitlist_invited = True
                user.save()
                print("Sent message to ", user.phone_number)
            except Exception as error:
                print(error)
                print("Failed to send message to", user.phone_number)
    except Exception as error:
        print(error)
        print("Something went wrong")


def assign_chat_token(self, request, queryset):
    """
    Creates chat token for the selected list of users from the Tagguser table
    Stores the tokens in Chat table
    """
    try:
        stream_client = StreamChat(
            api_key=settings.STREAM_API_KEY, api_secret=settings.STREAM_API_SECRET
        )
        created_count = 0
        requested_count = len(queryset)
        for user in queryset:
            chat_token, created = create_chat_token(stream_client, user)
            if created:
                created_count += 1
                print("Created chat token for: ", user.username)
            else:
                print("Error creating chat token for: ", user.username)

        self.message_user(
            request,
            f"{created_count}/{requested_count} chat_tokens were successfully created",
            messages.SUCCESS,
        )

    except Exception as err:
        print(err)
        print("Something went wrong ")


def create_stream_profile(modeladmin, request, queryset):
    """
    Creates stream profiles for selected users from Chat table, in batches of 100
    """
    try:
        stream_client = StreamChat(
            api_key=settings.STREAM_API_KEY, api_secret=settings.STREAM_API_SECRET
        )
        _queryset = queryset.values("user")
        users_queryset = TaggUser.objects.filter(id__in=_queryset)
        users = TaggUserSerializer(users_queryset, many=True).data
        for chunk in chunks(users, 100):
            update_stream_user_profile(stream_client, chunk)
        print("Done!")
    except Exception as err:
        print(err)
        print("Something went wrong ")


def populate_recommender_missing_rows(modeladmin, request, queryset):
    insert_recommender_missing_rows()


def populate_recommender_feature_values(modeladmin, request, queryset):
    compute_recommender_feature_values()


def send_notification_profile_viewed(modeladmin, request, queryset):
    send_notification_profile_visits()


def initialize_invite_friend_creation_date(modeladmin, request, queryset):
    for invite in InviteFriends.objects.all():
        invite.created_date = datetime.strptime(INVITE_FRIEND_RESET_DATE, "%Y-%m-%d")
        invite.save()
    print("Done")


def populate_taggusermeta(modeladmin, request, queryset):
    """
    To copy tagg user meta data from tagguser table to taggusermeta table
    """
    try:
        for user in queryset:
            taggusermeta_obj = TaggUserMeta.objects.update_or_create(
                user=user,
                defaults={
                    "is_onboarded": user.is_onboarded,
                    "waitlist_invited": user.waitlist_invited,
                    "profile_tutorial_stage": user.profile_tutorial_stage,
                    "suggested_people_linked": user.suggested_people_linked,
                },
            )
    except Exception as err:
        print(err)
        print("Something went wrong while populating taggusermeta")


def convert_all_moment_categories_to_json(modeladmin, request, queryset):
    """
    Converts all moment categories from A,B,C to ["A","B","C"].

    Skip ones that are already in json format.
    """
    try:
        for mc in MomentCategory.objects.all():
            try:
                success = json.loads(mc.moments_category)
                if success:
                    print(mc.user_id.username, "-", "Already in json format")
                    continue
            except JSONDecodeError:
                pass
            categories = mc.moments_category
            mc.moments_category = json.dumps(categories.split(","))
            mc.save()
            print(mc.user_id.username, "-", categories, "->", mc.moments_category)
    except Exception as err:
        print(err)
        print("Something went wrong while converting moment categories to json")


def generate_new_code(self, request, queryset):
    token = generate_token()
    self.message_user(
        request,
        f"Success: https://redirect.tagg.id/invite/{token.hexcode}",
        messages.SUCCESS,
    )


def add_homepage_all_users(modeladmin, request, queryset):
    try:
        users = TaggUser.objects.all()
        for user in users:
            if MomentCategory.objects.filter(user_id=user).exists():
                record = MomentCategory.objects.get(user_id=user)
                category_list = json.loads(record.moments_category)
                category_list.insert(0, HOMEPAGE)
                record.moments_category = json.dumps(category_list)
                record.save()
            else:
                create_single_moment_category(user, HOMEPAGE)
    except Exception as err:
        print("Something went wrong while creating homepage for all users")


def create_default_profile_template_all_users(modeladmin, request, queryset):
    try:
        users = TaggUser.objects.all()
        for user in users:
            create_default_skin(user)
    except Exception as err:
        print("Something went wrong while creating homepage for all users")


def waitlist_approve(self, request, queryset):
    success_count = 0

    for user in queryset:

        user.taggusermeta.is_onboarded = True
        user.save()
        inviteObj= InvitedUser.objects.filter(phone_number=user.phone_number)
        if inviteObj:
            InvitedUser.objects.filter(phone_number=user.phone_number).update(status="JOINED")
            for items in inviteObj:
                game_profile_inviter = GameProfile.objects.filter(tagg_user=items.inviter).first()
                if game_profile_inviter:
                    game_profile_inviter.tagg_score = game_profile_inviter.tagg_score+10
                    game_profile_inviter.save()
                    

            game_profile_invited = GameProfile.objects.filter(tagg_user=user).first()
            if game_profile_invited:
                game_profile_invited.tagg_score = game_profile_invited.tagg_score+10
                game_profile_invited.save()
        # Create initial instagram tagg for user to get started with

        # if VideoLinkWidget.objects.filter(owner=user,active=True).count()==0:
        #     VideoLinkWidget.objects.create(
        #         owner=user,
        #         order=0,
        #         type=WidgetType.SOCIAL_MEDIA,
        #         page=HOMEPAGE,
        #         link_type=VideoLinkWidgetType.TIKTOK,
        #         url=user.tiktok_handle,
        #         title=user.instagram_handle,
        #         active=True,
        #     )

        send_sms(user.phone_number, SMS_WAITLIST_APPROVED)
        success_count += 1
    self.message_user(
        request,
        f"SMS sent, {success_count}/{len(queryset)} users were successfully onboarded",
        messages.SUCCESS,
    )


def remove_taggs_on_non_home_pages(self, request, queryset):
    for user in queryset:
        # Delete all widgets for user that are not on Homepage
        Widget.objects.filter(Q(owner=user), ~Q(page=HOMEPAGE), Q(active=True)).update(
            active=False
        )


def remove_recent_moment_taggs(self, request, queryset):
    try:
        # Remove reward from rewards list in gameprofile table
        for game_profile in GameProfile.objects.all():
            rewards_list = json.loads(game_profile.rewards)
            if "CREATE_RECENT_MOMENT_TAGG" in rewards_list:
                rewards_list.remove("CREATE_RECENT_MOMENT_TAGG")
            game_profile.rewards = json.dumps(rewards_list)
            game_profile.save()

        # Remove recent moment tagg from widget table
        Widget.objects.filter(type="RECENT_MOMENT").delete()

    except Exception as err:
        print("Something went wrong while attempting to delete recent moment tagg")


def create_gamification_profile(self, request, queryset):
    try:
        for user in queryset:
            if not GameProfile.objects.filter(tagg_user=user).exists():
                GameProfile.objects.create(tagg_user=user)
    except Exception:
        print("Something went wrong while attempting to create game profile")


def set_current_widgets_to_active(self, request, queryset):
    try:
        Widget.objects.all().update(active=True)
    except Exception:
        print("Something went wrong while attempting to create game profile")


regenerate_facebook_token.short_description = (
    "Regenerate Facebook tokens for existing profiles"
)
regenerate_instagram_token.short_description = (
    "Regenerate Instagram tokens for existing profiles"
)
send_notification_moment_posted_friend_url.short_description = (
    "Send notification: to all friends if posted 2+ moments in the past 2 hours"
)
send_notification_moments_posted_reminder_url.short_description = (
    "Send notification: 3 or more friends posted ≥1 moment in the past 8 hours"
)
send_notification_custom.short_description = "Send notification: to all TaggUsers"
populate_badges.short_description = "Populate Badge DB"
populate_discover_categories.short_description = "Populate DiscoverCategory DB"
send_sms_invite_friends.short_description = "Send sms with invite code"
send_sms_waitlist.short_description = "Send sms with invite code"
assign_chat_token.short_description = "Assign chat tokens"
create_stream_profile.short_description = "Create Stream profile"
populate_recommender_missing_rows.short_description = (
    "Populate missing ROWS in PeopleRecommender DB"
)
populate_recommender_feature_values.short_description = "Populate missing FEATURE VALUES in PeopleRecommender DB (WARNING: run missing ROWs first)"
send_notification_profile_viewed.short_description = "Send notification: profile viewed"
initialize_invite_friend_creation_date.short_description = (
    "Set invite friend objects to 2021/05/01 to reset invite counts"
)
populate_taggusermeta.short_description = "Populate taggusermeta table"
convert_all_moment_categories_to_json.short_description = (
    "Convert all moment categories to json"
)
add_homepage_all_users.short_description = "Add home page for all users"
remove_taggs_on_non_home_pages.short_description = (
    "Remove Taggs on all pages except Home"
)
create_gamification_profile.short_description = "Create gamification profile for user"
set_current_widgets_to_active.short_description = "Set all widgets to active = True"
remove_recent_moment_taggs.short_description = "Remove Recent Moment Taggs"


class TaggUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "university",
        "phone_number",
        "last_login",
        "get_is_onboarded",
    )
    actions = [
        regenerate_facebook_token,
        regenerate_instagram_token,
        send_notification_moments_posted_reminder_url,
        send_notification_moment_posted_friend_url,
        populate_badges,
        populate_discover_categories,
        send_sms_waitlist,
        assign_chat_token,
        populate_recommender_missing_rows,
        populate_recommender_feature_values,
        send_notification_profile_viewed,
        initialize_invite_friend_creation_date,
        populate_taggusermeta,
        convert_all_moment_categories_to_json,
        create_default_profile_template_all_users,
        add_homepage_all_users,
        waitlist_approve,
        remove_taggs_on_non_home_pages,
        create_gamification_profile,
        remove_recent_moment_taggs,
    ]
    search_fields = ("username", "first_name", "last_name")

    def get_is_onboarded(self, obj):
        return obj.taggusermeta.is_onboarded

    get_is_onboarded.short_description = "is_onboarded"
    get_is_onboarded.admin_order_field = "taggusermeta__is_onboarded"


class InviteFriendsAdmin(admin.ModelAdmin):
    list_display = (
        "invitee_phone_number",
        "invitee_first_name",
        "invitee_last_name",
        "inviter_fullname",
        "invited",
    )
    actions = [send_sms_invite_friends]


class CustomPushNotificationAdmin(admin.ModelAdmin):
    list_display = ("message",)
    actions = [send_notification_custom]


class ChatAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_token")
    actions = [
        create_stream_profile,
    ]


class VIPUserAdmin(admin.ModelAdmin):
    list_display = ("phone_number",)


class TaggUserMetaAdmin(admin.ModelAdmin):
    list_display = ("username", "is_onboarded")
    search_fields = ("user__username",)

    def username(self, obj):
        return obj.user.username


class WidgetAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    list_display = ("id", "type", "username", "active")
    actions = [set_current_widgets_to_active]

    def username(self, obj):
        return obj.owner.username


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("user_id",)


admin.site.register(BlockedUser)
admin.site.register(MomentComments)
admin.site.register(MomentCategory, CategoryAdmin)
admin.site.register(Moment)
admin.site.register(Notification)
admin.site.register(TaggUser, TaggUserAdmin)
admin.site.register(InviteFriends, InviteFriendsAdmin)
admin.site.register(Badge)
admin.site.register(CustomPushNotification, CustomPushNotificationAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(VIPUser, VIPUserAdmin)
admin.site.register(TaggUserMeta, TaggUserMetaAdmin)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(VideoLinkWidget, WidgetAdmin)
admin.site.register(ApplicationLinkWidget)
