from datetime import datetime, timedelta
import uuid
import pytz

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)

from django.db.utils import IntegrityError


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email),)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        """
        Creates and saves a staff user with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    objects = UserManager()

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        editable=True,
        primary_key=True
    )
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    admin = models.BooleanField(default=False)  # a superuser
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # notice the absence of a "Password field", that is built in.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default.

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    @property
    def is_active(self):
        "Is the user active?"
        return self.active

    class Meta:
        ordering = ('email',)
        indexes = [
            models.Index(fields=["-created", "email"]),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.lower()

        try:
            user = User.objects.get(email=self.email)

            if user.pk != self.pk:
                raise Exception(IntegrityError, 'Another user has this email')

            super(User, self).save(*args, **kwargs)

        except User.DoesNotExist:
            super(User, self).save(*args, **kwargs)


class Reset(models.Model):
    user = models.OneToOneField(User, db_column="email", related_name="reset", on_delete=models.CASCADE)
    expiry = models.DateTimeField(blank=True, null=True)
    uuid = models.CharField(blank=True, null=True, max_length=36)


@receiver(post_save, sender=Reset)
def post_save_reset(instance, created, **kwargs):
    now = datetime.now().replace(tzinfo=pytz.UTC)
    if created or instance.expiry is None or now > instance.expiry:
        instance.expiry = now + timedelta(hours=1)
        instance.uuid = uuid.uuid4()
        instance.save()
