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

    username = data.get('username')
    password = data.get('password')

    # check if the user exists
    user = UserInfo.objects.get(username=username, password=password)
    if not user:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)
    
    else:
        print(f"User Exists with {username}:{password} with id {user.user_id_id}")
        
        if BBInstances.objects.filter(user_id = user.user_id_id).exists():
            instance = BBInstances.objects.get(user_id = user.user_id_id)
            print(f"Instance already exists with {user.user_id_id}:{instance.instance_id}")
            
            print(f"Datastore: {instance.datastore_id},{instance.datastore_name}")
            print(f"Owned by user {instance.user_id}")
            print(f"Is the Datastore private? {instance.datastore_private}")
            return JsonResponse({'msg': 'Instance already exists','datastore_id': instance.datastore_id, 
                                'datastore_name':instance.datastore_name,
                                    'instance_id':instance.instance_id, 'user_id':user.user_id_id,
                                    'datastore_private':instance.datastore_private}, status=200)
        
        else:
            connected_instance = BBInstances.objects.create(user_id=user.user_id_id,
                                            instance_id = uuid.uuid4(),
                                            datastore_id = uuid.uuid4(),
                                            datastore_name = f"default-datastore-{user.user_id_id}",)

            connected_instance.save()

            print("ByteBridge Instance Created")
            print(f"Owned by user {user.user_id_id}")
            print(f"Instance ID: {connected_instance.instance_id}")
            print(f"Datastore Created: {connected_instance.datastore_id}, {connected_instance.datastore_name}")

            return JsonResponse({'msg': 'Connected', 'instance_id': connected_instance.instance_id, 'user_id':connected_instance.user_id,
                                'datastore_id':connected_instance.datastore_id, 'datastore_name':connected_instance.datastore_name, 
                                'datastore_private':connected_instance.datastore_private, 
                                'datastore_default':connected_instance.datastore_default},status=200)



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
            
            
    return render(request, 'login.html')


