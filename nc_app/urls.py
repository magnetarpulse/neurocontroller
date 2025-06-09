from django.urls import path
from django.conf import settings
from .views import *  # Import views from app
from .views import verify_token_view
from . import views

urlpatterns = [
        path('api/register/', RegisterAPI.as_view(), name='register_api'),  # Registration API
        path('api/login/', LoginAPI.as_view(), name='login_api'),  # Login API   
        path('api/nc_connect', NCConnectAPI.as_view(), name='nc_connect_api'),  # to connect NC with BB
        path('api/get_datastore', GetDatastoreAPI.as_view(), name='get_datastore_api'),  # to get datastore from NC
        path('api/nc_ds_settings', NC_DS_Settings.as_view(), name='nc_ds_settings'),
        
        

path('verify/', verify_token_view, name='verify-token'),  #  Add token verification API
    path('auth/connect_bytebridge/', connect_bytebridge, name='connect_bytebridge'),
            path("api/register_bytebridge/", register_bytebridge_instance, name="register_bytebridge"),



    ]