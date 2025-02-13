# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-23 11:15
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('salesforce', '0011_auto_20170915_0326'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='salesforceaccount',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceaccounthistory',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforcecontact',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforcecontacthistory',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceevent',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforcelead',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceopportunity',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceopportunityfieldhistory',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceopportunityhistory',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforcetask',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceuser',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='salesforceuserrole',
            managers=[
                ('postgres_manager', django.db.models.manager.Manager()),
            ],
        ),
    ]
