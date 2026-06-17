from decimal import Decimal
from django.conf import settings
from products.models import Product


class Cart:
    """
    A class to manage the shopping cart using Redis / Sessions.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            # قیمت را حتماً به صورت String ذخیره می‌کنیم تا در JSON به مشکل نخورد
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        # ساخت یک دیکشنری سریع برای پیدا کردن محصولات
        product_map = {str(product.id): product for product in products}

        for product_id, item_data in self.cart.items():
            # 🔥 جادوی حل ارور: ساخت یک کپی جدید از دیتای آیتم تا سشن اصلی دستکاری نشود
            if product_id in product_map:
                item = item_data.copy()
                item['product_id'] = int(product_id)
                item['product'] = product_map[product_id]
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()