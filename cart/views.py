from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .cart import Cart
from .serializers import AddCartItemSerializer, CartSerializer
from products.models import Product


class CartView(APIView):
    """
    API view for the shopping cart.
    """

    def get(self, request, format=None):
        """
        Return the current cart.
        """
        cart = Cart(request)
        serializer = CartSerializer({'items': cart, 'total_price': cart.get_total_price()})
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Add an item to the cart.
        """
        cart = Cart(request)
        serializer = AddCartItemSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            update = serializer.validated_data['update']
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            cart.add(product=product, quantity=quantity, override_quantity=update)
            return Response(CartSerializer({'items': cart, 'total_price': cart.get_total_price()}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id, format=None):
        """
        Remove an item from the cart.
        """
        cart = Cart(request)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart.remove(product)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartClearView(APIView):
    """
    API view to clear the cart.
    """

    def delete(self, request, format=None):
        """
        Clear the cart.
        """
        cart = Cart(request)
        cart.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
