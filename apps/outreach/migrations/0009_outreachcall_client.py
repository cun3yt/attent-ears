# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-15 02:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_auto_20170810_0616'),
        ('outreach', '0008_auto_20170815_0225'),
    ]

    operations = [
        migrations.AddField(
            model_name='outreachcall',
            name='client',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='visualizer.Client'),
            preserve_default=False,
        ),
    ]
