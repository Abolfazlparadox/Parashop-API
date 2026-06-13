from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# ثبت مدل کاربر کاستوم در پنل ادمین با استفاده از کلاس استاندارد UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_customer')

    # اضافه کردن فیلدهای جدید به صفحه ویرایش کاربر در پنل ادمین
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('phone_number', 'is_customer')}),
    )