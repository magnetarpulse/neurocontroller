import json
import uuid
import requests
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.messages import get_messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import *
from .serializers import *


# Create your views here.
global static_path
static_path = r"/home/areena/neurobazaar/bytebridge/bb_app/datastore"


BB_CREATE_DS = 'http://127.0.0.1:9000/api/user_datastore'
BB_SEND_USER_DATASTORES = 'http://127.0.0.1:9000/api/send_user_datastores'
BB_CHANGE_DS_SETTINGS = 'http://127.0.0.1:9000/api/change_ds_settings'
BB_SEND_ALL_DATASTORES = 'http://127.0.0.1:9000/api/send_all_datastores'
BB_SEND_BUCKETS = 'http://127.0.0.1:9000/api/send_buckets'
BB_CREATE_BUCKETS = 'http://127.0.0.1:9000/api/create_buckets'
BB_CREATE_OBJECTS = 'http://127.0.0.1:9000/api/create_objects'



class RegisterAPI(APIView):
    def get(self, request):
        storage = get_messages(request)
        list(storage)
        return render(request, 'register.html')

    def post(self, request):
        storage = get_messages(request)
        list(storage)
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"Registered with:{username}:{password}")
    
        user = User.objects.filter(username=username)
        if user.exists():
            messages.error(request, 'User already exists')
            return redirect('/api/login/')
        
        user = User.objects.create_user(username=username, password=password)
        user.set_password(password)
        user.save()

        messages.success(request, 'User created successfully')
        return redirect('/api/login/')


class LoginAPI(APIView):
    def get(self, request):
        storage = get_messages(request)
        list(storage)
        return render(request, 'login.html')
    
    def post(self, request):
        storage = get_messages(request)
        list(storage)
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Logged in with:{username}:{password}")
        
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'User does not exist')
            return redirect('/api/login/')
        
        user = authenticate(username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid credentials')
            return redirect('/api/login/')
        else:
            # Log in the user and redirect to the upload file page upon successful login
            # Check if the user already has a UserInfo entry
            user, created = UserInfo.objects.get_or_create(
            user_id = user,  # This is the ForeignKey field
            defaults={'username': username, 'password': password})
            login(request, user)
            # Serialize user info for response
            serializer = UserInfoSerializer(user)
            return Response({'message': 'Logged in successfully', 'user': serializer.data}, status=status.HTTP_200_OK)



class NCConnectAPI(APIView):
    def post(self, request):
        try:
            # Parse JSON request
            data = json.loads(request.body.decode("utf-8"))
            username = data.get('username')
            password = data.get('password')

            print(f"Authentication request received from BB {username}")

            # Authenticate user
            user = authenticate(username=username, password=password)
            if user is None:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

            login(request, user)

            # Store session data
            user, _ = UserInfo.objects.get_or_create(
                user_id=user,
                defaults={'username': username, 'password': password})

            request.session['user_data'] = {
                'username': user.username,
                'user_id': user.user_id_id}

            print(f"User {username} authenticated successfully on NC")

            if BBInstances.objects.filter(owner_id = user.user_id_id).exists():
                instance = BBInstances.objects.get(owner_id = user.user_id_id)
                print(f"Instance already exists with {user.user_id_id}:{instance.instance_id}")
                
            
            else:
                instance = BBInstances.objects.create(owner_id=user.user_id_id,
                                                instance_id = uuid.uuid4(),
                                                datastore_id = uuid.uuid4(),
                                                datastore_name = f"default-datastore-{user.user_id_id}",
                                                accessed_at = timezone.now(),)
                instance.save()
            
            print(f"New ByteBridge Instance Created for user {instance.owner_id}: {instance.instance_id}")
            print(f"Datastore: {instance.datastore_id}, {instance.datastore_name}")

        
            return render(request, 'welcome.html', {'username':username, 'owner_id':instance.owner_id,'datastore_id': instance.datastore_id, 
                                    'datastore_name': instance.datastore_name, 'instance_id': instance.instance_id, 'static_path': static_path})
            
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)


class GetDatastoreAPI(APIView): 

    def post(self, request):
        try:
            owner_id = request.GET.get('owner_id')
            instance_id = request.GET.get('instance_id')
            datastore_id = request.GET.get('datastore_id')
            datastore_name = request.GET.get('datastore_name')
            static_path = request.GET.get('static_path')
            print(f"Getting datastore for {owner_id}:{instance_id}:{datastore_id}:{datastore_name}")

            response = requests.post(BB_CREATE_DS, json={'owner_id': owner_id, 'instance_id': instance_id, 
                                        'datastore_id': datastore_id, 'datastore_name': datastore_name, 'static_path': static_path}, timeout=5)
            
            if response.status_code != 200:
                return JsonResponse({'error': 'Failed to create datastore'}, status=response.status_code)

            return render(request,'index.html', {'owner_id':owner_id, 'static_path':static_path})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)


class NC_DS_Settings(APIView):
    def get(self, request):
        # Get the owner_id from the request
        storage = get_messages(request)
        list(storage)
        owner_id = request.GET.get('owner_id')
        response = requests.post(BB_SEND_USER_DATASTORES, json={'owner_id': owner_id}, timeout=5)
        if response.status_code == 200:
            response_data = response.json()  # Extract JSON response
            all_datastores = response_data.get('all_datastores')  # Extract datastore_id

            print(f"Owner ID {owner_id} received successfully by BB")
            print(f"Datastores: {all_datastores}")
            # You can process the response data here if needed
            return render(request, 'ds_settings.html', {'all_datastores': all_datastores, 'owner_id': owner_id})


    def post(self, request):
        storage = get_messages(request)
        list(storage)
        owner_id = request.POST.get('owner_id')
        selected_ds = request.POST.get('selected_ds')
        private_permissions = request.POST.get('private_permissions')
        datastore_name = request.POST.get('datastore_name')
        
        print(f"Owner ID: {owner_id}, Selected Datastore: {selected_ds}, Private Permissions: {private_permissions}")

        response = requests.post(BB_CHANGE_DS_SETTINGS, json={'owner_id': owner_id, 'selected_ds': selected_ds, 
                                    'private_permissions':private_permissions, 'datastore_name':datastore_name}, timeout=5)
        
        data = response.json()
        if response.status_code == 200:
            messages.success(request, "Datastore settings updated successfully")
        
        else:
            messages.info(request, "Datastore is already set to the selected value")
        
        response_data = requests.post(BB_SEND_USER_DATASTORES, json={'owner_id': owner_id}, timeout=5)
        if response_data.status_code == 200:
            response_data = response_data.json()  
            all_datastores = response_data.get('all_datastores') 
        
        return render(request, 'ds_settings.html', {'all_datastores': all_datastores , 'owner_id': owner_id})



class UploadFile(APIView):
    def get(self, request):
        storage = get_messages(request)
        list(storage)
        
        owner_id = request.GET.get('owner_id')
        static_path = request.GET.get('static_path')
        selected_ds = request.GET.get('selected_ds', "")
        
        response_ds = requests.post(BB_SEND_ALL_DATASTORES, json={'owner_id': owner_id}, timeout=5)
        
        if response_ds.status_code == 200:
            response_data = response_ds.json()
            datastores_upload = response_data.get('datastores_upload', [])
            print(f"Datastores in Get: {datastores_upload}")
            
            if not selected_ds:
                return render(request, 'upload_file.html', {
                    'owner_id': owner_id,
                    'datastores_upload': datastores_upload,
                    'selected_ds': selected_ds
                })
            
            response_bucket = requests.post(BB_SEND_BUCKETS, json={'owner_id': owner_id, 'selected_ds': selected_ds}, timeout=5)
            if response_bucket.status_code == 200:
                response_data = response_bucket.json()
                buckets_upload = response_data.get('buckets_upload', [])
                return render(request, 'upload_file.html', {
                    'owner_id': owner_id,
                    'selected_ds': selected_ds,
                    'datastores_upload': datastores_upload,
                    'buckets_upload': buckets_upload
                })
        
        messages.error(request, 'Failed to retrieve datastores.')
        return render(request, 'upload_file.html', {'owner_id': owner_id})

    def post(self, request):
        owner_id = request.POST.get('owner_id')
        selected_ds = request.POST.get('selected_ds', '')
        selected_bucket = request.POST.get('selected_bucket', '')
        file = request.FILES.get('file')
        file_type = request.POST.get('file_type')

        print(f"Owner ID: {owner_id}, Selected Datastore: {selected_ds}, Bucket Name: {selected_bucket}, File: {file}")

        response_ds = requests.post(BB_SEND_ALL_DATASTORES, json={'owner_id': owner_id}, timeout=5)
        datastores_upload = response_ds.json().get('datastores_upload', []) if response_ds.status_code == 200 else []
        
        buckets_upload = []
        if selected_ds:
            response_bucket = requests.post(BB_SEND_BUCKETS, json={'owner_id': owner_id, 'selected_ds': selected_ds}, timeout=5)
            if response_bucket.status_code == 200:
                buckets_upload = response_bucket.json().get('buckets_upload', [])
                print(f"Buckets in Post: {buckets_upload}")
        
        if file and file_type:
            if not selected_bucket:
                try:
                    bucket_name = f"default-bucket-{owner_id}"
                    response = requests.post(BB_CREATE_BUCKETS, json={'owner_id': owner_id, 'selected_ds': selected_ds, 'bucket_name': bucket_name, 'static_path':static_path}, timeout=5)
                    if response.status_code == 200:
                        selected_bucket = response.json().get('bucket_name', bucket_name)
                        print(f"Created new bucket: {selected_bucket}")
                    else:
                        raise Exception("Bucket creation failed")
                except Exception as e:
                    messages.error(request, f"Error creating bucket: {e}")
                    return JsonResponse({'error': 'Failed to create bucket', 'details': str(e)}, status=500)
            
            files = {'file': (file.name, file, file.content_type)}
            data = {
                'owner_id': owner_id,
                'selected_ds': selected_ds,
                'selected_bucket': selected_bucket,
                'file_type': file_type,
                'static_path': static_path
            }
            response = requests.post(BB_CREATE_OBJECTS, data=data, files=files, timeout=5)
            
            if response.status_code == 200:
                messages.success(request, 'File uploaded successfully')

                return render(request, 'upload_file.html', {
                'owner_id': owner_id,
                #'selected_ds': selected_ds,
                #'selected_bucket': selected_bucket,
                'datastores_upload': datastores_upload,
                'buckets_upload': buckets_upload
            })
            
            else:
                messages.error(request, 'Failed to upload file. Try again later')
        
        return render(request, 'upload_file.html', {
            'owner_id': owner_id,
            'selected_ds': selected_ds,
            'selected_bucket': selected_bucket,
            'datastores_upload': datastores_upload,
            'buckets_upload': buckets_upload
        })
