# Generated by Django 3.1.7 on 2021-03-20 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0006_auto_20210320_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='egs_blocked',
            field=models.TextField(blank=True),
        ),
    ]
