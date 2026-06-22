from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Order, OrderItem, Coupon
from django.utils.html import format_html


# 1. تعریف Inline برای نمایش اقلام سفارش درون صفحه سفارش اصلی
class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0  # تعداد ردیف‌های خالی پیش‌فرض
    readonly_fields = ('product', 'price', 'quantity')  # فیلدهایی که نباید در ادمین تغییر کنن
    can_delete = False

    # تغییر اسم در پنل ادمین
    verbose_name = "آیتم سفارش"
    verbose_name_plural = "اقلام سفارش"


# 2. تعریف کلاس اصلی ادمین برای سفارشات
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # فیلدهایی که در لیست اصلی نشون داده می‌شن
    list_display = ['id', 'user', 'get_status_badge', 'total_paid', 'created_at']

    # فیلدهایی که می‌تونی روشون فیلتر بزنی (ستون سمت راست)
    list_filter = ['status', 'created_at']

    # قابلیت سرچ کردن سفارش بر اساس نام کاربر یا تلفن
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'id']

    # اضافه کردن اقلام سفارش به پایین صفحه جزئیات سفارش
    inlines = [OrderItemInline]

    # فیلدهایی که فقط خواندنی هستن (ادمین نباید بتونه مبلغ رو دستی عوض کنه!)
    readonly_fields = ['total_paid', 'created_at', 'updated_at']

    # مرتب‌سازی پیش‌فرض (جدیدترین‌ها اول)
    ordering = ['-created_at']

    # متد کاستوم برای نمایش وضعیت با استایل‌های زیبای Unfold
    @admin.display(description='وضعیت')
    def get_status_badge(self, obj):
        # فرض می‌کنیم وضعیت‌های شما اینا هستن، رنگ‌ها رو بر اساس نیازت عوض کن
        colors = {
            'pending': 'bg-yellow-500',  # زرد برای در انتظار
            'processing': 'bg-blue-500',  # آبی برای در حال پردازش
            'shipped': 'bg-indigo-500',  # نیلی برای ارسال شده
            'delivered': 'bg-green-500',  # سبز برای تحویل داده شده
            'canceled': 'bg-red-500',  # قرمز برای لغو شده
        }

        # اگر status در مدل شما اسم دیگه‌ای داره، obj.status رو عوض کن
        color_class = colors.get(getattr(obj, 'status', 'pending'), 'bg-gray-500')
        status_display = obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status

        return format_html(
            '<span class="px-2 py-1 rounded text-white text-xs font-semibold {}">{}</span>',
            color_class,
            status_display
        )

# 3. (اختیاری) اگر می‌خوای اقلام رو جداگانه هم در منو ببینی، ولی معمولاً این کار رو نمی‌کنن
@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price']


# این کلاس رو در هر کجای فایل (مثلاً پایین کلاس OrderAdmin) اضافه کن
@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

    # برای اینکه تو پنل ادمین، تاریخ‌ها رو راحت‌تر انتخاب کنیم
    ordering = ['-valid_to']