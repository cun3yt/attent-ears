# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-28 20:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0006_auto_20171026_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='slack_team_id',
            field=models.TextField(db_index=True, default=None, null=True),
        ),
    ]
