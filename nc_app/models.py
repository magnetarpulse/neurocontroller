
import uuid
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class UserInfo(models.Model):
    """ Model to store information of each user """

    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)
    user_id= models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Information for {self.username}: {self.password}"


class BBInstances(models.Model):
    """ Model to store the instances of the bytebridge app """

    instance_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    instance_ip = models.GenericIPAddressField(blank=False, null = False)
    instance_port = models.IntegerField(blank=False, null = False)
    
    username = models.CharField(max_length=100, blank=False)
    password = models.CharField(max_length=100, blank=False)
    datastore_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    datastore_private = models.BooleanField(default=True)
    user_id= models.IntegerField(blank=True, null=True) # ForeignKey to the User model
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Instance {self.instance_id}:{self.datastore_id}"

