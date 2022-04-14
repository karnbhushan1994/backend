from django.db.models import Q

from .models import CommentThreads, MomentComments


def is_acceptable_comment_length(comment):
    if len(comment) > 256:
        return False
    return True


def get_moment_comments_count(moment_id, request_user=None):
    def sum_thread(parent_comment):
        if request_user:
            return CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
                ~Q(commenter__blocker__blocked=request_user),
                ~Q(commenter__blocked__blocker=request_user),
            ).count()
        else:
            return CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
            ).count()

    # User should not be able to view comments of the user they are blocked by
    if request_user:
        parent_comments = MomentComments.objects.filter(
            Q(moment_id=moment_id),
            ~Q(commenter__blocker__blocked=request_user),
            ~Q(commenter__blocked__blocker=request_user),
        )
    else:
        parent_comments = MomentComments.objects.filter(Q(moment_id=moment_id))

    return (
        sum([sum_thread(parent_comment) for parent_comment in parent_comments])
        + parent_comments.count()
    )


def get_moment_comment_preview(moment_id, request_user):
    return (
        MomentComments.objects.filter(
            Q(moment_id=moment_id), ~Q(commenter__blocker__blocked=request_user)
        )
        .order_by("-date_created")
        .first()
    )
