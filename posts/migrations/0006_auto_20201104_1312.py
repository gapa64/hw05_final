# Generated by Django 2.2.9 on 2020-11-04 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20201030_0755'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date']},
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(max_length=79, unique=True),
        ),
    ]
