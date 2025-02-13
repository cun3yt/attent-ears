# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-06 20:44
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('salesforce', '0006_salesforceaccount_is_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field1',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field10',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field11',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field12',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field13',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field14',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field15',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field2',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field3',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field4',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field5',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field6',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field7',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field8',
        ),
        migrations.RemoveField(
            model_name='salesforceaccount',
            name='custom_field9',
        ),
        migrations.AddField(
            model_name='salesforceaccount',
            name='extra_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
    ]
