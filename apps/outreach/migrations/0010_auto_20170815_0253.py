# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-15 02:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outreach', '0009_outreachcall_client'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outreachmailing',
            name='outreach_prospect',
        ),
        migrations.AddField(
            model_name='outreachmailing',
            name='outreach_id',
            field=models.IntegerField(blank=True, db_index=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='outreachmailing',
            name='outreach_prospect_id',
            field=models.IntegerField(blank=True, db_index=True, default=None, null=True),
        ),
    ]
