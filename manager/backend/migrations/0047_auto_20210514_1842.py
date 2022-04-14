# Generated by Django 3.0.7 on 2021-05-14 18:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0046_merge_20210514_1842"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitefriends",
            name="invite_code",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="backend.InvitationCode",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="invitefriends",
            unique_together={("invitee_phone_number", "invite_code")},
        ),
    ]