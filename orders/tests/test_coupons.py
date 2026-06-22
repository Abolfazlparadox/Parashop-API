from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from orders.models import Order, Coupon
from users.models import UserAddress
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

User = get_user_model()


class CouponAPITests(APITestCase):
    def setUp(self):
        # 🔑 1. ساخت کاربر و احراز هویت
        self.user = User.objects.create_user(username='coupon_tester', phone_number='09112223344', password='123')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # 2. ساخت آدرس
        self.address = UserAddress.objects.create(
            user=self.user,
            title="خانه",
            receiver_name="تستر",
            receiver_phone="09112223344",
            province="تهران",
            city="تهران",
            postal_address="خیابان تخفیف",
            postal_code="1234567890"
        )

        # 3. ساخت یک سفارش در انتظار پرداخت با مبلغ ۱۰۰ هزار تومان
        self.order = Order.objects.create(
            user=self.user,
            address=self.address,
            total_paid=Decimal('100000.00'),
            status='pending'
        )

        now = timezone.now()

        # 🎁 4. ساخت کوپن‌های تستی
        # الف) کوپن معتبر: 20 درصد تخفیف (اعتبار از دیروز تا فردا)
        self.valid_coupon = Coupon.objects.create(
            code="YALDA20",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=20,
            active=True
        )

        # ب) کوپن منقضی شده: 50 درصد تخفیف (اعتبارش دیروز تموم شده)
        self.expired_coupon = Coupon.objects.create(
            code="OLD50",
            valid_from=now - timedelta(days=5),
            valid_to=now - timedelta(days=1),  # در گذشته است
            discount=50,
            active=True
        )

        # ج) کوپن غیرفعال شده توسط ادمین
        self.inactive_coupon = Coupon.objects.create(
            code="OFF10",
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            discount=10,
            active=False  # ادمین دکمه خاموش رو زده
        )

    def test_apply_valid_coupon_success(self):
        """تست: آیا اعمال یک کوپن معتبر، قیمت را به درستی کاهش می‌دهد؟"""
        url = f'/api/v1/orders/{self.order.id}/apply_coupon/'
        payload = {"code": "YALDA20"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("discount_applied", response.data)

        # 100 هزار تومان با 20 درصد تخفیف باید بشه 80 هزار تومان
        # 20 هزار تومان تخفیف اعمال شده
        self.assertEqual(float(response.data['discount_applied']), 20000.0)
        self.assertEqual(float(response.data['new_total']), 80000.0)

        # بررسی در سطح دیتابیس
        self.order.refresh_from_db()
        self.assertEqual(self.order.coupon, self.valid_coupon)
        self.assertEqual(self.order.discount_amount, Decimal('20000.00'))
        self.assertEqual(self.order.total_paid, Decimal('80000.00'))

    def test_apply_expired_coupon_fails(self):
        """تست: جلوگیری از اعمال کوپن منقضی شده (تاریخ گذشته)"""
        url = f'/api/v1/orders/{self.order.id}/apply_coupon/'
        payload = {"code": "OLD50"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "این کد تخفیف منقضی یا غیرفعال شده است.")

        # مطمئن می‌شیم مبلغ سفارش تغییر نکرده باشه
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_paid, Decimal('100000.00'))

    def test_apply_inactive_coupon_fails(self):
        """تست: جلوگیری از اعمال کوپنی که توسط ادمین غیرفعال شده"""
        url = f'/api/v1/orders/{self.order.id}/apply_coupon/'
        payload = {"code": "OFF10"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "این کد تخفیف منقضی یا غیرفعال شده است.")

    def test_apply_coupon_on_non_pending_order_fails(self):
        """تست: نمی‌توان روی سفارشی که پرداخت شده یا لغو شده کد تخفیف زد"""
        # تغییر وضعیت سفارش به 'در حال پردازش' (پرداخت شده)
        self.order.status = 'processing'
        self.order.save()

        url = f'/api/v1/orders/{self.order.id}/apply_coupon/'
        payload = {"code": "YALDA20"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "فقط روی سفارشات در انتظار پرداخت می‌توان کد تخفیف اعمال کرد.")

    def test_cannot_apply_multiple_coupons_on_one_order(self):
        """تست: یک سفارش نباید دو بار تخفیف بگیرد (جلوگیری از انباشت تخفیف)"""
        # کاربر بار اول کوپن را اعمال می‌کند (موفق)
        url = f'/api/v1/orders/{self.order.id}/apply_coupon/'
        self.client.post(url, {"code": "YALDA20"})

        # کاربر طمع می‌کند و می‌خواهد دوباره همان کوپن (یا کوپن دیگری) را بزند!
        response = self.client.post(url, {"code": "YALDA20"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "یک کد تخفیف قبلاً روی این سفارش اعمال شده است.")