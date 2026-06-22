from django.test import TestCase
from django.db.models import ProtectedError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Category, Product

User = get_user_model()


# =======================================================
# 1. تست‌های دیتابیس و معماری مدل‌ها (Model Tests)
# =======================================================
class ProductCatalogModelTests(TestCase):

    def setUp(self):
        self.parent_category = Category.objects.create(title_fa="الکترونیک", title_en="Electronics", slug="electronics")
        self.child_category = Category.objects.create(parent=self.parent_category, title_fa="لپ‌تاپ",
                                                      title_en="Laptops", slug="laptops")
        self.product = Product.objects.create(
            category=self.child_category, title_fa="مک‌بوک پرو", slug="macbook-pro", price=150000000, inventory=10
        )

    def test_category_creation_and_hierarchy(self):
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(self.parent_category.children.first(), self.child_category)

    def test_category_str_representation(self):
        self.assertEqual(str(self.parent_category), "الکترونیک")
        self.assertEqual(str(self.child_category), "الکترونیک > لپ‌تاپ")

    def test_product_creation_and_relations(self):
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.category, self.child_category)

    def test_category_protect_delete_constraint(self):
        with self.assertRaises(ProtectedError):
            self.child_category.delete()

    def test_parent_category_cascade_delete(self):
        self.product.delete()
        self.parent_category.delete()
        self.assertEqual(Category.objects.count(), 0)


# =======================================================
# 2. تست‌های API، جستجو، فیلتر و صفحه‌بندی (API Tests)
# =======================================================
class ProductCatalogAPITests(APITestCase):

    def setUp(self):
        # 🔑 ۱. ساخت یک کاربر تستی برای احراز هویت
        self.user = User.objects.create_user(
            username='test_shopper',
            phone_number='09121112233',
            password='testpassword123'
        )

        # 🔑 ۲. تولید توکن JWT برای کاربر
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        # 🔑 ۳. قرار دادن توکن در هدر درخواست‌های کلاینت تست
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # ساخت دسته‌بندی‌های تستی
        self.cat_mobile = Category.objects.create(title_fa="موبایل", slug="mobile")
        self.cat_laptop = Category.objects.create(title_fa="لپ‌تاپ", slug="laptop")

        # اضافه کردن فیلد موجودی (inventory) برای تست فیلتر in_stock
        self.p1 = Product.objects.create(
            category=self.cat_mobile, title_fa="آیفون 15", slug="iphone-15", price=50000000, is_active=True, inventory=5
        )
        self.p2 = Product.objects.create(
            category=self.cat_laptop, title_fa="مک‌بوک پرو M3", slug="macbook-pro", price=120000000, is_active=True,
            inventory=0  # ناموجود
        )
        self.p3 = Product.objects.create(
            category=self.cat_laptop, title_fa="لپ‌تاپ لنوو گیمینگ", slug="lenovo", price=40000000, is_active=True,
            inventory=10
        )
        self.p4_inactive = Product.objects.create(
            category=self.cat_mobile, title_fa="گوشی نوکیا قدیمی", slug="nokia", price=1000000, is_active=False,
            inventory=2
        )

        # گرفتن آدرس API لیست محصولات (router basename: 'product')
        self.list_url = reverse('product-list')

    def test_list_only_active_products_and_pagination_format(self):
        """تست عدم نمایش محصولات غیرفعال و بررسی ساختار صفحه‌بندی (Pagination)"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # فقط ۳ محصول فعال باید برگردد (محصول غیرفعال نوکیا نباید باشد)
        self.assertEqual(response.data['count'], 3)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

    def test_filter_by_category(self):
        """تست فیلتر دقیق (Exact Match) محصولات بر اساس یک دسته‌بندی خاص"""
        response = self.client.get(self.list_url, {'category': self.cat_laptop.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_search_filter(self):
        """تست جستجوی متنی (Search) در عنوان محصولات"""
        response = self.client.get(self.list_url, {'search': 'مک‌بوک'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title_fa'], "مک‌بوک پرو M3")

    def test_ordering_by_price_ascending(self):
        """تست مرتب‌سازی صعودی (ارزان‌ترین به گران‌ترین)"""
        response = self.client.get(self.list_url, {'ordering': 'price'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title_fa'], "لپ‌تاپ لنوو گیمینگ")

    def test_ordering_by_price_descending(self):
        """تست مرتب‌سازی نزولی (گران‌ترین به ارزان‌ترین)"""
        response = self.client.get(self.list_url, {'ordering': '-price'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title_fa'], "مک‌بوک پرو M3")

    # =======================================================
    # اضافه شدن تست‌های فیلتر پیشرفته (Advanced Filters)
    # =======================================================

    def test_filter_min_price(self):
        """تست فیلتر حداقل قیمت (نمایش کالاهای گران‌تر از ۵۰ میلیون)"""
        response = self.client.get(self.list_url, {'min_price': '50000000'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # باید آیفون (۵۰ میلیون) و مک‌بوک (۱۲۰ میلیون) رو برگردونه
        self.assertEqual(response.data['count'], 2)

    def test_filter_max_price(self):
        """تست فیلتر حداکثر قیمت (نمایش کالاهای ارزان‌تر از ۵۰ میلیون)"""
        response = self.client.get(self.list_url, {'max_price': '50000000'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # باید آیفون (۵۰ میلیون) و لنوو (۴۰ میلیون) رو برگردونه
        self.assertEqual(response.data['count'], 2)

    def test_filter_price_range(self):
        """تست فیلتر بازه قیمتی (بین ۴۵ تا ۶۰ میلیون)"""
        response = self.client.get(self.list_url, {'min_price': '45000000', 'max_price': '60000000'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # فقط باید آیفون ۱۵ رو برگردونه
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title_fa'], "آیفون 15")

    def test_filter_in_stock_only(self):
        """تست فیلتر کالاهای موجود در انبار"""
        response = self.client.get(self.list_url, {'in_stock': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # مک‌بوک موجودی نداره (۰ هست) پس نباید برگرده. فقط آیفون و لنوو باید باشن
        self.assertEqual(response.data['count'], 2)
        titles = [item['title_fa'] for item in response.data['results']]
        self.assertNotIn("مک‌بوک پرو M3", titles)