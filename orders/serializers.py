from rest_framework import serializers
from .models import Order, OrderItem
from users.models import UserAddress


class CreateOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()

    def validate_address_id(self, value):
        user = self.context['request'].user
        try:
            address = UserAddress.objects.get(id=value, user=user)
        except UserAddress.DoesNotExist:
            raise serializers.ValidationError("Invalid address ID.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title_fa', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_title', 'price', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'address', 'total_paid', 'status', 'created_at',
            'coupon', 'discount_amount',  # 👈 این دو تا اضافه شدن
            'items'
        ]
        read_only_fields = ('user', 'status', 'total_paid', 'created_at')
