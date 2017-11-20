# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.fields
import django.db.models.deletion
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('release_date', models.DateField(null=True, blank=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='Band',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BandMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('band', modelcluster.fields.ParentalKey(related_name='members', to='tests.Band', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Chef',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Dish',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(null=True, blank=True)),
                ('data', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('dish', models.ForeignKey(related_name='+', to='tests.Dish', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=255)),
                ('body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TaggedPlace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Wine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('place_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='tests.Place', on_delete=django.db.models.deletion.CASCADE)),
                ('serves_hot_dogs', models.BooleanField(default=False)),
                ('proprietor', models.ForeignKey(related_name='restaurants', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tests.Chef', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('tests.place',),
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='documents')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='taggedplace',
            name='content_object',
            field=modelcluster.fields.ParentalKey(related_name='tagged_items', to='tests.Place', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='taggedplace',
            name='tag',
            field=models.ForeignKey(related_name='tests_taggedplace_items', to='taggit.Tag', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='review',
            name='place',
            field=modelcluster.fields.ParentalKey(related_name='reviews', to='tests.Place', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='place',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(to='taggit.Tag', through='tests.TaggedPlace', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='recommended_wine',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='tests.Wine', null=True),
        ),
        migrations.AddField(
            model_name='album',
            name='band',
            field=modelcluster.fields.ParentalKey(related_name='albums', to='tests.Band', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='restaurant',
            field=modelcluster.fields.ParentalKey(related_name='menu_items', to='tests.Restaurant', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
