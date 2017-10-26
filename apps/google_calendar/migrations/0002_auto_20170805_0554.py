# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-05 05:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('visualizer', '0001_initial'),
        ('google_calendar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlecalendarlistsyncstate',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='googlecalendarevent',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apps.visualizer.Client'),
        ),
        migrations.AddField(
            model_name='googlecalendar',
            name='sync_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
