from django.db import models
from django.utils.timezone import now

from accounts.models import User


class Feedback(models.Model):
    user = models.ForeignKey(User, db_column="email", related_name="feedback", on_delete=models.CASCADE)
    text = models.CharField(default='', max_length=1000)
    created = models.DateTimeField(default=now, editable=True)

    def __str__(self):
        return '{}: {}'.format(str(self.user), self.text)

    class Meta:
        ordering = ('created', 'user')
