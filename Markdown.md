# 🏗️ Parashop API - Project Context Document

## 1. Architecture Overview
The project is a robust, production-ready E-commerce REST API built with Django and Django REST Framework (DRF). It leverages a distributed architecture using Docker.

| Component | Technology / Library |
| :--- | :--- |
| **Framework** | Django 5.2+, DRF 3.17+ |
| **Database** | PostgreSQL |
| **Caching & Broker** | Redis (Alpine) |
| **Async Tasks** | Celery & Celery Beat |
| **Authentication** | JWT (`djangorestframework-simplejwt`) |
| **Admin Panel** | `django-unfold` (Custom Neon Blue Theme) |
| **API Docs** | `drf-spectacular` (Swagger UI & ReDoc) |

## 2. Application Structure
The monolith is modularized into distinct business domains:
* **core:** Main configuration, ASGI/WSGI entry points, URL routing, and Celery setup.
* **users:** Custom user model, authentication, profile management, addresses, and OTP logic.
* **products:** Bilingual product catalog (Category, Product), inventory, and advanced filtering.
* **cart:** Redis-backed shopping cart logic, totally isolated from PostgreSQL until checkout.
* **orders:** Order lifecycle, coupons, ZarinPal payment gateway, and asynchronous state management.

## 3. Database Schema (Models)
| App | Model | Relationships & Key Fields |
| :--- | :--- | :--- |
| **users** | `User` | Extends `AbstractUser`. Fields: `phone_number`, `is_customer`, `is_vendor`, `is_phone_verified`. |
| **users** | `UserProfile` | `OneToOne(User)`. Fields: `avatar`, `national_code`, `birth_date`, `gender`. |
| **users** | `UserAddress` | `ForeignKey(User)`. Fields: `province`, `city`, `postal_address`, `is_default`. |
| **products** | `Category` | `ForeignKey('self')` for nested hierarchies. Fields: `title_fa`, `title_en`, `slug`. |
| **products** | `Product` | `ForeignKey(Category)`. Fields: `title_fa/en`, `price`, `inventory`, `is_active`. |
| **orders** | `Coupon` | Fields: `code`, `valid_from`, `valid_to`, `discount` (0-100), `active`. |
| **orders** | `Order` | `ForeignKey(User, Address, Coupon)`. Fields: `status`, `total_paid`, `discount_amount`. |
| **orders** | `OrderItem` | `ForeignKey(Order, Product)`. Fields: `price`, `quantity`. |
| **orders** | `Payment` | `ForeignKey(Order)`. Fields: `amount`, `authority`, `ref_id`, `status`. |

## 4. API Endpoints & Routers
| Domain | Route | Methods | Auth Required |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/v1/auth/login/`, `/api/v1/auth/refresh/` | POST | No |
| **Users** | `/api/v1/users/register/`, `/logout/` | POST | Varies |
| **Users** | `/api/v1/users/password/forgot/`, `/reset/` | POST | No |
| **Profile** | `/api/v1/users/profile/`, `/password/change/` | GET, PATCH, PUT | Yes |
| **Addresses**| `/api/v1/users/addresses/` | GET, POST, PUT, DEL | Yes |
| **Products** | `/api/v1/products/categories/`, `/list/` | GET | No |
| **Cart** | `/api/v1/cart/`, `/add/`, `/clear/`, `/remove/<id>/` | GET, POST, DEL | Yes |
| **Orders** | `/api/v1/orders/` | GET, POST | Yes |
| **Payments** | `/api/v1/orders/<id>/pay/`, `/payment/verify/` | POST | Varies |
| **Coupons** | `/api/v1/orders/<id>/apply_coupon/` | POST | Yes |

## 5. Business Logic & Services
* **Idempotency & Concurrency:** High-risk views (payment verification, coupon application, order cancellation) are strictly wrapped in `with transaction.atomic():` and utilize `select_for_update()` to prevent database race conditions.
* **ZarinPal Integration (`ZarinPalService`):** Isolated service handling Sandbox v4 API requests. Automatically converts Toman to Rial and manages network timeouts.
* **Redis Cart:** The `Cart` class manages sessions efficiently, converting product properties to strings in Redis and mapping them back to QuerySet objects during iteration.
* **Celery Beat (`cancel_unpaid_orders`):** Runs every 5 minutes. Queries `pending` orders older than 15 minutes, restores the `Product.inventory`, and marks the order as `canceled`.
* **Filtering (`DjangoFilterBackend`):** Advanced catalog filtering supporting minimum/maximum price limits, textual search, and `in_stock` boolean checks.

## 6. Critical Configurations (`settings.py`)
* **Custom User:** `AUTH_USER_MODEL = 'users.User'`
* **Throttling:** 5 requests/min for anonymous users, 60 requests/min for authenticated users.
* **JWT Config:** Access token expires in 60 minutes, Refresh in 1 day. Custom claims inject `username`, `phone_number`, and `is_customer` into the token payload.
* **Cache:** `django_redis.cache.RedisCache` pointing to `redis://redis:6379/1`.
* **Celery Broker:** `redis://redis:6379/0`.