# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-16 07:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('outreach', '0016_outreachcall_record_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='outreachaccount',
            name='covering_api_offset',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='outreachcall',
            name='covering_api_offset',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='outreachmailing',
            name='covering_api_offset',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='outreachprospect',
            name='covering_api_offset',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='outreachuser',
            name='covering_api_offset',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='outreachaccount',
            name='updated_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='outreachcall',
            name='updated_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='outreachmailing',
            name='updated_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='outreachprospect',
            name='updated_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
