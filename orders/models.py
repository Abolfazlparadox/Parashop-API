from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product
from users.models import UserAddress
from django.utils import timezone

User = get_user_model()

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='کد تخفیف')
    valid_from = models.DateTimeField(verbose_name='معتبر از')
    valid_to = models.DateTimeField(verbose_name='معتبر تا')
    # محدود کردن درصد تخفیف بین 0 تا 100
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='درصد تخفیف'
    )
    active = models.BooleanField(default=True, verbose_name='فعال')

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'

    def __str__(self):
        return self.code

    # متدی برای چک کردن اینکه آیا الان میشه از این کوپن استفاده کرد یا نه
    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

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
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL,
                               verbose_name='کد تخفیف استفاده شده')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='مبلغ تخفیف')
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


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
    )

    # رابطه یک-به-چند: هر سفارش می‌تونه چند تلاش برای پرداخت داشته باشه
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')

    # مبلغی که دقیقاً به درگاه ارسال شده (برای جلوگیری از مغایرت‌های مالی)
    amount = models.DecimalField(max_digits=12, decimal_places=0)

    # شناسه یکتای زرین‌پال برای ارجاع کاربر به درگاه (Authority)
    authority = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # کد پیگیری بانکی که بعد از پرداخت موفق از سمت درگاه به ما داده می‌شه
    ref_id = models.CharField(max_length=255, null=True, blank=True)

    # وضعیت تراکنش
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # آی‌پی کاربری که پرداخت رو انجام داده (برای امنیت و پیگیری‌های قانونی)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id} - {self.get_status_display()}"

