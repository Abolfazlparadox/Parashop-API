from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title_fa', 'title_en', 'slug', 'parent', 'is_active')

class ProductSerializer(serializers.ModelSerializer):
    # استخراج دیتای دسته‌بندی بدون نیاز به سریالایزر تودرتو (برای پرفورمنس بهتر)
    category_title = serializers.CharField(source='category.title_fa', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'title_fa', 'title_en', 'slug',
            'description_fa', 'description_en',
            'price', 'inventory',
            'category', 'category_title', 'category_slug', # اطلاعات دسته
            'is_active', 'created_at'
        )