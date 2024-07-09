# Generated by Django 5.0.6 on 2024-07-09 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScraperResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('userid', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('registration_number', models.CharField(blank=True, max_length=255, null=True)),
                ('registration_date', models.DateField(blank=True, null=True)),
                ('name_used_in_practice', models.CharField(blank=True, max_length=255, null=True)),
                ('registrant_type', models.CharField(blank=True, max_length=255, null=True)),
                ('languages_of_care', models.TextField(blank=True, null=True)),
                ('registration_status', models.CharField(blank=True, max_length=255, null=True)),
                ('areas_of_practice', models.TextField(blank=True, null=True)),
            ],
        ),
    ]