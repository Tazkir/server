import uuid

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from projects.models import Project


class Webhook(models.Model):
    project = models.ForeignKey(Project, db_column="public_key", related_name="webhooks", on_delete=models.CASCADE)
    event_trigger = models.CharField(max_length=1000)
    url = models.URLField()
    secret = models.CharField(blank=True, null=True, max_length=40)

    class Meta:
        unique_together = (("project", "event_trigger"),)
        ordering = ('project', 'event_trigger')


@receiver(post_save, sender=Webhook)
def post_save_webhook(instance, created, **kwargs):
    if created:
        instance.secret = 'whk-{}'.format(str(uuid.uuid4()))
        instance.save()
