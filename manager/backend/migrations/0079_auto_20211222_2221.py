# Generated by Django 3.0.7 on 2021-12-22 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0078_auto_20211209_0141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skin',
            name='primary_color',
            field=models.CharField(max_length=7),
        ),
        migrations.AlterField(
            model_name='skin',
            name='secondary_color',
            field=models.CharField(max_length=7),
        ),
    ]
