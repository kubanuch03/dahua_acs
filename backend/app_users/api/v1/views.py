from rest_framework import views, response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from app_users.service.create_user import create_user
from rest_framework import permissions, status, viewsets, serializers



class CreateUser(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        create = create_user()
        if create:
            return response.Response({"status": 200}, status=HTTP_200_OK)
        return response.Response({"status": 400}, status=HTTP_400_BAD_REQUEST)
        
