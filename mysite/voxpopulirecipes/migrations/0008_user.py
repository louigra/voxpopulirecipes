# Generated by Django 5.1.1 on 2024-11-14 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voxpopulirecipes', '0007_recipe_created_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=200)),
                ('email', models.CharField(max_length=200)),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
            ],
        ),
    ]
