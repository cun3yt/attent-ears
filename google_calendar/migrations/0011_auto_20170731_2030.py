# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-31 20:30
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_auto_20170731_2023'),
        ('google_calendar', '0010_googlecalendar_timezone'),
    ]

    operations = [
        migrations.RenameField(
            model_name='googlecalendar',
            old_name='created_at',
            new_name='db_created_at',
        ),
        migrations.RenameField(
            model_name='googlecalendar',
            old_name='updated_at',
            new_name='db_updated_at',
        ),
        migrations.RenameField(
            model_name='googlecalendarevent',
            old_name='created_at',
            new_name='db_created_at',
        ),
        migrations.RenameField(
            model_name='googlecalendarevent',
            old_name='updated_at',
            new_name='db_updated_at',
        ),
        migrations.RenameField(
            model_name='googlecalendarlistsyncstate',
            old_name='created_at',
            new_name='db_created_at',
        ),
        migrations.AddField(
            model_name='googlecalendarapilogs',
            name='db_created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='attendees',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='visualizer.Client'),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='creator',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='end',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='event_id',
            field=models.CharField(default=None, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='htmlLink',
            field=models.CharField(default='', max_length=2083),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='organizer',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='recurring_event_id',
            field=models.CharField(default=None, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='start',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='status',
            field=models.CharField(default='tentative', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='summary',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='updated',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
