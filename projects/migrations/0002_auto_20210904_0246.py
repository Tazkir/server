# Generated by Django 3.1.2 on 2021-09-04 02:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collaboraotor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, default='', max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(db_column='public_key', on_delete=django.db.models.deletion.CASCADE, related_name='collaborators', to='projects.project')),
                ('user', models.ForeignKey(db_column='email', on_delete=django.db.models.deletion.CASCADE, related_name='orgs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user', 'project'),
            },
        ),
        migrations.AddIndex(
            model_name='collaboraotor',
            index=models.Index(fields=['user', 'project'], name='projects_co_email_322689_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='collaboraotor',
            unique_together={('user', 'project')},
        ),
    ]
