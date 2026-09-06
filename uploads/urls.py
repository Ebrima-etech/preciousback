from django.urls import path
from . import views

app_name = 'uploads'

urlpatterns = [
    path('upload/', views.upload_image, name='upload_image'),
    path('delete/', views.delete_image, name='delete_image'),
]
