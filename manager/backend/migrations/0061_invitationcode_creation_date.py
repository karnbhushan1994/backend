# Generated by Django 3.0.7 on 2021-10-22 21:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0060_revamp_badge'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitationcode',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
