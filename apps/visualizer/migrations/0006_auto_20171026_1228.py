# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-26 12:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0005_client_warehouse_sql_view'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='warehouse_sql_view',
            new_name='warehouse_view_definition',
        ),
        migrations.AddField(
            model_name='client',
            name='warehouse_view_name',
            field=models.TextField(default=None, null=True),
        ),
    ]
