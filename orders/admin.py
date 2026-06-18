from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price', 'get_cost']


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'address', 'status', 'total_paid', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'address__postal_address')
    inlines = [OrderItemInline]
    readonly_fields = ('user', 'address', 'total_paid', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        # Orders should be created through the API, not the admin panel
        return False
