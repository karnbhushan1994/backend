# Generated by Django 3.0.7 on 2021-03-27 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0035_merge_20210327_0002"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tagguser",
            name="university",
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
