# Generated by Django 3.0.7 on 2020-10-27 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0005_merge_20201021_1949"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="tagguser",
            name="backend_tag_email_fb295f_idx",
        ),
        migrations.AddField(
            model_name="tagguser",
            name="phone_number",
            field=models.CharField(default="", max_length=12, unique=True),
        ),
        migrations.AddIndex(
            model_name="tagguser",
            index=models.Index(
                fields=["phone_number"], name="backend_tag_phone_n_7c29a0_idx"
            ),
        ),
    ]