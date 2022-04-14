# Generated by Django 3.2.11 on 2022-02-25 16:05

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0113_merge_0111_auto_20220216_1426_0112_auto_20220218_1426'),
    ]

    operations = [

        migrations.CreateModel(
            name='NewCommentStatus',
            fields=[
                ('NewComment_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('flag', models.BooleanField()),
                ('commenter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]