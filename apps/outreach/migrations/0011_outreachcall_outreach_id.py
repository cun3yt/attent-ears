# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-15 02:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outreach', '0010_auto_20170815_0253'),
    ]

    operations = [
        migrations.AddField(
            model_name='outreachcall',
            name='outreach_id',
            field=models.IntegerField(blank=True, db_index=True, default=None, null=True),
        ),
    ]
