from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'list', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]