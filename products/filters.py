import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    # فیلتر برای حداقل و حداکثر قیمت
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')

    # فیلتر سفارشی برای اینکه فقط کالاهای موجود در انبار را نشان دهد
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Product
        # فیلتر دقیق بر اساس آیدی یا اسلاگ دسته‌بندی
        fields = ['category']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(inventory__gt=0)  # فقط کالاهایی که موجودی بیشتر از 0 دارند
        return queryset