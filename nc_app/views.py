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

from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
import jwt
from django.conf import settings

# Create your views here.
global static_path
static_path = r"/home/areena/neurobazaar/bytebridge/bb_app/datastore"


BB_CREATE_DS = 'http://127.0.0.1:9000/api/user_datastore'
BB_SEND_USER_DATASTORES = 'http://127.0.0.1:9000/api/send_user_datastores'
BB_CHANGE_DS_SETTINGS = 'http://127.0.0.1:9000/api/change_ds_settings'



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

@api_view(['POST'])
@permission_classes([AllowAny])  
def connect_bytebridge(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response({"error": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(f"🔐 Token received and decoded: {decoded}")
        # You can register/log ByteBridge's IP or ID here
        return Response({"message": "ByteBridge connected", "user": decoded}, status=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    
import secrets  # ✅ for secure key generation

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_bytebridge_instance(request):
    try:
        owner_id = request.user.id
        data = request.data
        ip_address = data.get("ip_address")
        port = data.get("port")
        exposed_path = data.get("exposed_path")

        if not all([ip_address, port, exposed_path]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        access_key = secrets.token_hex(32)  # ✅ Secure 64-character access key

        instance = BBInstances.objects.create(
            owner_id=owner_id,
            ip_address=ip_address,
            port=port,
            exposed_path=exposed_path,
            datastore_name=f"{ip_address}:{port}",
            access_key=access_key
        )

        return Response({
            "message": "ByteBridge registered successfully",
            "access_key": access_key
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
