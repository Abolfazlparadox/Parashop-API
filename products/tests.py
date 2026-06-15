from django.test import TestCase
from django.db.models import ProtectedError
from .models import Category, Product


class ProductCatalogModelTests(TestCase):

    def setUp(self):
        # ۱. ساخت دسته اصلی (پدر)
        self.parent_category = Category.objects.create(
            title_fa="الکترونیک",
            title_en="Electronics",
            slug="electronics"
        )

        # ۲. ساخت دسته فرعی (فرزند)
        self.child_category = Category.objects.create(
            parent=self.parent_category,
            title_fa="لپ‌تاپ",
            title_en="Laptops",
            slug="laptops"
        )

        # ۳. ساخت یک محصول و اتصال آن به دسته فرزند
        self.product = Product.objects.create(
            category=self.child_category,
            title_fa="مک‌بوک پرو",
            title_en="MacBook Pro",
            slug="macbook-pro",
            description_fa="لپ‌تاپ قدرتمند و حرفه‌ای",
            price=150000000,  # ۱۵۰ میلیون تومان
            inventory=10
        )

    def test_category_creation_and_hierarchy(self):
        """تست ساخته شدن دسته‌ها و بررسی رابطه پدر-فرزندی (Nested)"""
        self.assertEqual(Category.objects.count(), 2)
        # بررسی اینکه آیا فرزند به درستی در لیست فرزندانِ پدر قرار گرفته یا نه
        self.assertEqual(self.parent_category.children.count(), 1)
        self.assertEqual(self.parent_category.children.first(), self.child_category)

    def test_category_str_representation(self):
        """تست خروجی متنی دسته‌ها برای نمایش در پنل ادمین"""
        self.assertEqual(str(self.parent_category), "الکترونیک")
        # دسته فرزند باید اسم مادرش رو هم نشون بده
        self.assertEqual(str(self.child_category), "الکترونیک > لپ‌تاپ")

    def test_product_creation_and_relations(self):
        """تست ساخته شدن محصول و ارتباط صحیح آن با جدول دسته‌بندی"""
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.category, self.child_category)
        self.assertEqual(str(self.product), "مک‌بوک پرو")

    def test_category_protect_delete_constraint(self):
        """
        تست حیاتی دیتابیس:
        نباید بشه دسته‌ای رو که توش محصول وجود داره پاک کرد (جلوگیری از یتیم شدن محصولات)
        """
        with self.assertRaises(ProtectedError):
            self.child_category.delete()

    def test_parent_category_cascade_delete(self):
        """تست حذف زنجیره‌ای (CASCADE): اگر دسته پدر حذف شود، دسته فرزند هم حذف می‌شود؟"""
        # دقت کن که روی دسته پدر هیچ محصولی مستقیم ثبت نشده، پس ارور پروتکت نمی‌خوریم
        # اما برای تست کردن باید موقتاً محصول رو پاک کنیم که به خاطر فرزندش ارور نده
        self.product.delete()
        self.parent_category.delete()
        # وقتی پدر پاک شد، فرزندش (لپ‌تاپ) هم باید خودکار از دیتابیس پاک شده باشه
        self.assertEqual(Category.objects.count(), 0)