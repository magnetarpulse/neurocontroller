import json
import uuid
from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
def connect(request):
    
    data = json.loads(request.body.decode("utf-8"))
    ip = data.get('ip')
    port = data.get('port')
    username = data.get('username')
    password = data.get('password')

    # check if the user exists
    user = UserInfo.objects.get(username=username, password=password)
    if not user:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    else:
        print(f"User Exists with {username}:{password} with id {user.user_id_id}")
        
        if BBInstances.objects.filter(username=username, password=password).exists():
            instance = BBInstances.objects.get(username=username, password=password, instance_ip=ip, instance_port=port)
            print(f"Instance already exists with {username}:{password}:{ip}:{port}:{instance.instance_id}:{instance.datastore_id}:{user.user_id_id}")
            print(f"Owned by user {instance.user_id}")
            print(f"Is the Datastore private? {instance.datastore_private}")
            return JsonResponse({'msg': 'Instance already exists','datastore_id': instance.datastore_id, 
                                    'instance_id':instance.instance_id, 'user_id':user.user_id_id,
                                    'datastore_private':instance.datastore_private,
                                
                                    }, status=200)
        
        else:
            connected_instance = BBInstances.objects.create(instance_ip=ip, instance_port=port,username=username, password=password, user_id=user.user_id_id)
            connected_instance.save()
            datastore_id = connected_instance.datastore_id
            instance_id = connected_instance.instance_id
            user_id = user.user_id_id
            datastore_private = connected_instance.datastore_private
            
            #if privacy == '1':
            #    print("Private Datastore")
            print("ByteBridge Instance Created")
            print(f"Datastore ID: {datastore_id}")
            print(f"Instance ID: {instance_id}")
            print(f"Owned by user {user.user_id_id}")
            return JsonResponse({'msg': 'Connected', 'datastore_id':datastore_id, 'instance_id': instance_id, 
                                'user_id':user_id,'datastore_private':datastore_private}, status=200)



def register_page(request):
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Registered with:{username}:{password}")
    
        user = User.objects.filter(username=username)
        if user.exists():
            messages.error(request, 'User already exists')
            return redirect('/register/')
        
        user = User.objects.create_user(username=username, password=password)
        user.set_password(password)
        user.save()

        messages.success(request, 'User created successfully')
        return redirect('/login/')
        
    return render(request, 'register.html')


def login_page(request):
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Logged in with:{username}:{password}")
        
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'User does not exist')
            return redirect('/login/')
        
        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid credentials')
            return redirect('/login/')
        else:
            # Log in the user and redirect to the upload file page upon successful login
            # Check if the user already has a UserInfo entry
            logged_user, created = UserInfo.objects.get_or_create(
            # This is the ForeignKey field
            user_id = user, defaults={'username': username, 'password': password})
            login(request, user)
            
            #return redirect('/upload/')
    
    return render(request, 'login.html')


