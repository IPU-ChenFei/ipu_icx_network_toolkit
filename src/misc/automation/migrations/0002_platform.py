# Generated by Django 3.1.7 on 2021-03-20 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform_id', models.IntegerField()),
                ('platform_name_short', models.TextField(blank=True)),
                ('platform_name', models.TextField(blank=True)),
            ],
        ),
    ]
