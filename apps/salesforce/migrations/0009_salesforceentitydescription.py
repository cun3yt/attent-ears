# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-07 20:56
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_auto_20170810_0616'),
        ('salesforce', '0008_auto_20170907_0324'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesforceEntityDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('db_updated_at', models.DateTimeField(auto_now=True)),
                ('db_created_at', models.DateTimeField(auto_now_add=True)),
                ('entity_name', models.TextField(db_index=True)),
                ('standard_fields', django.contrib.postgres.fields.jsonb.JSONField()),
                ('custom_fields', django.contrib.postgres.fields.jsonb.JSONField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apps.visualizer.Client')),
            ],
            options={
                'db_table': 'salesforce_entity_description',
            },
        ),
    ]
