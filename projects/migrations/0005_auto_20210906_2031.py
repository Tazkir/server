# Generated by Django 3.1.2 on 2021-09-06 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_auto_20210904_1550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='access_key',
            field=models.CharField(blank=True, default='', editable=False, max_length=100),
        ),
    ]
