# Generated by Django 3.0.7 on 2021-01-31 07:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("backend", "0024_auto_20210127_2304"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="content_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="notification_object",
            field=models.UUIDField(null=True),
        ),
    ]
