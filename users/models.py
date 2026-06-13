from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # شماره تماس برای یک فروشگاه بسیار حیاتی است (به عنوان فیلد یکتا)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )

    # برای آینده که بخواهیم نقش‌های مختلف (مشتری، ادمین فروش، پیک) تعریف کنیم
    is_customer = models.BooleanField(default=True, verbose_name="Is Customer")

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username or self.email