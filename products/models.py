from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    مدل دسته‌بندی محصولات با قابلیت تودرتو بودن (Nested)
    """
    # رابطه Self-referential برای ساخت زیردسته‌ها (مثلا: کالای دیجیتال -> موبایل -> سامسونگ)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Category")
    )

    # فیلدهای دوزبانه
    title_fa = models.CharField(max_length=255, verbose_name=_("Title (Persian)"))
    title_en = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Title (English)"))

    # Slug برای آدرس‌های سئو-فرندلی (مثلا /category/mobile-phones)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True, verbose_name=_("Slug"))

    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __str__(self):
        # اگر دسته مادر داشت، اسم مادر رو هم نشون بده تا تو پنل ادمین قاطی نشن
        if self.parent:
            return f"{self.parent.title_fa} > {self.title_fa}"
        return self.title_fa


class Product(models.Model):
    """
    مدل اصلی محصولات فروشگاه
    """
    # استفاده از PROTECT: اگر دسته‌بندی حذف شد، محصولاتش حذف نشوند (جلوگیری از فاجعه دیتابیسی)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_("Category")
    )

    # اطلاعات پایه (دوزبانه)
    title_fa = models.CharField(max_length=255, verbose_name=_("Product Title (Persian)"))
    title_en = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Product Title (English)"))
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)

    description_fa = models.TextField(verbose_name=_("Description (Persian)"))
    description_en = models.TextField(blank=True, null=True, verbose_name=_("Description (English)"))

    # اطلاعات مالی و انبارداری
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_("Price (IRT)"))
    inventory = models.PositiveIntegerField(default=0, verbose_name=_("Inventory / Stock"))

    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        # ایندکس‌گذاری: برای اینکه سرچ روی اسلاگ و وضعیت محصولات در صدم ثانیه انجام شود
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return self.title_fa