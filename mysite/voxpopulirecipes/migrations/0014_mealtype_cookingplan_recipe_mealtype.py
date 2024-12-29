# Generated by Django 5.1.1 on 2024-12-23 15:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voxpopulirecipes', '0013_remove_vpuser_email_remove_vpuser_first_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MealType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='CookingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='My Cooking Plan', max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipes', models.ManyToManyField(related_name='cooking_plans', to='voxpopulirecipes.recipe')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='voxpopulirecipes.vpuser')),
            ],
        ),
        migrations.AddField(
            model_name='recipe',
            name='mealType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='voxpopulirecipes.mealtype'),
        ),
    ]