# Generated by Django 3.0.7 on 2021-03-27 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0036_auto_20210327_0002"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tagguser",
            name="university",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Brown University", "Brown University"),
                    ("Cornell University", "Cornell University"),
                    ("Harvard University", "Harvard University"),
                ],
                max_length=256,
            ),
        ),
    ]
