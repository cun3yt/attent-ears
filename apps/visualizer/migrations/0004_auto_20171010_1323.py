# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-10 13:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_auto_20170810_0616'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='keep_in_sync',
        ),
        migrations.AddField(
            model_name='client',
            name='status',
            field=models.TextField(choices=[('Applied', 'Applied'), ('Active', 'Active'), ('Terminated', 'Terminated')], default='Applied'),
        ),
    ]
