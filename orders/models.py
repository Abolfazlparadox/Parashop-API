from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from products.models import Product
from users.models import UserAddress

User = get_user_model()


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        SHIPPED = 'shipped', _('Shipped')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name=_('User'))
    address = models.ForeignKey(
        UserAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('Address')
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name=_('Status')
    )
    total_paid = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name=_('Total Paid')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('Order'))
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,  # Prevent deleting a product that is part of an order
        related_name='order_items',
        verbose_name=_('Product')
    )
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Price'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity
