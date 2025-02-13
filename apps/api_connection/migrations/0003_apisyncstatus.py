# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-21 01:57
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_connection', '0002_apiconnectionlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiSyncStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('db_created_at', models.DateTimeField(auto_now_add=True)),
                ('resource', models.CharField(default='', max_length=50)),
                ('start', models.DateTimeField(blank=True, default=None, null=True)),
                ('end', models.DateTimeField(blank=True, default=None, null=True)),
                ('extra_data', django.contrib.postgres.fields.jsonb.JSONField(default={})),
                ('api_connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api_connection.ApiConnection')),
            ],
            options={
                'db_table': 'api_sync_status',
            },
        ),
    ]
