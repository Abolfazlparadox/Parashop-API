from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem, UserAddress
from .serializers import OrderSerializer, CreateOrderSerializer
from cart.cart import Cart
from .tasks import send_order_confirmation_email


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        cart = Cart(request)
        if len(cart) == 0:
            return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address_id = serializer.validated_data['address_id']
        address = UserAddress.objects.get(id=address_id)

        order = Order.objects.create(user=request.user, address=address)
        total_paid = 0

        for item in cart:
            order_item = OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )
            total_paid += order_item.get_cost()

        order.total_paid = total_paid
        order.save()

        # Trigger the asynchronous task
        send_order_confirmation_email.delay(order.id)

        cart.clear()

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
