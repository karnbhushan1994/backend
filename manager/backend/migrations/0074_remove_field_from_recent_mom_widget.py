# Generated by Django 3.0.7 on 2021-11-15 20:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0073_merge_20211120_0209"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="recentmomentwidget",
            name="some_data",
        ),
    ]
