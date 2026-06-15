from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
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
    """API مشاهده لیست محصولات با قابلیت سرچ، فیلتر و صفحه‌بندی"""
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)

    # معرفی موتورهای فیلتر (این خط اختیاریه چون تو settings گلوبالش کردیم، اما برای خوانایی کد عالیه)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # ۱. فیلترهای دقیق (Exact Match): مثلا کاربر روی دسته موبایل کلیک کرده
    filterset_fields = ['category', 'is_active']

    # ۲. سرچ متنی (LIKE %search%): کلمه‌ای که کاربر در باکس جستجو تایپ می‌کند
    search_fields = ['title_fa', 'title_en', 'description_fa']

    # ۳. مرتب‌سازی (ORDER BY): فیلدهایی که فرانت‌اند می‌تواند بر اساس آن‌ها سورت کند
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category')