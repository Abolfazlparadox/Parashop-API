from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    جدول اصلی کاربر - فقط فیلدهای حیاتی احراز هویت و امنیت
    """
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )
    # فیلدهای تایید هویت برای جلوگیری از کاربران فیک
    is_phone_verified = models.BooleanField(default=False, verbose_name="Is Phone Verified")
    is_email_verified = models.BooleanField(default=False, verbose_name="Is Email Verified")

    # تفکیک نقش‌ها برای دسترسی‌های نقش‌محور (RBAC) در آینده
    is_customer = models.BooleanField(default=True, verbose_name="Is Customer")
    is_vendor = models.BooleanField(default=False, verbose_name="Is Vendor")  # برای سیستم‌های مارکت‌پلیس

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username or str(self.phone_number)


class UserProfile(models.Model):
    """
    جدول پروفایل کاربر - اطلاعات تکمیلی و بیزینسی
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    national_code = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="National Code")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Birth Date")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Gender")

    # فیلد سیگنال برای ساخت خودکار پروفایل هنگام ثبت نام کاربر
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserAddress(models.Model):
    """
    سیستم چندآدرسه برای ارسال کالا
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50, help_text="مثلا: خانه، محل کار", verbose_name="Address Title")

    # مشخصات گیرنده (شاید کاربر بخواهد برای شخص دیگری سفارش بفرستد)
    receiver_name = models.CharField(max_length=100, verbose_name="Receiver Full Name")
    receiver_phone = models.CharField(max_length=15, verbose_name="Receiver Phone Number")

    # اطلاعات جغرافیایی
    province = models.CharField(max_length=100, verbose_name="Province")
    city = models.CharField(max_length=100, verbose_name="City")
    postal_address = models.TextField(verbose_name="Postal Address")
    postal_code = models.CharField(max_length=10, verbose_name="Postal Code")

    is_default = models.BooleanField(default=False, verbose_name="Is Default Address")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"