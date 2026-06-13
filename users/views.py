from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserAddressSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer,UserProfileSerializer,ChangePasswordSerializer
from rest_framework import status, views
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .utils import SMSService
from .models import UserProfile, UserAddress

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


class RequestOTPView(views.APIView):
    """API درخواست کد تایید برای فراموشی رمز یا لاگین بدون رمز"""
    permission_classes = (AllowAny,)

    # استفاده از همون سیستم Throttling که ساختیم برای جلوگیری از اسپم پیامک
    throttle_scope = 'anon'

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "شماره تماس الزامی است."}, status=status.HTTP_400_BAD_REQUEST)

        # بررسی وجود کاربر
        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return Response({"error": "کاربری با این شماره یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

        # تولید کد و ذخیره در کش برای ۲ دقیقه (120 ثانیه)
        otp_code = SMSService.generate_otp()
        cache.set(f"otp_{phone_number}", otp_code, timeout=120)

        # ارسال پیامک (شبیه‌سازی شده)
        SMSService.send_otp(phone_number, otp_code)

        return Response({"message": "کد تایید ارسال شد."}, status=status.HTTP_200_OK)


class ResetPasswordWithOTPView(views.APIView):
    """API بررسی کد و تغییر رمز عبور"""
    permission_classes = (AllowAny,)

    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([phone_number, otp_code, new_password]):
            return Response({"error": "ارسال شماره، کد تایید و رمز جدید الزامی است."},
                            status=status.HTTP_400_BAD_REQUEST)

        # خواندن کد از حافظه کش
        cached_otp = cache.get(f"otp_{phone_number}")

        if cached_otp is None or cached_otp != otp_code:
            return Response({"error": "کد تایید نامعتبر است یا منقضی شده."}, status=status.HTTP_400_BAD_REQUEST)

        # تغییر رمز عبور
        user = get_object_or_404(User, phone_number=phone_number)
        user.set_password(new_password)
        user.save()

        # پاک کردن کد از کش پس از استفاده موفق برای جلوگیری از استفاده مجدد
        cache.delete(f"otp_{phone_number}")

        return Response({"message": "رمز عبور با موفقیت تغییر کرد."}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """API مشاهده و ویرایش پروفایل کاربر لاگین شده"""
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    # نیازی به پاس دادن ID در URL نیست، پروفایل رو از روی توکن کاربر پیدا می‌کنیم
    def get_object(self):
        return self.request.user.profile


class ChangePasswordView(generics.UpdateAPIView):
    """API تغییر رمز برای کاربرانی که داخل پنل خود هستند"""
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # چک کردن اینکه آیا رمز قبلی رو درست وارد کرده یا نه
            if not user.check_password(serializer.validated_data.get("old_password")):
                return Response({"old_password": ["رمز عبور فعلی اشتباه است."]}, status=status.HTTP_400_BAD_REQUEST)

            # تغییر به رمز جدید و ذخیره در دیتابیس
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            return Response({"message": "رمز عبور با موفقیت تغییر کرد."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAddressViewSet(viewsets.ModelViewSet):
    """API کامل مدیریت آدرس‌های کاربر (نمایش، ساخت، ویرایش، حذف)"""
    serializer_class = UserAddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # هر کاربر فقط باید آدرس‌های خودش رو ببینه، نه بقیه رو!
        return UserAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # موقع ساخت آدرس جدید، آیدی کاربری که درخواست داده رو به عنوان صاحب آدرس ثبت می‌کنیم
        serializer.save(user=self.request.user)