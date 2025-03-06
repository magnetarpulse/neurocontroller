from rest_framework import serializers
from .models import *

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = '__all__'


class BBInstancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BBInstances
        fields = '__all__'