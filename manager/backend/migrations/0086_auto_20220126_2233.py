# Generated by Django 3.0.7 on 2022-01-26 22:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0085_gameprofile_rewards"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfileViews",
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
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "profile_visited",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile_visited",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "profile_visitor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="profile_visitor",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="profileviews",
            index=models.Index(
                fields=["profile_visited", "timestamp"],
                name="backend_pro_profile_e92525_idx",
            ),
        ),
    ]
