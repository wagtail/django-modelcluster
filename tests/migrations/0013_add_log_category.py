# Generated by Django 4.2.16 on 2024-11-25 12:55

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0012_add_record_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('log', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='tests.log')),
            ],
        ),
        migrations.AddConstraint(
            model_name='logcategory',
            constraint=models.UniqueConstraint(fields=('log', 'name'), name='unique_log_category'),
        ),
    ]