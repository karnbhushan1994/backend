# Generated by Django 3.0.7 on 2021-10-01 20:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0057_remove_legacy_usermeta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taggusermeta',
            name='is_private',
        ),
    ]
