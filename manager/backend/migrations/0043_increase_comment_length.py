# Generated by Django 3.0.7 on 2021-05-04 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0042_custom_notifications"),
    ]

    operations = [
        migrations.AlterField(
            model_name="momentcomments",
            name="comment",
            field=models.CharField(max_length=1024),
        )
    ]
