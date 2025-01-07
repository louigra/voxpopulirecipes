# Generated by Django 5.1.4 on 2025-01-05 04:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voxpopulirecipes', '0016_recipe_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipenote',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='voxpopulirecipes.recipe'),
        ),
    ]
