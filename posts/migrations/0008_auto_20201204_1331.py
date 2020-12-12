# Generated by Django 2.2.6 on 2020-12-04 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20201204_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='description',
            field=models.TextField(verbose_name='Описание группы'),
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(max_length=79, unique=True, verbose_name='Slug группы'),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Название группы'),
        ),
    ]