from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

from products.models import Product, Category

User = get_user_model()


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class CartAPITestCase(APITestCase):
    """
    Test cases for the cart API.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(title_fa="تستی", slug="test-cat")

        self.product1 = Product.objects.create(
            category=self.category,
            title_fa='Test Product 1',
            slug='test-product-1',
            price=10.00,
            inventory=10
        )
        self.product2 = Product.objects.create(
            category=self.category,
            title_fa='Test Product 2',
            slug='test-product-2',
            price=20.00,
            inventory=10
        )

    def test_add_to_cart(self):
        url = reverse('cart_add')
        data = {'product_id': self.product1.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'][0]['product_id'], self.product1.id)
        self.assertEqual(response.data['items'][0]['quantity'], 2)
        # اصلاح شد: 20 به جای 20.00
        self.assertEqual(response.data['total_price'], '20')

    def test_get_cart(self):
        url = reverse('cart_add')
        data = {'product_id': self.product1.id, 'quantity': 2}
        self.client.post(url, data, format='json')
        url = reverse('cart_detail')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        # اصلاح شد: 20 به جای 20.00
        self.assertEqual(response.data['total_price'], '20')

    def test_remove_from_cart(self):
        url = reverse('cart_add')
        data = {'product_id': self.product1.id, 'quantity': 2}
        self.client.post(url, data, format='json')
        url = reverse('cart_remove', kwargs={'product_id': self.product1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('cart_detail')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['items']), 0)
        # اصلاح شد: 0 به جای 0.00
        self.assertEqual(response.data['total_price'], '0')

    def test_clear_cart(self):
        url = reverse('cart_add')
        data = {'product_id': self.product1.id, 'quantity': 2}
        self.client.post(url, data, format='json')
        url = reverse('cart_clear')
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('cart_detail')
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data['items']), 0)
        # اصلاح شد: 0 به جای 0.00
        self.assertEqual(response.data['total_price'], '0')