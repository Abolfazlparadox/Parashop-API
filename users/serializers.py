from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, UserAddress

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # اضافه کردن اطلاعات به داخل خود توکن (برای فرانت‌اند)
        token = super().get_token(user)
        token['username'] = user.username
        token['phone_number'] = user.phone_number
        token['is_customer'] = user.is_customer
        return token

    def validate(self, attrs):
        # اضافه کردن اطلاعات به بدنه پاسخ JSON (برای پاس شدن تست شما)
        data = super().validate(attrs)
        data['username'] = self.user.username
        data['phone_number'] = self.user.phone_number
        data['is_customer'] = self.user.is_customer
        return data

# اسم کلاس به همان چیزی که در views.py صدا زده شده تغییر کرد
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'phone_number')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    # این فیلدها از جدول اصلی User خوانده و آپدیت می‌شوند
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'email', 'avatar', 'national_code', 'birth_date', 'gender')

    def update(self, instance, validated_data):
        # جدا کردن دیتای جدول User
        user_data = validated_data.pop('user', {})
        user = instance.user

        if user_data:
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.email = user_data.get('email', user.email)
            user.save()

        # آپدیت کردن دیتای جدول Profile
        return super().update(instance, validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        # فیلد کاربر رو مخفی می‌کنیم تا کسی نتونه آدرس رو برای یوزر دیگه‌ای بسازه
        exclude = ('user',)