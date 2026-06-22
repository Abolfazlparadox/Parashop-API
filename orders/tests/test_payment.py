from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from orders.models import Order, Payment
from unittest.mock import patch
from decimal import Decimal

User = get_user_model()


class PaymentFlowTests(APITestCase):
    def setUp(self):
        # ۱. ساخت کاربر و احراز هویت
        self.user = User.objects.create_user(username='pay_test', phone_number='09123334444', password='pwd')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # ۲. ساخت یک سفارش تستی (فرض می‌کنیم آدرس رو مجازاً می‌ذاریم None یا اگر اجباریه باید آدرس بسازیم)
        self.order = Order.objects.create(
            user=self.user,
            total_paid=Decimal('500000.00'),  # ۵۰۰ هزار تومان
            status='pending'
        )

    # 🛑 جادوی Mock: ما تابع send_request سرویس زرین‌پال رو جعل می‌کنیم
    @patch('orders.services.zarinpal.ZarinPalService.send_request')
    def test_payment_request_success(self, mock_send_request):
        # به داکر می‌گیم: هر وقت کسی به send_request زنگ زد، این جوابِ دروغین رو بهش بده
        mock_send_request.return_value = {
            "success": True,
            "authority": "A00000000000000000000000000000000000",
            "payment_url": "https://sandbox.zarinpal.com/pg/StartPay/A0000000000"
        }

        url = f'/api/v1/orders/{self.order.id}/pay/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_url', response.data)

        # بررسی می‌کنیم که در دیتابیس رکورد Payment ساخته شده باشد
        self.assertTrue(
            Payment.objects.filter(order=self.order, authority="A00000000000000000000000000000000000").exists())

    @patch('orders.services.zarinpal.ZarinPalService.verify_payment')
    def test_payment_verify_success(self, mock_verify_payment):
        # آماده‌سازی رکورد پرداخت (انگار کاربر قبلا رفته درگاه)
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total_paid,
            authority="TEST_AUTHORITY_123",
            status='pending'
        )

        # شبیه‌سازی موفقیت از سمت بانک
        mock_verify_payment.return_value = {
            "success": True,
            "ref_id": "88776655",
            "message": "پرداخت با موفقیت انجام شد."
        }

        url = '/api/v1/orders/payment/verify/'
        # فرانت‌اند بعد از بازگشت از درگاه این دیتا رو می‌فرسته
        payload = {
            "Authority": "TEST_AUTHORITY_123",
            "Status": "OK"
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ref_id'], "88776655")

        # ⚠️ تست‌های امنیتی و حساس
        payment.refresh_from_db()
        self.order.refresh_from_db()

        # وضعیت پرداخت باید success شده باشد
        self.assertEqual(payment.status, 'success')
        # وضعیت سفارش باید processing شده باشد
        self.assertEqual(self.order.status, 'processing')