import json
import uuid
import requests
import csv
import pandas as pd
from os.path import basename
from io import StringIO
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
from django.conf import settings
from django.http import HttpResponseRedirect

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password


# Create your views here.
global static_path
static_path = r"/home/cc/nb/bytebridge/datastore"



BB_CHECK_DATASTORE = 'http://127.0.0.1:9000/api/check_user_datastore'
BB_DATASTORES='http://127.0.0.1:9000/api/datastores'

# For changing datastore settings
BB_CHANGE_DS_SETTINGS = 'http://127.0.0.1:9000/api/change_ds_settings'

# For changing bucket settings
BB_CHANGE_BUCKET_SETTINGS = 'http://127.0.0.1:9000/api/change_bucket_settings'


# Register on NC
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
            agesmess.error(request, 'User already exists')
            return redirect('/api/login/')
        
        user = User.objects.create_user(username=username, password=password)
        user.set_password(password)
        user.save()

        messages.success(request, 'User created successfully')
        return redirect('/api/login/')


# Login on NC
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
            # Check if the user already has a Users entry
            user, created = Users.objects.get_or_create(
            user_id = user,  # This is the ForeignKey field
            defaults={'username': username, 'password': make_password(password)})
            login(request, user)
            # Serialize user info for response
            serializer = UsersSerializer(user)
            return Response({'message': 'Logged in successfully', 'user': serializer.data}, status=status.HTTP_200_OK)



# Authentication code
@api_view(['POST'])
@csrf_exempt
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"}, status=400)

    refresh = RefreshToken.for_user(user)
    
    # Add username to the access token
    access_token = refresh.access_token
    access_token["username"] = user.username 

    response = JsonResponse({
        "access": str(access_token),
        "refresh": str(refresh),
        "username": user.username
    })

    # Store token in cookies
    response.set_cookie(
        "access_token",
        str(access_token),
        httponly=True,
        samesite="Lax"
    )

    print(f"Token generated and stored in cookie: {access_token}")  # Debugging
    return response


# Verifying Token with logged in
@api_view(['GET'])
@authentication_classes([JWTAuthentication])  #  Uses JWT authentication
@permission_classes([IsAuthenticated])  #  Ensures the user is authenticated
def verify_token_view(request):
    """
    This API verifies the JWT token and returns the user details.
    ByteBridge will call this endpoint to authenticate users.
    """
    print(f"-----  Received request with user: {request.user}")

    if not request.user or not request.user.is_authenticated:
        print(" Unauthorized access attempt!")
        return Response({"detail": "Invalid token"}, status=403)

    return Response({
        "user_id": request.user.id,
        "username": request.user.username
    })



# BB request to connect to NC
class NCConnectAPI(APIView):
    def post(self, request):
        try:
            # Parse JSON request
            data = json.loads(request.body.decode("utf-8"))
            username = data.get('username')

            print(f"Authentication request received from BB {username}")

            user_django = User.objects.get(username=username)
            # Store session data
            user, _ = Users.objects.get_or_create(
                user_id= user_django,  # This is the ForeignKey field
                password = user_django.password,
                defaults={'username': username})

            request.session['user_data'] = {
                'username': user.username,
                'user_id': user.user_id_id}

            print(f"User {username} authenticated successfully on NC")

            if ByteBridges.objects.filter(owner_id = user.user_id_id).exists():
                instance = ByteBridges.objects.get(owner_id = user.user_id_id)
                print(f"Instance already exists with {user.user_id_id}:{instance.instance_id}")
                
            
            else:
                instance = ByteBridges.objects.create(owner_id=user.user_id_id,
                                                instance_id = uuid.uuid4(),
                                                accessed_at = timezone.now(),)
                instance.save()
            
            print(f"New ByteBridge Instance Created for user {instance.owner_id}: {instance.instance_id}")
            
            return render(request, 'welcome.html', {'username':username, 'owner_id':instance.owner_id,
                                                    'instance_id': instance.instance_id, 'static_path': static_path})
            
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)



# Get all datastores from BB
class GetDatastoreInfoAPI(APIView): 
    def get(self, request):
        owner_id = request.GET.get('owner_id')
        instance_id = request.GET.get('instance_id')
        static_path = request.GET.get('static_path')
        print(f"In Get Owner ID: {owner_id}, Instance ID: {instance_id}, Static Path: {static_path}")
        return render(request, 'index.html', {'owner_id':owner_id, 'static_path':static_path, 'instance_id': instance_id})
    
    def post(self, request):
        try:
            owner_id = request.POST.get('owner_id')
            instance_id = request.POST.get('instance_id')
            static_path = request.POST.get('static_path')
            print(f"Owner ID: {owner_id}, Instance ID: {instance_id}, Static Path: {static_path}")

            
            response = requests.post(BB_CHECK_DATASTORE, json={'owner_id': owner_id, 'instance_id': instance_id, 'static_path': static_path},
                                cookies=request.COOKIES, 
                                timeout=5)
            
            if response.status_code != 200:
                return JsonResponse({'error': 'Failed to create datastore'}, status=response.status_code)

            return render(request,'index.html', {'owner_id':owner_id, 'static_path':static_path, 'instance_id': instance_id})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)


# Datastore settings for BB
class NC_DS_Settings(APIView):
    def get(self, request):
        # Get the owner_id from the request
        storage = get_messages(request)
        list(storage)
        owner_id = request.GET.get('owner_id')
        static_path = request.GET.get('static_path')
        response = requests.post(BB_DATASTORES, json={'owner_id': owner_id,'static_path':static_path},cookies=request.COOKIES,  timeout=5)
        if response.status_code == 200:
            response_data = response.json()  # Extract JSON response
            datastores_upload = response_data.get('datastores_upload',[])  # Extract datastore_id

            print(f"Owner ID {owner_id} received successfully by BB")
            print(f"Datastores: {datastores_upload}")
            return render(request, 'ds_settings.html', {'all_datastores': datastores_upload, 'owner_id': owner_id, 'static_path': static_path})


    def post(self, request):
        storage = get_messages(request)
        list(storage)
        owner_id = request.POST.get('owner_id')
        selected_ds = request.POST.get('selected_ds')
        private_permissions = request.POST.get('private_permissions')
        datastore_name = request.POST.get('datastore_name')
        
        print(f"Owner ID: {owner_id}, Selected Datastore: {selected_ds}, Private Permissions: {private_permissions}, Datastore Name: {datastore_name}")

        response = requests.post(BB_CHANGE_DS_SETTINGS, json={'owner_id': owner_id, 'selected_ds': selected_ds, 
                                    'private_permissions':private_permissions, 'datastore_name':datastore_name},cookies=request.COOKIES, timeout=5)
        
        if response.status_code == 200:
            messages.success(request, "Datastore settings updated successfully")
        
        else:
            messages.error(request, "Failed to update datastore settings")
        
        response_data = requests.post(BB_DATASTORES, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
        if response_data.status_code == 200:
            response_data = response_data.json()  
            all_datastores = response_data.get('all_datastores',[]) 
            return render(request, 'ds_settings.html', {'all_datastores': all_datastores , 'owner_id': owner_id})


# Upload a file to BB
class UploadFile(APIView):
    def get(self, request):
        storage = get_messages(request)
        list(storage)
        
        owner_id = request.GET.get('owner_id')
        static_path = request.GET.get('static_path')
        selected_ds = request.GET.get('selected_ds', '')
        privacy_bucket = request.GET.get('privacy_bucket', '')
        print(f"Upload File in GET *** Owner ID: {owner_id}, Static Path: {static_path}")
        print(f"Selected Datastore in GET: {selected_ds}, Privacy Bucket: {privacy_bucket}")

        response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id,'include_public':True}, cookies=request.COOKIES,  timeout=5)
        
        if response_ds.status_code == 200:
            response_data = response_ds.json()
            datastores_upload = response_data.get('datastores_upload', [])
            print(f"Datastores in Get: {datastores_upload}")

            return render(request, 'upload_file.html', {
                    'owner_id': owner_id,
                    'static_path': static_path,
                    'datastores_upload': datastores_upload,
                    'selected_ds': selected_ds,
                    'privacy_bucket':privacy_bucket })
    
    def post(self, request):
        storage = get_messages(request)
        list(storage)
        
        owner_id = request.POST.get('owner_id')
        static_path = request.POST.get('static_path')
        
        selected_ds = request.POST.get('selected_ds', '')
        privacy_bucket = request.POST.get('privacy_bucket', '')
        file = request.FILES.get('file')
        file_type = request.POST.get('file_type')
        print(f"Upload File in POST *** Owner ID: {owner_id}, Static Path: {static_path}")
        print(f"Selected Datastore in POST: {selected_ds}, Privacy Bucket: {privacy_bucket}")

        response_ds = requests.post(
            BB_DATASTORES,
            json={'owner_id': owner_id, 'include_public': True},
            cookies=request.COOKIES,
            timeout=5
        )

        datastores_upload = []
        if response_ds.status_code == 200:
            response_data = response_ds.json()
            datastores_upload = response_data.get('datastores_upload', [])
            print(f"Datastores in POST: {datastores_upload}")

        selected_bucket = None
        if selected_ds and privacy_bucket:
            BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
            response_bucket = requests.post(
                BB_LIST_BUCKETS, json={'owner_id': owner_id, 'privacy_bucket': privacy_bucket},
                cookies=request.COOKIES,
                timeout=5
            )

            if response_bucket.status_code == 200:
                dataset_bucket = response_bucket.json().get('dataset_bucket', [])
                print(f"Dataset Bucket: {dataset_bucket}")
                if dataset_bucket:
                    selected_bucket = dataset_bucket[0]['bucket_id']
                    print(f"Selected Existing Bucket: {selected_bucket}")

            elif response_bucket.status_code == 201:
                print("Bucket not found. Creating a new one...")
                bucket_name = f"default-bucket-{owner_id}-{privacy_bucket}"
                BB_CREATE_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/create_buckets'
                try:
                    response = requests.post(
                        BB_CREATE_BUCKETS,
                        json={
                            'owner_id': owner_id,
                            'selected_ds': selected_ds,
                            'bucket_name': bucket_name,
                            'static_path': static_path,
                            #'default': True,
                            'private_permissions': privacy_bucket
                        },
                        cookies=request.COOKIES,
                        timeout=5
                    )
                    if response.status_code == 200:
                        selected_bucket = response.json().get('created_bucket')
                        print("Created New Bucket:", selected_bucket)
                    else:
                        raise Exception("Bucket creation failed")
                except Exception as e:
                    messages.error(request, f"Error creating bucket: {e}")
                    return JsonResponse({'error': 'Failed to create bucket', 'details': str(e)}, status=500)

        
        if file and file_type and selected_bucket:
            files = {'file': (file.name, file, file.content_type)}
            data = {
                'owner_id': owner_id,
                'file_type': file_type,
                'static_path': static_path,
                'selected_ds': selected_ds,
                'selected_bucket': selected_bucket,
            }

            BB_CREATE_OBJECTS = f'http://127.0.0.1:9000/api/{selected_ds}/{selected_bucket}/create_objects'
            response = requests.post(
                BB_CREATE_OBJECTS,
                data=data,
                files=files,
                cookies=request.COOKIES,
                timeout=5
            )

            if response.status_code == 200:
                messages.success(request, 'File uploaded successfully')
            else:
                messages.error(request, 'Failed to upload file. Try again later')
        else:
            if not file or not file_type:
                messages.error(request, 'Missing file or file_type')
            elif not selected_bucket:
                messages.error(request, 'Bucket not available or could not be created')

        
        return render(request, 'upload_file.html', {
            'owner_id': owner_id,
            'static_path': static_path,
            'datastores_upload': datastores_upload,
            'selected_ds': selected_ds,
            'privacy_bucket': privacy_bucket,
        })




#List all the datasets for viewing and deleting from BB
class ListDatasets(APIView):
    def get(self, request):
        owner_id = request.GET.get('owner_id')
        dataset_type = request.GET.get('dataset_type', 'private')
        static_path = request.GET.get('static_path', '/home/cc/nb/bytebridge/datastore')

        print(f"In GET - Owner_id: {owner_id}, Dataset Type: {dataset_type}")
        all_datasets = []

        # Fetch datastores from BB
        if dataset_type == 'private':
            response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
        else:
            response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id, 'pub_comm': True}, cookies=request.COOKIES, timeout=5)

        if response_ds.status_code == 200:
            response_datastore = response_ds.json()
            datastores_upload = response_datastore.get('datastores_upload', [])
            print(f"Datastores: {datastores_upload}")

            for datastore in datastores_upload:
                selected_ds = datastore[1]
                BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'

                response_bucket = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id, 'dataset_type': dataset_type}, cookies=request.COOKIES, timeout=5)
                if response_bucket.status_code == 200:
                    response_b = response_bucket.json()
                    buckets_upload = response_b.get('buckets_upload', [])
                    print(f"Buckets: {buckets_upload}")

                    for bucket in buckets_upload:
                        selected_bucket = bucket[1]
                        print(f"Selected Bucket: {selected_bucket}")

                        BB_LIST_OBJECTS = f'http://127.0.0.1:9000/api/{selected_ds}/{selected_bucket}/objects'
                        response_object = requests.post(BB_LIST_OBJECTS, json={'owner_id': owner_id, 'dataset_type': dataset_type}, cookies=request.COOKIES, timeout=5)
                        if response_object.status_code == 200:
                            response_o = response_object.json()
                            print(f"Response from BB: {response_o}")
                            datasets = response_o.get('datasets', [])
                            print(f"Datasets from BB: {datasets}")
                            all_datasets.extend(datasets)

        return render(request, 'list_datasets.html', {'owner_id': owner_id, 'dataset_type': dataset_type, 'datasets': all_datasets, 'static_path': static_path})


    def post(self,request):
        owner_id = request.POST.get('owner_id')
        dataset_type= request.POST.get('dataset_type')
        static_path = request.POST.get('static_path')
        
        all_datasets = []
        print(f"Owner_id: {owner_id}, Dataset Type: {dataset_type}")

        # get the datastores from BB
        if dataset_type == 'private':
            response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
        else:
            response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id,'pub_comm':True}, cookies=request.COOKIES,  timeout=5)

        if response_ds.status_code == 200:
            response_datastore = response_ds.json()
            datastores_upload = response_datastore.get('datastores_upload', [])
            print(f"Datastores: {datastores_upload}")
            

            for datastore in datastores_upload:
                selected_ds = datastore[1]
                BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
                response_bucket = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id,'dataset_type':dataset_type}, cookies=request.COOKIES, timeout=5)
                if response_bucket.status_code == 200:
                    response_b = response_bucket.json()
                    buckets_upload = response_b.get('buckets_upload', [])
                    print(f"Buckets: {buckets_upload}")
                    
                    for bucket in buckets_upload:
                        selected_bucket = bucket[1]
                        print(f"Selected Bucket: {selected_bucket}")
                        
                        BB_LIST_OBJECTS = f'http://127.0.0.1:9000/api/{selected_ds}/{selected_bucket}/objects'
                        response_object = requests.post(BB_LIST_OBJECTS, json={'owner_id': owner_id,'dataset_type':dataset_type}, cookies=request.COOKIES, timeout=5)
                        if response_object.status_code == 200:
                            response_o = response_object.json()
                            print(f"Response from BB: {response_o}")
                            datasets= response_o.get('datasets', [])
                            print(f"Datasets from BB: {datasets}")
                            all_datasets.extend(datasets)
                            print(f"All Datasets: {all_datasets}")

        return render(request, 'list_datasets.html', {'owner_id':owner_id,'dataset_type': dataset_type, 'datasets': all_datasets, 'static_path': static_path})
            
        
        
# View a specific dataset from BB
class ViewDataset(APIView):
    def get(self, request, file_id, file_path):
        try:
            print(f"Viewing file Id: {file_id}")
            print(f"Viewing file Path: {file_path}")

            BB_VIEW_OBJECT = f'http://127.0.0.1:9000/api/{file_id}/view_object'
            
            response = requests.post(BB_VIEW_OBJECT, json={'file_id': file_id, 'file_path': file_path}, cookies=request.COOKIES, timeout=5)
            print(f"POST status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                file_path = response_data.get('file_path')
                content_type = response_data.get('content_type', '')
                file_name = response_data.get('file_name', '')
                file_size = response_data.get('file_size', 0)

                print(f"Received file_path: {file_path}")
                print(f"Received content_type: {content_type}")

                file_response = requests.get(file_path, cookies=request.COOKIES)
                print(f"GET file status: {file_response.status_code}")

                if 'text/csv' in content_type:
                    csv_file = StringIO(file_response.text)
                    reader = csv.reader(csv_file.read().splitlines())
                    rows = list(reader)
                    return render(request, 'view_dataset.html', {'rows': rows, 'file_path': file_path, 'content_type': content_type, 'file_name': file_name, 'file_size': file_size})
                

                elif 'image' in content_type:
                    return HttpResponseRedirect(file_path)

                else:
                    return render(request, 'view_dataset.html', {'file_path': file_path, 'content_type': content_type, 'file_name': file_name, 'file_size': file_size})

            else:
                print(f"POST to BB_VIEW_FILE failed: {response.content}")
                return HttpResponse("Failed to get file path", status=500)

        except Exception as e:
            print(f"Exception in ViewDataset: {str(e)}")
            return HttpResponse(f"Exception occurred: {str(e)}", status=500)




# Delete a specific file from BB
class DeleteFile(APIView):
    def get(self, request):
        owner_id = request.GET.get('owner_id')
        dataset_type = request.GET.get('dataset_type')
        file_id = request.GET.get('file_id')
        
        print(f"Owner_id: {owner_id}, Dataset Type: {dataset_type}, file_id: {file_id}")
        
        BB_DELETE_OBJECT=f"http://127.0.0.1:9000/api/{file_id}/delete_object"
        response_delete = requests.post(BB_DELETE_OBJECT, json={'owner_id': owner_id, 'dataset_type':dataset_type}, cookies=request.COOKIES, timeout=5)
        
        if response_delete.status_code == 200:
            print("File deleted successfully")
        elif response_delete.status_code == 403:
            print("Unauthorized access to delete file")
        else:
            print(f"Failed to delete file: {response_delete.status_code}")

        url = f"/api/list_datasets?owner_id={owner_id}&dataset_type={dataset_type}"
        return HttpResponseRedirect(url)
        

# Delete a specific bucket from BB
class DeleteBuckets(APIView):
    def get(self, request):
        storage = get_messages(request)
        list(storage)
        
        owner_id = request.GET.get('owner_id')
        static_path = request.POST.get('static_path', '/home/cc/nb/bytebridge/datastore')
        selected_ds = request.GET.get('selected_ds', '')
        
        response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id,'include_public':True}, cookies=request.COOKIES,  timeout=5)
        
        if response_ds.status_code == 200:
            response_data = response_ds.json()
            datastores_upload = response_data.get('datastores_upload', [])
            print(f"Datastores in Get for deletion: {datastores_upload}")
            
            if not selected_ds:
                BB_LIST_BUCKETS = 'http://127.0.0.1:9000/api/buckets'
                return render(request, 'bucket_deletion.html', {
                    'owner_id': owner_id,
                    'static_path': static_path,
                    'datastores_upload': datastores_upload,
                    'selected_ds': selected_ds
                })
            
            else:
                BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
            
            response_bucket = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
            if response_bucket.status_code == 200:
                response_data = response_bucket.json()
                buckets_upload = response_data.get('buckets_upload', [])
                return render(request, 'bucket_deletion.html', {
                    'owner_id': owner_id,
                    'static_path': static_path,
                    'selected_ds': selected_ds,
                    'datastores_upload': datastores_upload,
                    'buckets_upload': buckets_upload
                })
        
        messages.error(request, 'Failed to retrieve datastores.')
        return render(request, 'bucket_deletion.html', {'owner_id': owner_id, 'static_path': static_path})


    def post(self, request):
        storage = get_messages(request)
        list(storage)
        
        owner_id = request.POST.get('owner_id')
        selected_ds = request.POST.get('selected_ds','')
        selected_bucket = request.POST.get('selected_bucket', '')
        
        print(f"Owner ID: {owner_id}, Selected Datastore: {selected_ds}, Selected Bucket: {selected_bucket}")

        response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id, 'include_public':True}, cookies=request.COOKIES, timeout=5)
        datastores_upload = response_ds.json().get('datastores_upload', []) if response_ds.status_code == 200 else []
        
        buckets_upload = []
        if selected_ds:
            BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
            response_bucket = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id},cookies=request.COOKIES, timeout=5)
            if response_bucket.status_code == 200:
                buckets_upload = response_bucket.json().get('buckets_upload',[])
                print(f"Buckets in Post for Deletion: {buckets_upload}")
        
                if selected_bucket:

                    BB_DELETE_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/{selected_bucket}/delete_buckets'
                    response = requests.post(BB_DELETE_BUCKETS, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
                    
                    if response.status_code == 200:
                        messages.success(request, 'Bucket deleted successfully')
                    
                    #if response.status_code == 404:
                    #    messages.error(request, 'Bucket can only be deleted by its owner')
                    
                    else:
                        messages.error(request, 'Failed to delete bucket. Try again later')
                        
        return render(request, 'bucket_deletion.html', {
            'owner_id': owner_id,
            'static_path': static_path,
            'selected_ds': selected_ds,
            'selected_bucket': selected_bucket,
            'datastores_upload': datastores_upload,
            'buckets_upload': buckets_upload
        })


# Create a new non-default bucket in BB
# class BucketCreation(APIView):
#     def get(self,request):
#         storage = get_messages(request)
#         list(storage)
#         owner_id = request.GET.get('owner_id')
#         selected_ds = request.GET.get('datastore_id')
#         print(f"Owner ID: {owner_id}, Datastore: {selected_ds}")
#         return render(request, 'bucket_creation.html', {'owner_id': owner_id, 'static_path': static_path})

#     def post(self, request):
#         owner_id = request.GET.get('owner_id')
#         static_path = request.POST.get('static_path')
#         selected_ds = request.GET.get('datastore_id')
#         bucket_name = request.POST.get('bucket_name')
#         private_permissions = request.POST.get('private_permissions')
        
#         print(f"Owner ID: {owner_id}, Datastore_Id: {selected_ds}, Bucket Name: {bucket_name}, Private Permissions: {private_permissions}")
        
#         BB_CREATE_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/create_buckets'
        
#         response = requests.post(BB_CREATE_BUCKETS, json={'owner_id': owner_id,
#                             'bucket_name': bucket_name, 'private_permissions': private_permissions},cookies=request.COOKIES, timeout=5)
        
#         if response.status_code == 200:
#             messages.success(request, "New Bucket created successfully")

#         else:
#             messages.error(request, "Failed to create new bucket")
        
#         return render(request, 'bucket_creation.html', {'owner_id': owner_id, 'static_path': static_path})



# Bucket settings for BB
# class NC_Bucket_Settings(APIView):
#     def get(self, request):
#         storage = get_messages(request)
#         list(storage)
#         owner_id = request.GET.get('owner_id')
#         selected_ds = request.GET.get('selected_ds','')

#         response_ds = requests.post(BB_DATASTORES, json={'owner_id': owner_id,'include_public':True}, cookies=request.COOKIES,  timeout=5)
#         if response_ds.status_code == 200:
#             response_data = response_ds.json()
#             datastores_upload = response_data.get('datastores_upload', []) 

#             if not selected_ds:
#                 BB_LIST_BUCKETS = 'http://127.0.0.1:9000/api/buckets'
#                 return render(request, 'bucket_settings.html', {
#                     'owner_id': owner_id,
#                     'static_path': static_path,
#                     'datastores_upload': datastores_upload,
#                     'selected_ds': selected_ds
#                 })       


#             else:
#                 BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
        
#             response_bucket = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
#             if response_bucket.status_code == 200:
#                 response_data = response_bucket.json()
#                 buckets_upload = response_data.get('buckets_upload', [])
#                 return render(request, 'bucket_settings.html', {
#                     'owner_id': owner_id,
#                     'static_path': static_path,
#                     'selected_ds': selected_ds,
#                     'datastores_upload': datastores_upload,
#                     'buckets_upload': buckets_upload
#                 })
        
#             else:
#                 messages.error(request, 'No buckets found in the selected datastore.')
#                 return render(request, 'bucket_settings.html', {
#                     'owner_id': owner_id,
#                     'static_path': static_path,
#                     'selected_ds': selected_ds,
#                     'datastores_upload': datastores_upload,
#                 })
#         else:
#             messages.error(request, 'Failed to retrieve datastores. Try again later')
#             return render(request, 'bucket_settings.html', {'owner_id': owner_id, 'static_path': static_path})
        
    
#     def post(self, request):
#         storage = get_messages(request)
#         list(storage)
#         owner_id = request.POST.get('owner_id')
#         selected_bucket = request.POST.get('selected_bucket')
#         private_permissions = request.POST.get('private_permissions')
#         bucket_name = request.POST.get('bucket_name')
#         selected_ds = request.GET.get('selected_ds','')
        
#         print(f"Owner ID: {owner_id}, Selected Bucket: {selected_bucket}, Private Permissions: {private_permissions}, Bucket Name: {bucket_name}")

#         response = requests.post(BB_CHANGE_BUCKET_SETTINGS, json={'owner_id': owner_id, 'selected_bucket': selected_bucket, 
#                                     'private_permissions':private_permissions, 'bucket_name':bucket_name}, cookies=request.COOKIES, timeout=5)
        
#         if response.status_code == 200:
#             messages.success(request, "Bucket settings updated successfully")
        
#         else:
#             messages.error(request, "Failed to update bucket settings")

#         if selected_ds:
#             BB_LIST_BUCKETS = f'http://127.0.0.1:9000/api/{selected_ds}/buckets'
        
#         else:
#             BB_LIST_BUCKETS = 'http://127.0.0.1:9000/api/buckets'
        
#         response_data = requests.post(BB_LIST_BUCKETS, json={'owner_id': owner_id}, cookies=request.COOKIES, timeout=5)
#         if response_data.status_code == 200:
#             response_data = response_data.json()  
#             buckets_upload = response_data.get('buckets_upload',[]) 
#             return render(request, 'bucket_settings.html', {'buckets_upload': buckets_upload , 'owner_id': owner_id})

