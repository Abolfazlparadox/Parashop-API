from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('title_fa', 'title_en', 'parent', 'is_active')
    search_fields = ('title_fa', 'title_en', 'slug')
    list_filter = ('is_active', 'parent')

    # پر شدن خودکار اسلاگ بر اساس عنوان انگلیسی (یا فارسی)
    prepopulated_fields = {'slug': ('title_en',)}


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('title_fa', 'category', 'price', 'inventory', 'is_active')
    search_fields = ('title_fa', 'title_en', 'slug')
    list_filter = ('is_active', 'category')

    prepopulated_fields = {'slug': ('title_en',)}

    # فیلدهای مالی و وضعیت را در یک ردیف جداگانه دسته‌بندی می‌کنیم
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('category', 'title_fa', 'title_en', 'slug')
        }),
        ('توضیحات', {
            'fields': ('description_fa', 'description_en')
        }),
        ('مالی و انبار', {
            'fields': ('price', 'inventory', 'is_active')
        }),
    )