from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import ProductFilter

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API مشاهده لیست و جزئیات دسته‌بندی‌ها"""
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)  # دسترسی آزاد برای همه

    def get_queryset(self):
        # فقط دسته‌های فعال را برگردان
        return Category.objects.filter(is_active=True)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ویوست محصولات: پشتیبانی از دریافت لیست محصولات و جزئیات یک محصول
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

    # اضافه کردن موتورهای فیلتر، سرچ و مرتب‌سازی
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # 1. تنظیم کلاس فیلتری که ساختیم (برای قیمت، موجودی و دسته‌بندی)
    filterset_class = ProductFilter

    # 2. فیلدهایی که کاربر می‌تواند در آن‌ها جستجوی متنی کند (Like Search)
    search_fields = ['title_fa', 'title_en', 'description_fa', 'description_en']

    # 3. فیلدهایی که کاربر می‌تواند لیست را بر اساس آن‌ها مرتب کند
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']  # مرتب‌سازی پیش‌فرض: جدیدترین‌ها اول