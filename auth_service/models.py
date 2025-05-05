from django.db import models

from django.contrib.auth.models import AbstractBaseUser

import uuid

class User(AbstractBaseUser):
    """ Model to store user information. Password and last login fields are inherited from AbstractBaseUser. """

    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=128, blank=False)
    last_name = models.CharField(max_length=128, blank=False)
    email = models.CharField(max_length=128, blank=False)


class ByteBridge(models.Model):
    """ Model to store connected ByteBridge instance information. """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    owner_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accessed_at = models.DateTimeField(null=False, blank=False)
