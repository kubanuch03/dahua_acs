from django.urls import path

from app_users.api.v1.views import  CreateUser

urlpatterns = [
    path('api/v1/create/', CreateUser.as_view(), name='create-user'),    
]

