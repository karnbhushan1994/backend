# Generated by Django 3.0.7 on 2022-03-28 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0151_auto_20220328_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inviteduser',
            name='fullname',
            field=models.CharField(blank=True, default='', max_length=110),
        ),
    ]
