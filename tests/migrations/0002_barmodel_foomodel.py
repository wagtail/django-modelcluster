# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tests.models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FooModel',
            fields=[
                ('id', tests.models.FooField(serialize=False, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='BarModel',
            fields=[
                ('id', models.OneToOneField(primary_key=True, serialize=False, to='tests.FooModel')),
            ],
        ),
    ]
