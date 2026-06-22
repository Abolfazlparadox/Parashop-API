from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order, OrderItem
from users.models import UserAddress
import random
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'تولید دیتای فیک برای فروشگاه (کاربر، محصول، سفارش)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('در حال پاکسازی دیتای قبلی (به جز Superuserها)...'))
        # پاک کردن دیتای قبلی برای تمیز شدن دیتابیس
        Order.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        UserAddress.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS('شروع تولید دیتای جدید...'))

        # 1. ساخت دسته‌بندی‌ها
        categories_data = [
            {'title_en': 'Laptops', 'title_fa': 'لپ‌تاپ‌ها', 'slug': 'laptops'},
            {'title_en': 'Smartphones', 'title_fa': 'گوشی‌های هوشمند', 'slug': 'smartphones'},
            {'title_en': 'Accessories', 'title_fa': 'لوازم جانبی', 'slug': 'accessories'},
        ]
        categories = []
        for cat_data in categories_data:
            cat = Category.objects.create(**cat_data)
            categories.append(cat)

        self.stdout.write('✅ دسته‌بندی‌ها ساخته شدند.')

        # 2. ساخت محصولات
        products_data = [
            ('MacBook Pro M3', 'مک‌بوک پرو', categories[0], 120000000),
            ('Asus ROG Zephyrus', 'ایسوس راگ', categories[0], 95000000),
            ('iPhone 15 Pro', 'آیفون ۱۵ پرو', categories[1], 80000000),
            ('Galaxy S24 Ultra', 'گلکسی اس ۲۴', categories[1], 75000000),
            ('AirPods Pro', 'ایرپاد پرو', categories[2], 12000000),
        ]
        products = []
        for index, prod_data in enumerate(products_data):
            prod = Product.objects.create(
                category=prod_data[2],
                title_en=prod_data[0],
                title_fa=prod_data[1],
                slug=f"product-{index}",
                price=Decimal(prod_data[3]),
                inventory=random.randint(10, 50)
            )
            products.append(prod)

        self.stdout.write('✅ محصولات ساخته شدند.')

        # 3. ساخت کاربران و آدرس‌ها
        users = []
        addresses = []
        for i in range(1, 6):
            user = User.objects.create_user(
                username=f'0912000000{i}',
                phone_number=f'0912000000{i}',
                password='password123',
                first_name=f'کاربر {i}',
                last_name='تستی'
            )
            users.append(user)

            address = UserAddress.objects.create(
                user=user,
                title="خانه",
                receiver_name=f"{user.first_name} {user.last_name}",
                receiver_phone=user.phone_number,
                province="تهران",
                city="تهران",
                postal_address=f"خیابان تستی {i}، پلاک {i}",
                postal_code="1234567890"
            )
            addresses.append(address)

        self.stdout.write('✅ کاربران و آدرس‌ها ساخته شدند.')

        # 4. ساخت سفارشات (Orders) با وضعیت‌های مختلف
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'canceled']  # نام وضعیت‌ها رو با مدل خودت چک کن

        for i in range(15):  # تولید 15 سفارش
            user = random.choice(users)
            address = [a for a in addresses if a.user == user][0]

            order = Order.objects.create(
                user=user,
                address=address,
                total_paid=0,  # بعد از افزودن آیتم‌ها آپدیت میشه
                status=random.choice(statuses)
            )

            total_price = 0
            # اضافه کردن 1 تا 3 محصول به هر سفارش
            for _ in range(random.randint(1, 3)):
                prod = random.choice(products)
                qty = random.randint(1, 2)
                item_price = prod.price * qty
                total_price += item_price

                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    price=prod.price,
                    quantity=qty
                )

            # آپدیت مبلغ نهایی سفارش
            order.total_paid = total_price
            order.save()

        self.stdout.write('✅ 15 سفارش تستی با موفقیت ساخته شد.')
        self.stdout.write(self.style.SUCCESS('🎉 دیتابیس با موفقیت پر شد! حالا به پنل ادمین بروید.'))