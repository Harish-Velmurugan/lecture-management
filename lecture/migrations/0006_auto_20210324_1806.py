# Generated by Django 3.1.7 on 2021-03-24 12:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lecture', '0005_auto_20210312_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='max_seats',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Maximum Seats'),
        ),
    ]
