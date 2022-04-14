import uuid

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType

from ..models import TaggUser


class ReactionType(models.TextChoices):
    LIKE = "LIKE"


class Reaction(models.Model):
    """
    id: UUID for a reaction
    reaction_type:  type of the reaction [LIKE] (Extendable through text choices)
    content_type:   type of the object that was reacted to
    reaction_object_id: Object id of the object that was reacted to [CommentThreads, Comments]
    timestamp: time of reaction

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reaction_type = models.CharField(
        max_length=10, choices=ReactionType.choices, default=ReactionType.LIKE
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    reaction_object_id = models.UUIDField(null=True)
    object = GenericForeignKey("content_type", "reaction_object_id")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["reaction_object_id", "reaction_type"])]
        unique_together = ("reaction_object_id", "reaction_type")


class CommentsReactionList(models.Model):
    """
    User reactions for comment threads
    reaction: reaction object
    actor: TaggUser who reacted
    """

    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    actor = models.ForeignKey(TaggUser, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["reaction"])]
        unique_together = ("reaction", "actor")


class CommentThreadsReactionList(models.Model):
    """
    User reactions for comment threads
    reaction: reaction object
    actor: TaggUser who reacted
    """

    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE)
    actor = models.ForeignKey(TaggUser, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["reaction"])]
        unique_together = ("reaction", "actor")
