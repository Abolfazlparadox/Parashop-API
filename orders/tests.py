from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

from products.models import Product, Category
from users.models import UserAddress
from orders.models import Order, OrderItem

User = get_user_model()


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake-orders',
        }
    }
)
class OrderManagementAPITestCase(APITestCase):
    """
    تست‌های یکپارچه برای سیستم سفارشات (تبدیل سبد خرید به فاکتور)
    """

    def setUp(self):
        # ۱. ساخت کاربر و احراز هویت
        self.user = User.objects.create_user(username='orderuser', phone_number='09123456789', password='Password123!')
        self.client.force_authenticate(user=self.user)

        # ۲. ساخت آدرس برای کاربر (برای ثبت سفارش اجباری است)
        self.address = UserAddress.objects.create(
            user=self.user,
            title="خانه",
            province="تهران",
            city="تهران",
            postal_address="خیابان تست، پلاک 1",
            postal_code="1234567890",
            receiver_name="کاربر تستی",
            receiver_phone="09123456789"
        )

        # ۳. ساخت دسته‌بندی و محصولات
        self.category = Category.objects.create(title_fa="تستی", slug="test-cat")
        self.product1 = Product.objects.create(
            category=self.category, title_fa='گوشی آیفون', slug='iphone', price=50000000, inventory=10
        )
        self.product2 = Product.objects.create(
            category=self.category, title_fa='قاب گوشی', slug='case', price=500000, inventory=50
        )

        # آدرس‌های API (فرض بر این است که از روتر با basename='order' استفاده شده)
        self.order_list_url = reverse('order-list')
        self.cart_add_url = reverse('cart_add')

    def test_create_order_successfully_and_clear_cart(self):
        """تست طلایی: ثبت موفق سفارش و خالی شدن خودکار سبد خرید پس از آن"""

        # قدم اول: اضافه کردن ۲ محصول به سبد خرید (Redis)
        self.client.post(self.cart_add_url, {'product_id': self.product1.id, 'quantity': 1}, format='json')
        self.client.post(self.cart_add_url, {'product_id': self.product2.id, 'quantity': 2}, format='json')

        # قدم دوم: درخواست ثبت سفارش با ارسال آیدی آدرس
        data = {'address_id': self.address.id}
        response = self.client.post(self.order_list_url, data, format='json')

        # بررسی موفقیت‌آمیز بودن API
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # بررسی ثبت دقیق در دیتابیس PostgreSQL
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.address, self.address)

        # محاسبه قیمت: (1 * 50,000,000) + (2 * 500,000) = 51,000,000
        self.assertEqual(order.total_paid, 51000000)
        self.assertEqual(order.items.count(), 2)  # دو آیتم باید در سفارش ثبت شده باشد

        # قدم سوم: بررسی پاک شدن سبد خرید موقت
        cart_response = self.client.get(reverse('cart_detail'))
        self.assertEqual(len(cart_response.data['items']), 0)
        self.assertEqual(cart_response.data['total_price'], '0')

    def test_create_order_with_empty_cart_fails(self):
        """تست امنیتی: جلوگیری از ثبت سفارش وقتی سبد خرید خالی است"""
        data = {'address_id': self.address.id}
        response = self.client.post(self.order_list_url, data, format='json')

        # باید ارور 400 بدهد و هیچ سفارشی ثبت نشود
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_get_user_orders_list(self):
        """تست مشاهده لیست سفارشات (تاریخچه خرید کاربر)"""
        # ساخت یک سفارش دستی در دیتابیس
        order = Order.objects.create(
            user=self.user,
            address=self.address,
            total_paid=50000000,
            status='Pending'
        )
        OrderItem.objects.create(order=order, product=self.product1, price=50000000, quantity=1)

        response = self.client.get(self.order_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # بررسی صفحه‌بندی و وجود سفارش
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['total_paid'], '50000000')
        self.assertEqual(response.data['results'][0]['status'], 'Pending')