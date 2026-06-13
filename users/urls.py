from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LogoutView, RequestOTPView, ResetPasswordWithOTPView,
    UserProfileView, ChangePasswordView, UserAddressViewSet
)

# روتر برای ViewSet آدرس‌ها
router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='user-address')

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),

    # Password Management
    path('password/forgot/', RequestOTPView.as_view(), name='forgot_password'),
    path('password/reset/', ResetPasswordWithOTPView.as_view(), name='reset_password'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    # Addresses (مسیرهای روت شده شامل /addresses/ و /addresses/<id>/)
    path('', include(router.urls)),
]