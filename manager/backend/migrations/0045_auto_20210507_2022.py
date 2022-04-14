# Generated by Django 3.0.7 on 2021-05-07 20:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0044_auto_20210507_1844"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommentThreadsReactionList",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="backend.Reaction",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="commentthreadsreactionlist",
            index=models.Index(
                fields=["reaction"], name="backend_com_reactio_d4171c_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="commentthreadsreactionlist",
            unique_together={("reaction", "actor")},
        ),
    ]