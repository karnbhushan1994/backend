from datetime import datetime, timedelta
from ..models import TaggUser
from django.db.models import Q, Count

# Not used
# def new_to_tagg(user):
#     return TaggUser.objects.filter(
#         Q(date_joined__gte=datetime.now() - timedelta(days=2)),
#         ~Q(blocker__blocked=user),
#         ~Q(id=user.id),
#         Q(is_onboarded=True)).order_by('?')


# Replaced by Suggested People
# def people_you_may_know(user):
#     return TaggUser.objects.filter(
#         ~Q(requested__requester=user),
#         ~Q(requester__requested=user),
#         ~Q(blocker__blocked=user),
#         ~Q(id=user.id),
#         Q(is_onboarded=True)).order_by('?')


def get_trending_users(user):
    return TaggUser.objects.filter(
        # Include users who are onboarded.
        Q(taggusermeta__is_onboarded=True),
        # Include users from the same school.
        Q(university=user.university),
        # Include users who have commented recently.
        Q(moment__momentcomments__date_created__gte=datetime.now() - timedelta(days=3)),
        # Exclude anyone who has blocked the user.
        ~Q(blocker__blocked=user),
        # Exclude the querying user then order descending by number of comments.
        ~Q(id=user.id)).annotate(c=Count('moment__momentcomments')).order_by('-c')


def get_class_year_users(user, year):
    return TaggUser.objects.filter(
        # Include users who are onboarded.
        Q(taggusermeta__is_onboarded=True),
        # Include users from the same school.
        Q(university=user.university),
        # Include users from given class year.
        Q(university_class=year),
        # Exclude anyone who has blocked the user.
        ~Q(blocker__blocked=user),
        # Exclude the querying user then shuffle the result.
        ~Q(id=user.id),
    ).order_by("?")


def discover_query(category):
    if "end" in category:
        return get_trending_users
    elif "18" in category:
        return lambda user: get_class_year_users(user, 2018)
    elif "19" in category:
        return lambda user: get_class_year_users(user, 2019)
    elif "20" in category:
        return lambda user: get_class_year_users(user, 2020)
    elif "21" in category:
        return lambda user: get_class_year_users(user, 2021)
    elif "22" in category:
        return lambda user: get_class_year_users(user, 2022)
    elif "23" in category:
        return lambda user: get_class_year_users(user, 2023)
    elif "24" in category:
        return lambda user: get_class_year_users(user, 2024)
    else:
        raise Exception("Unknonwn discover category")
