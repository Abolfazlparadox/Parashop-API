from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# همیشه از این روش برای صدا زدن مدل کاربر استفاده کن، نه ایمپورت مستقیم!
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    # تنظیم پسورد به صورت write_only تا هرگز در خروجی API نمایش داده نشه
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password')

    def create(self, validated_data):
        # استفاده از create_user برای هش شدن اتوماتیک پسورد
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            phone_number=validated_data.get('phone_number', ''),
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # گرفتن توکن پیش‌فرض با اطلاعات پایه
        token = super().get_token(user)

        # اضافه کردن اطلاعات اختصاصی (Custom Claims)
        token['username'] = user.username
        token['phone_number'] = user.phone_number
        token['is_customer'] = user.is_customer

        return token