# Generated by Django 3.0.8 on 2021-03-12 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('testScriptComponentExecutionResultsId', models.IntegerField()),
                ('name', models.CharField(max_length=500)),
                ('testPackageDisplayedName', models.CharField(max_length=500)),
                ('result', models.CharField(max_length=500)),
                ('startTime', models.CharField(max_length=500)),
                ('stopTime', models.CharField(max_length=500)),
                ('duration', models.CharField(max_length=500)),
                ('logFiles', models.TextField(blank=True)),
                ('testScriptComponentId', models.IntegerField()),
                ('testScriptId', models.IntegerField()),
                ('groupId', models.IntegerField()),
                ('failureReason', models.TextField(blank=True)),
            ],
        ),
    ]