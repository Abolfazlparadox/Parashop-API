from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import override_settings
from django.core.cache import cache
from .models import UserAddress

User = get_user_model()


# =======================================================
# 1. تست‌های احراز هویت (بدون استفاده از کش)
# =======================================================
@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
)
class UserAuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone_number': '09123456789',
            'password': 'StrongPassword123!'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_registration_success(self):
        new_user_data = {'username': 'newuser', 'phone_number': '09987654321', 'password': 'NewPassword123!'}
        response = self.client.post(self.register_url, new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertTrue(hasattr(User.objects.get(username='newuser'), 'profile'))

    def test_user_login_success(self):
        login_data = {'username': 'testuser', 'password': 'StrongPassword123!'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_login_wrong_password(self):
        login_data = {'username': 'testuser', 'password': 'WrongPassword!'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_jwt_claims(self):
        login_data = {'username': 'testuser', 'password': 'StrongPassword123!'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username'), self.user_data['username'])

    def test_token_refresh(self):
        login_response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'StrongPassword123!'},
                                          format='json')
        refresh_token = login_response.data['refresh']
        response = self.client.post(reverse('token_refresh'), {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_registration_duplicate_username(self):
        duplicate_data = {'username': 'testuser', 'phone_number': '09000000000', 'password': 'SomePassword123!'}
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =======================================================
# 2. تست‌های پنل کاربری (پروفایل، آدرس، تغییر رمز)
# =======================================================
@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
)
class UserDashboardTests(APITestCase):

    def setUp(self):
        self.profile_url = reverse('user_profile')
        self.change_password_url = reverse('change_password')
        # نام استاندارد روتر در DRF برای لیست کردن ViewSetها
        self.address_list_url = reverse('user-address-list')

        # ساخت و لاگین اجباری کاربر برای تست APIهای محافظت‌شده
        self.user = User.objects.create_user(username='dashuser', phone_number='09222222222', password='MyPassword123!')
        self.client.force_authenticate(user=self.user)

    def test_get_and_update_profile(self):
        """تست دریافت و ویرایش اطلاعات پروفایل (ترکیب جدول User و Profile)"""
        data = {'first_name': 'Ali', 'national_code': '1234567890'}
        response = self.client.patch(self.profile_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Ali')
        self.assertEqual(response.data['national_code'], '1234567890')

    def test_change_password_success(self):
        """تست تغییر رمز عبور از داخل پنل کاربری"""
        data = {'old_password': 'MyPassword123!', 'new_password': 'NewStrongPassword123!'}
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword123!'))

    def test_create_user_address(self):
        """تست ثبت آدرس جدید برای کاربر"""
        data = {
            'title': 'خانه',
            'receiver_name': 'علی تست',
            'receiver_phone': '09222222222',
            'province': 'تهران',
            'city': 'تهران',
            'postal_address': 'خیابان تستی، پلاک 1',
            'postal_code': '1234567890'
        }
        response = self.client.post(self.address_list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserAddress.objects.filter(user=self.user).count(), 1)


# =======================================================
# 3. تست‌های فراموشی رمز (تست کش و OTP)
# =======================================================
@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
)
class UserPasswordResetTests(APITestCase):

    def setUp(self):
        self.forgot_url = reverse('forgot_password')
        self.reset_url = reverse('reset_password')
        self.user = User.objects.create_user(username='otpuser', phone_number='09333333333', password='OldPassword123!')

    def test_request_otp_success(self):
        """تست درخواست پیامک و ذخیره کد در کش سرور"""
        response = self.client.post(self.forgot_url, {'phone_number': '09333333333'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cached_otp = cache.get("otp_09333333333")
        self.assertIsNotNone(cached_otp)  # بررسی می‌کنیم که کش خالی نباشد

    def test_reset_password_with_valid_otp(self):
        """تست تغییر رمز با استفاده از کد پیامک‌شده"""
        # یک کد رو دستی تو کش قرار می‌دیم
        cache.set("otp_09333333333", "123456", timeout=120)

        data = {
            'phone_number': '09333333333',
            'code': '123456',
            'new_password': 'RecoveredPassword123!'
        }
        response = self.client.post(self.reset_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('RecoveredPassword123!'))