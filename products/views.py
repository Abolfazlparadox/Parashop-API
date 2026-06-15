from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API مشاهده لیست و جزئیات دسته‌بندی‌ها"""
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)  # دسترسی آزاد برای همه

    def get_queryset(self):
        # فقط دسته‌های فعال را برگردان
        return Category.objects.filter(is_active=True)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """API مشاهده لیست و جزئیات محصولات (بهینه‌شده با select_related)"""
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        # 🔥 جادوی حل مشکل N+1:
        # با select_related('category') جنگو یک JOIN در دیتابیس می‌زند
        return Product.objects.filter(is_active=True).select_related('category')