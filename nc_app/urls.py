from django.urls import path
from django.conf import settings
from .views import *  # Import views from app
from django.urls import re_path

urlpatterns = [
        path('api/register/', RegisterAPI.as_view(), name='register_api'),  # Registration API
        path('api/login/', LoginAPI.as_view(), name='login_api'),  # Login API   
        path('api/nc_connect', NCConnectAPI.as_view(), name='nc_connect_api'),  # to connect NC with BB
        #path('api/get_datastore', GetDatastoreAPI.as_view(), name='get_datastore_api'),  # to get datastore from NC
        path('api/nc_ds_settings', NC_DS_Settings.as_view(), name='nc_ds_settings'),
        path('api/upload_file', UploadFile.as_view(), name='upload_file'),
        re_path(r'^api/get_datastore$', GetDatastoreAPI.as_view(), name='get_datastore_api'),


    ]