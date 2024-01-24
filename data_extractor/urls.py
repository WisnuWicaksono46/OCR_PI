from django.urls import path
from .views import extract_folder
from .views import download_zip

urlpatterns = [
    path('', extract_folder, name='extract_folder'),
    path('success/', download_zip, name='download_zip')
]
