from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class UserInfo(models.Model):
    """ Model to store information of each user """

    username = models.CharField(max_length=100, blank=False)
    password = models.CharField(max_length=100, blank=False)
    user_id= models.ForeignKey(User, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Information for {self.username}: {self.password}"


class BBInstances(models.Model):
    """ Model to store the instances of the bytebridge app and with a default datastore that's created """

    owner_id= models.IntegerField(blank=False, null=False) # ForeignKey to the User model
    instance_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    datastore_id = models.UUIDField(default=uuid.uuid4, editable=False)
    datastore_name = models.CharField(max_length=100, blank=False)  # http://192.168.1.106:8001/list_files/
    private_permissions = models.BooleanField(default=True)
    default = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accessed_at = models.DateTimeField(default=timezone.now)    
    access_key = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(default="127.0.0.1") 
    port = models.IntegerField(default=8001)                        
    exposed_path = models.TextField(default="C:/default/path")      

    

    def __str__(self):
        return f"Instance {self.instance_id}:{self.datastore_id}"
