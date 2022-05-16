import uuid

from jsonfield import JSONField

from django.db import models
from django.dispatch import receiver
from django.utils.timezone import now
from django.db.models.signals import pre_save, pre_delete, post_save
from django.contrib.auth.hashers import make_password

from accounts.models import User


class Project(models.Model):
    owner = models.ForeignKey(User, db_column="email", related_name="projects", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    title = models.CharField(max_length=999)
    goal = models.CharField(max_length=999, blank=True, null=True)

    public_key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    private_key = models.UUIDField(default=uuid.uuid4)

    plan_type = models.CharField(max_length=1000, default='basic')
    subscription_id = models.CharField(max_length=1000, default=None, blank=True, null=True)

    apply_plan = models.BooleanField(default=False)
    monthly_payment = models.PositiveIntegerField(default=0)
    monthly_users = models.PositiveIntegerField(default=25)
    message_history = models.PositiveIntegerField(default=14)
    upgrade_reminder_date_time = models.DateTimeField(blank=True, null=True)

    is_emails_enabled = models.BooleanField(default=False)
    email_company_name = models.CharField(max_length=300, default='', blank=True, null=True)
    email_sender = models.EmailField(max_length=255, default='', blank=True, null=True)
    email_link = models.URLField(max_length=500, default='', blank=True, null=True)
    email_last_sent = models.DateTimeField(default=now, editable=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} - {}'.format(str(self.owner), self.title)

    class Meta:
        ordering = ('owner', 'public_key')
        indexes = [
            models.Index(fields=['public_key']),
            models.Index(fields=['private_key']),
        ]

    def save(self, *args, **kwargs):
        if 'basic' in self.plan_type and self.apply_plan:
            self.monthly_users = 25
            self.monthly_payment = 0
            self.message_history = 14

        if 'light' in self.plan_type and self.apply_plan:
            self.monthly_payment = 7
            self.message_history = 30

        elif 'production' in self.plan_type and self.apply_plan:
            self.monthly_payment = 25
            self.message_history = 365 * 1

        elif 'professional' in self.plan_type and self.apply_plan:
            self.monthly_payment = 36
            self.message_history = 365 * 2

        if self.apply_plan:
            self.apply_plan = False

        super(Project, self).save(*args, **kwargs)


class Collaborator(models.Model):
    user = models.ForeignKey(User, db_column="email", related_name="orgs", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, db_column="public_key", related_name="collaborators", on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default='', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'project'),)
        ordering = ('user', 'project')
        indexes = [
            models.Index(fields=['user', 'project']),
        ]

    def __str__(self):
        return str(self.project)


class Invite(models.Model):
    to_email = models.EmailField(max_length=255, editable=True, default='')
    project = models.ForeignKey(Project, db_column="public_key", related_name="invites", on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default='', blank=True)
    access_key = models.CharField(max_length=100, default='', blank=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('project', 'to_email'),)
        ordering = ('project', 'to_email')
        indexes = [
            models.Index(fields=['project', 'to_email']),
            models.Index(fields=['access_key', ]),
        ]

    def __str__(self):
        return str(self.project.pk) + ' - ' + self.to_email + ' - ' + self.access_key


class Person(models.Model):
    project = models.ForeignKey(Project, db_column="public_key", related_name="people", on_delete=models.CASCADE)

    username = models.CharField(max_length=999)
    secret = models.CharField(max_length=999)

    email = models.EmailField(max_length=255, default='', blank=True)
    first_name = models.CharField(max_length=255, default='', blank=True)
    last_name = models.CharField(max_length=255, default='', blank=True)

    avatar = models.ImageField(upload_to='avatars', max_length=None, blank=True, null=True)
    custom_json = JSONField(default=dict)

    is_online = models.BooleanField(default=False)
    is_authenticated = models.BooleanField(default=True, editable=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        unique_together = (("project", "username"),)
        ordering = ('project', 'username')
        indexes = [
            models.Index(fields=['project', 'username']),
        ]


@receiver(pre_save, sender=Person)
def pre_save_person(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance.secret = make_password(instance.secret, None)
    else:
        if not obj.secret == instance.secret:  # Field has changed
            instance.secret = make_password(instance.secret, None)


class Connection(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=100)
    person = models.ForeignKey(Person, related_name="connections", on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return '{} - {}'.format(id, self.person.username)

    class Meta:
        unique_together = (("id"),)
        ordering = ('id',)
        indexes = [
            models.Index(fields=['id']),
        ]


@receiver(post_save, sender=Project)
def post_save_project(instance, created, **kwargs):
    if created:
        Collaborator.objects.create(user=instance.owner, project=instance, role='admin')


@receiver(post_save, sender=Person)
def post_save_person(instance, created, **kwargs):
    from webhooks.sender import hook
    from .serializers import PersonSerializer
    from projects.serializers import ProjectSerializer
    person_json = PersonSerializer(instance, many=False).data
    project_json = ProjectSerializer(instance.project, many=False).data
    if created:
        hook.post(event_trigger='On New User', project_json=project_json, person_json=person_json)
    else:
        hook.post(event_trigger='On Edit User', project_json=project_json, person_json=person_json)


@receiver(pre_delete, sender=Person)
def pre_delete_person(instance, **kwargs):
    from webhooks.sender import hook
    from .serializers import PersonSerializer
    from projects.serializers import ProjectSerializer
    person_json = PersonSerializer(instance, many=False).data
    project_json = ProjectSerializer(instance.project, many=False).data
    hook.post(event_trigger='On Delete User', project_json=project_json, person_json=person_json)


@receiver(post_save, sender=Invite)
def post_save_invite(instance, created, **kwargs):
    if created:
        instance.access_key = 'inv-{}'.format(str(uuid.uuid4()))
        instance.save()
