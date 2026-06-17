from rest_framework import serializers

class AddCartItemSerializer(serializers.Serializer):
    """
    Serializer for adding items to the cart.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    update = serializers.BooleanField(required=False, default=False)


class CartItemSerializer(serializers.Serializer):
    """
    Serializer for cart items.
    """
    product_id = serializers.IntegerField()
    # استخراج عنوان فارسی محصول برای نمایش در سبد خرید فرانت‌اند
    title = serializers.CharField(source='product.title_fa', read_only=True)
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=0)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0)


class CartSerializer(serializers.Serializer):
    """
    Serializer for the entire cart.
    """
    items = CartItemSerializer(many=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0)