from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# ایمپورت کردن ویوهای spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ------------------------------------------------
    # 📖 API Documentation (Swagger & ReDoc)
    # ------------------------------------------------
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'), # این خود فایل نقشه است (JSON/YAML)
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # محیط گرافیکی
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'), # محیط گرافیکی جایگزین

    # ------------------------------------------------
    # 🔐 Authentication APIs
    # ------------------------------------------------
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ------------------------------------------------
    # 👤 Users App APIs
    # ------------------------------------------------
    path('api/v1/users/', include('users.urls')),
]