# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-10 06:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0002_userapiconnection'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userapiconnection',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserApiConnection',
        ),
    ]
