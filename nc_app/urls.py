from django.urls import path
from django.conf import settings
from .views import *  # Import views from app
from django.conf.urls.static import static  # Static files serving
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # Static files serving


if settings.DEBUG:
    datastore_path = settings.DATASTORE['default']['PATH']

    urlpatterns = [
        #path('api/upload/', FileUploadView.as_view(), name='api-file-upload'),
        path('login/', login_page, name='login_page'),    # Login page
        path('register/', register_page, name='register'),  # Registration page
        path ('connect/', connect, name='connect'), # connect BB with NC
    ]

    #urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    #urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Serve static files using staticfiles_urlpatterns
    #urlpatterns += staticfiles_urlpatterns()
   


