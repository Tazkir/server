# Generated by Django 3.1.2 on 2021-09-19 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
