from datetime import datetime, timedelta
import uuid
import pytz

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from projects.models import Person


class Session(models.Model):
    person = models.OneToOneField(Person, related_name="session", on_delete=models.CASCADE, blank=True, null=True)
    token = models.CharField(editable=False, max_length=100, null=True, blank=True)
    expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '{}: {}'.format(self.person.username, self.token)

    class Meta:
        ordering = ('person', '-expiry',)
        indexes = [
            models.Index(fields=['person', '-expiry']),
        ]


@receiver(post_save, sender=Session)
def post_save_session(instance, created, **kwargs):
    now = datetime.now().replace(tzinfo=pytz.UTC)
    if created or instance.expiry is None or now > instance.expiry:
        instance.expiry = now + timedelta(days=1)
        instance.token = 'st-{}'.format(str(uuid.uuid4()))
        instance.save()
