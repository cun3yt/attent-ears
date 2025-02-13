# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-05 02:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0003_auto_20170810_0616'),
        ('salesforce', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesforceAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('db_updated_at', models.DateTimeField(auto_now=True)),
                ('db_created_at', models.DateTimeField(auto_now_add=True)),
                ('custom_field1', models.TextField(blank=True, default=None, null=True)),
                ('custom_field2', models.TextField(blank=True, default=None, null=True)),
                ('custom_field3', models.TextField(blank=True, default=None, null=True)),
                ('custom_field4', models.TextField(blank=True, default=None, null=True)),
                ('custom_field5', models.TextField(blank=True, default=None, null=True)),
                ('custom_field6', models.TextField(blank=True, default=None, null=True)),
                ('custom_field7', models.TextField(blank=True, default=None, null=True)),
                ('custom_field8', models.TextField(blank=True, default=None, null=True)),
                ('custom_field9', models.TextField(blank=True, default=None, null=True)),
                ('custom_field10', models.TextField(blank=True, default=None, null=True)),
                ('custom_field11', models.TextField(blank=True, default=None, null=True)),
                ('custom_field12', models.TextField(blank=True, default=None, null=True)),
                ('custom_field13', models.TextField(blank=True, default=None, null=True)),
                ('custom_field14', models.TextField(blank=True, default=None, null=True)),
                ('custom_field15', models.TextField(blank=True, default=None, null=True)),
                ('sfdc_id', models.CharField(db_index=True, max_length=30)),
                ('master_record_id', models.IntegerField()),
                ('name', models.TextField()),
                ('type', models.TextField()),
                ('website', models.TextField()),
                ('number_of_employees', models.IntegerField()),
                ('owner_id', models.CharField(max_length=30)),
                ('created_date', models.DateTimeField()),
                ('created_by_id', models.CharField(max_length=30)),
                ('last_modified_date', models.DateTimeField()),
                ('last_modified_by_id', models.CharField(max_length=30)),
                ('last_activity_date', models.DateTimeField()),
                ('last_viewed_date', models.DateTimeField()),
                ('account_source', models.TextField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='visualizer.Client')),
            ],
            options={
                'db_table': 'salesforce_account',
            },
        ),
        migrations.AlterField(
            model_name='salesforcecustomfieldmapping',
            name='client',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='visualizer.Client'),
            preserve_default=False,
        ),
    ]
