# Generated by Django 3.0.7 on 2021-06-02 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0050_z_for_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='sociallink',
            name='ig_token_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]