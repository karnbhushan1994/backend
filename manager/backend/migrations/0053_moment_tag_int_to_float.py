# Generated by Django 3.0.7 on 2021-07-13 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0052_merge_20210609_1851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='momenttag',
            name='x',
            field=models.FloatField(blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='momenttag',
            name='y',
            field=models.FloatField(blank=True, default=0),
        ),
    ]
