# Generated by Django 3.1.7 on 2021-03-20 03:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0003_auto_20210320_0910'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='platform',
            name='platform_id',
        ),
    ]
