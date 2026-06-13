from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # چون در settings گفتیم همه APIها قفل باشن، اینجا باید دسترسی ثبت‌نام رو برای همه باز کنیم
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer