    from rest_framework.test import APITestCase
    from rest_framework import status
    from django.contrib.auth import get_user_model
    from django.test import override_settings
    from rest_framework_simplejwt.tokens import RefreshToken
    
    from users.models import UserAddress
    from products.models import Product, Category
    from orders.models import Order, OrderItem
    
    User = get_user_model()
    
    
    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
    )
    class CheckoutIntegrationTestCase(APITestCase):
        """
        End-to-End Test for the Checkout Flow.
        """
    
        def setUp(self):
            # 1. Create a User
            self.user = User.objects.create_user(username='test_buyer', password='password123', phone_number='09120000000')
            
            # Authenticate using JWT directly (bypassing login API)
            refresh = RefreshToken.for_user(self.user)
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
            # 2. Create UserAddress using the EXACT schema fields from users.models.UserAddress
            self.address = UserAddress.objects.create(
                user=self.user,
                title="خانه",
                receiver_name="John Doe",
                receiver_phone="09121111111",
                province="تهران",
                city="تهران",
                postal_address="خیابان تست، کوچه تست، پلاک ۱",
                postal_code="1234567890"
            )
    
            # 3. Create Category
            self.category = Category.objects.create(
                title_fa="موبایل",
                slug="mobile-phones"
            )
    
            # 4. Create Product using the EXACT schema fields from products.models.Product
            self.product = Product.objects.create(
                category=self.category,
                title_fa="گوشی تستی",
                slug="test-phone",
                price=15000000,  # 15,000,000 Toman (decimal_places=0)
                inventory=10
            )
    
        def test_complete_checkout_flow(self):
            """
            Simulates adding an item to the cart and successfully checking out.
            """
            # Step 1: Add product to cart
            cart_add_url = '/api/v1/cart/add/'
            cart_payload = {
                'product_id': self.product.id,
                'quantity': 2
            }
            response = self.client.post(cart_add_url, cart_payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
            # Step 2: Verify Cart content
            cart_url = '/api/v1/cart/'
            response = self.client.get(cart_url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['items']), 1)
            self.assertEqual(float(response.data['total_price']), 30000000.0) # 2 * 15,000,000
    
            # Step 3: Proceed to Checkout (Create Order)
            checkout_url = '/api/v1/orders/'
            checkout_payload = {
                'address_id': self.address.id
            }
            response = self.client.post(checkout_url, checkout_payload, format='json')
            
            # Verify successful order creation
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(float(response.data['total_paid']), 30000000.0)
            self.assertEqual(len(response.data['items']), 1)
            
            # Verify the database state
            self.assertEqual(Order.objects.count(), 1)
            self.assertEqual(OrderItem.objects.count(), 1)
            
            order = Order.objects.first()
            self.assertEqual(order.user, self.user)
            self.assertEqual(order.address, self.address)
            self.assertEqual(order.total_paid, 30000000)
            
            # Step 4: Verify Cart is empty after checkout
            response = self.client.get(cart_url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['items']), 0)
            self.assertEqual(float(response.data['total_price']), 0.0)
