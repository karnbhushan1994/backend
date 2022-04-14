from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0085_gameprofile_rewards'),
    ]

    operations = [
        migrations.AddField(
            model_name='genericlinkwidget',
            name='background_url',
            field=models.CharField(max_length=8192, null=True),
        ),
    ]