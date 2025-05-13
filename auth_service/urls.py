from django.urls import path
from django.conf import settings
from .views import *  # Import views from app
from django.urls import re_path


urlpatterns = [
        path('api/register/', RegisterAPI.as_view(), name='register_api'),  # Registration API
        path('api/login/', LoginAPI.as_view(), name='login_api'),  # Login API   
        path('api/nc_connect', NCConnectAPI.as_view(), name='nc_connect_api'),  # to connect NC with BB
        path('auth/verify/', verify_token_view, name='verify-token'),  #  Add token verification API
        
        path('api/nc_ds_settings', NC_DS_Settings.as_view(), name='nc_ds_settings'), # datastore settings from BB
        #path('api/nc_bucket_settings', NC_Bucket_Settings.as_view(), name='nc_bucket_settings'), # bucket settings from BB
        
        re_path(r'^api/get_datastore$', GetDatastoreInfoAPI.as_view(), name='get_datastore_api'), # to get datastore from BB for a user
        #path('api/bucket_creation', BucketCreation.as_view(), name='bucket_creation'), # to create bucket in BB
        path('api/delete_buckets', DeleteBuckets.as_view(), name='delete_buckets'),  # to delete bucket from BB

        path('api/upload_file', UploadFile.as_view(), name='upload_file'), # to upload file to BB
        path('api/list_datasets', ListDatasets.as_view(), name='list_datasets'), # to list datasets from BB
        re_path(r'^api/view/(?P<file_id>[\w-]+)/(?P<file_path>.+)/$', ViewDataset.as_view(), name='view_dataset'), # to view dataset from BB
        path('api/delete_file', DeleteFile.as_view(), name='delete_file'),  # to delete file from BB
        

    ] 