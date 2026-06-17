from django.urls import path
from .views import CartView, CartClearView

urlpatterns = [
    path('', CartView.as_view(), name='cart_detail'),
    path('add/', CartView.as_view(), name='cart_add'),
    path('remove/<int:product_id>/', CartView.as_view(), name='cart_remove'),
    path('clear/', CartClearView.as_view(), name='cart_clear'),
]
