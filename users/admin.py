from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import User, UserProfile, UserAddress


# ---------------------------------------------------------
# Inlines (نمایش جداول مرتبط در داخل صفحه اصلی کاربر)
# ---------------------------------------------------------
class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'اطلاعات پروفایل'
    # جلوگیری از ساخت چند پروفایل برای یک یوزر
    max_num = 1


class UserAddressInline(TabularInline):
    model = UserAddress
    extra = 0  # ردیف‌های خالی اضافی رو نشون نده
    verbose_name_plural = 'آدرس‌های کاربر'


# ---------------------------------------------------------
# Main User Admin
# ---------------------------------------------------------
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    # اضافه کردن پروفایل و آدرس به صفحه ویرایش کاربر
    inlines = (UserProfileInline, UserAddressInline)

    # ستون‌هایی که در لیست کاربران نمایش داده می‌شوند
    list_display = ('username', 'phone_number', 'email', 'is_customer', 'is_phone_verified', 'is_active', 'date_joined')

    # فیلترهای کناری صفحه برای پیدا کردن سریع کاربران
    list_filter = ('is_customer', 'is_vendor', 'is_phone_verified', 'is_active', 'is_staff')

    # فیلدهایی که مدیر می‌تواند در باکس جستجو وارد کند
    search_fields = ('username', 'phone_number', 'email', 'profile__national_code')

    # مرتب‌سازی پیش‌فرض (جدیدترین کاربران اول باشند)
    ordering = ('-date_joined',)

    # دسته‌بندی فیلدها در صفحه ویرایش کاربر
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات فروشگاهی و احراز هویت', {
            'fields': (
                'phone_number',
                'is_phone_verified',
                'is_email_verified',
                'is_customer',
                'is_vendor'
            )
        }),
    )