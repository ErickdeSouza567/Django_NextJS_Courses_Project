from rest_framework import APIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import UserSerializer

from core.utils.exceptions import ValidationError
from core.utils.formatters import format_serializer_error

from django.contrib.auth.hashers import make_password

class SignUpView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request: Request):
        data = {
            "name": request.data.get("name"),
            "email": request.data.get("email"),
            "password": request.data.get("password")
        }
        
        serializer = UserSerializer(data=data)
        
        if not serializer.is_valid():
            raise ValidationError(format_serializer_error(serializer.errors))
        
        user = User.objects.create(
            name=data.get("name"),
            email=data.get("email"),
            password=make_password(data.get("password")
        ))
        
        acces_token = RefreshToken.for_user(user).access_token
        
        return Response({
            
            "user": UserSerializer(user).data,
            "access_token": str(acces_token)
        })