# Generated by Django 3.0.7 on 2021-02-26 23:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0029_auto_20210212_2143"),
    ]

    operations = [
        migrations.RenameField(
            model_name="tagguser",
            old_name="is_validated",
            new_name="is_onboarded",
        ),
    ]
