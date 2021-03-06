# Generated by Django 3.0.7 on 2021-11-05 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0062_merge_20211105_2047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationlinkwidget',
            name='link_type',
            field=models.CharField(choices=[('SPOTIFY', 'Spotify'), ('SOUNDCLOUD', 'Soundcloud'), ('APPLE_MUSIC', 'Apple Music'), ('APPLE_PODCAST', 'Apple Podcast'), ('POSHMARK', 'Poshmark'), ('DEPOP', 'Depop'), ('ETSY', 'Etsy'), ('SHOPIFY', 'Shopify'), ('AMAZON', 'Amazon'), ('APP_STORE', 'App Store')], max_length=32),
        ),
        migrations.AlterField(
            model_name='applicationlinkwidget',
            name='url',
            field=models.CharField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='genericlinkwidget',
            name='thumbnail_url',
            field=models.CharField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='genericlinkwidget',
            name='url',
            field=models.CharField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='videolinkwidget',
            name='thumbnail_url',
            field=models.CharField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='videolinkwidget',
            name='url',
            field=models.CharField(max_length=8192),
        ),
    ]
