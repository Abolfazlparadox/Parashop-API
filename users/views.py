from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # چون در settings گفتیم همه APIها قفل باشن، اینجا باید دسترسی ثبت‌نام رو برای همه باز کنیم
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LogoutView(APIView):
    # فقط کاربرانی که لاگین هستن (توکن معتبر دارن) می‌تونن لاگ‌اوت کنن
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # کلاینت باید رفرش‌توکن رو در بدنه درخواست (body) با کلید "refresh" بفرسته
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)

            # توکن رو به بلک‌لیست اضافه می‌کنیم
            token.blacklist()

            # کد 205 (Reset Content) یک استاندارد خوب برای لاگ‌اوت موفق است
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            # اگر توکن نامعتبر بود یا قبلا باطل شده بود
            return Response(status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    # جایگزین کردن کلاسی که وظیفه تولید توکن را دارد
    serializer_class = CustomTokenObtainPairSerializer