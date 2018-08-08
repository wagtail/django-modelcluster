# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-20 10:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0006_auto_20171109_0614'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reviewer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='article',
            name='related_articles',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='_article_related_articles_+', serialize=False, to='tests.Article'),
        ),
        migrations.AlterUniqueTogether(
            name='bandmember',
            unique_together=set([('band', 'name')]),
        ),
        migrations.AddField(
            model_name='article',
            name='reviewer',
            field=modelcluster.fields.ParentalKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', serialize=False, to='tests.Reviewer'),
        ),
    ]
