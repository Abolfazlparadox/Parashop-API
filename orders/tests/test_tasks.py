from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order, OrderItem
from users.models import UserAddress
from decimal import Decimal

# ایمپورت کردن تسکِ سلری
from orders.tasks import cancel_unpaid_orders

User = get_user_model()


class CeleryTasksTests(TestCase):
    def setUp(self):
        # ۱. ساخت کاربر
        self.user = User.objects.create_user(username='test_bot', phone_number='09998887777', password='123')

        # ۲. ساخت آدرس
        self.address = UserAddress.objects.create(
            user=self.user,
            title="خانه",
            receiver_name="تستر",
            receiver_phone="09998887777",
            province="تهران",
            city="تهران",
            postal_address="خیابان تست",
            postal_code="1234567890"
        )

        # ۳. ساخت دسته‌بندی و محصول (موجودی اولیه: ۵)
        self.category = Category.objects.create(title_en='Tech', title_fa='تکنولوژی')
        self.product = Product.objects.create(
            category=self.category,
            title_en='Test Laptop',
            title_fa='لپ‌تاپ تستی',
            price=Decimal('1000.00'),
            inventory=5
        )

    def test_cancel_old_unpaid_order(self):
        """تست: آیا سفارشی که بیشتر از ۱۵ دقیقه ازش گذشته لغو می‌شه؟"""

        # ثبت سفارش در وضعیت pending
        order = Order.objects.create(user=self.user, address=self.address, total_paid=2000, status='pending')

        # افزودن ۲ تا لپ‌تاپ به سفارش
        OrderItem.objects.create(order=order, product=self.product, price=1000, quantity=2)

        # شبیه‌سازی کم شدن موجودی انبار هنگام ثبت سفارش (موجودی می‌شه ۳)
        self.product.inventory -= 2
        self.product.save()

        # ⏳ جادوی سفر در زمان: تاریخ ثبت سفارش رو می‌بریم به ۲۰ دقیقه پیش
        old_time = timezone.now() - timedelta(minutes=20)
        # برای دور زدن auto_now_add از متد update استفاده می‌کنیم
        Order.objects.filter(id=order.id).update(created_at=old_time)

        # 🚀 اجرای مستقیم تسک سلری (بدون نیاز به صبر کردن)
        cancel_unpaid_orders()

        # رفرش کردن دیتا از دیتابیس
        order.refresh_from_db()
        self.product.refresh_from_db()

        # بررسی نتایج: باید لغو شده باشه و موجودی برگرده به ۵
        self.assertEqual(order.status, 'canceled')
        self.assertEqual(self.product.inventory, 5)

    def test_do_not_cancel_recent_order(self):
        """تست: آیا سفارشی که فقط ۲ دقیقه ازش گذشته، دست‌نخورده باقی می‌مونه؟"""

        order = Order.objects.create(user=self.user, address=self.address, total_paid=2000, status='pending')
        OrderItem.objects.create(order=order, product=self.product, price=1000, quantity=2)

        self.product.inventory -= 2
        self.product.save()

        # زمان سفارش رو می‌بریم به ۲ دقیقه پیش
        recent_time = timezone.now() - timedelta(minutes=2)
        Order.objects.filter(id=order.id).update(created_at=recent_time)

        # اجرای تسک سلری
        cancel_unpaid_orders()

        order.refresh_from_db()
        self.product.refresh_from_db()

        # بررسی نتایج: نباید لغو شده باشه و موجودی همون ۳ باقی بمونه
        self.assertEqual(order.status, 'pending')
        self.assertEqual(self.product.inventory, 3)