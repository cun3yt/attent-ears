# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-16 01:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outreach', '0013_auto_20170816_0052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outreachuser',
            name='email_address',
            field=models.CharField(db_index=True, default='', max_length=255),
        ),
    ]
