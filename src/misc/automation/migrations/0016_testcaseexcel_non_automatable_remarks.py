# Generated by Django 3.1.7 on 2021-03-21 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0015_testcaseexcel'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcaseexcel',
            name='non_automatable_remarks',
            field=models.TextField(blank=True),
        ),
    ]
