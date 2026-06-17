### 🌟 معرفی پروژه Parashop-API

ساخت `Parashop-API` با این سطح از استانداردها، مهارت‌های مهندسی نرم‌افزار شما را به شدت ارتقا داده و رزومه‌تان را برای هر مصاحبه‌ای (به‌ویژه با نیازمندی‌های توسعه مدرن بک‌اند) به یک گزینه بی‌رقیب تبدیل می‌کند. توسعه این پروژه از صفر، با رعایت اصول Clean Code و Clean Architecture، و کامیت‌های مرحله‌به‌مرحله پیش خواهد رفت.

> 💡 **نکته معماری:** در دنیای واقعی، توسعه یک پروژه از روز اول با معماری میکروسرویس خالص معمولاً باعث پیچیدگی بی‌دلیل (Over-engineering) می‌شود. رویکرد ما در این پروژه: هسته اصلی فروشگاه (Core E-commerce) به صورت **Monolith ماژولار** با Django و DRF نوشته می‌شود. سپس برای بخش‌هایی مانند سیستم پیشنهادگر (AI)، یک **میکروسرویس مجزا با FastAPI و SQLAlchemy** پیاده‌سازی می‌کنیم. این استراتژی، تسلط هم‌زمان بر جنگو، معماری میکروسرویس و نیازمندی‌های بازار کار (FastAPI) را تضمین می‌کند.

---

### 🗺️ نقشه راه توسعه (Roadmap)

* **فاز ۰ (راه‌اندازی):** ایجاد محیط ایزوله با `uv`، ساختاردهی در PyCharm، و کانفیگ اولیه PostgreSQL و Git.
* **فاز ۱ (احراز هویت):** طراحی Custom User Model و پیاده‌سازی JWT (JSON Web Tokens) با دسترسی‌های نقش‌محور.
* **فاز ۲ (کاتالوگ چندزبانه):** طراحی مدل‌های محصول، پیاده‌سازی ساختار دو زبانه (i18n) در دیتابیس و توسعه RESTful APIs.
* **فاز ۳ (سفارشات):** استفاده از Redis برای مدیریت بهینه سبد خرید و طراحی دیتابیس تراکنشی برای ثبت سفارشات.
* **فاز ۴ (میکروسرویس AI):** ساخت سرویس مجزا با FastAPI و SQLAlchemy و برقراری ارتباط با هسته جنگو.
* **فاز ۵ (بهینه‌سازی):** نوشتن Unit Test، دیباگینگ و بهینه‌سازی کوئری‌های دیتابیس (جلوگیری از مشکل N+1).
* **فاز ۶ (دیپلوی):** داکرایز کردن پروژه با `Dockerfile` و `docker-compose.yml` و راه‌اندازی روی سرور مجازی (VPS).

---

### 🚀 دستورات اجرا شده (فاز صفر و یک)

تمام دستوراتی که تا این مرحله برای راه‌اندازی محیط، دیتابیس، و گیت در PowerShell (با دسترسی Administrator) اجرا شده‌اند:

```powershell
# ۱. ساخت پوشه پروژه و محیط مجازی با uv
mkdir Parashop-API
cd Parashop-API
uv venv
.\.venv\Scripts\Activate.ps1

# ۲. نصب نیازمندی‌های پایه
uv pip install django djangorestframework psycopg2-binary python-dotenv

# ۳. ساخت هسته جنگو و فایل‌های ایگنور
django-admin startproject core .
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo "db.sqlite3" >> .gitignore

# ۴. راه‌اندازی گیت و اولین کامیت
git init
git add .
git commit -m "chore: initial project setup with uv and django"

# ۵. ایجاد برنچ توسعه و فایل گزارش کار
git checkout -b feature/database-and-auth
New-Item -ItemType File -Name "DEV_LOG.md"

```

---

### 📝 محتوای فایل گزارش کار (DEV_LOG.md)

محتوای زیر را می‌توانید مستقیماً داخل فایل `DEV_LOG.md` خود کپی کنید تا روند توسعه ثبت بماند:

```markdown
# 📝 دفترچه گزارش کار و روند توسعه Parashop-API

## 👤 سیستم کاربران (Custom User Model)
- ارث‌بری از `AbstractUser` برای انعطاف‌پذیری در آینده.
- اضافه شدن فیلدهای `phone_number` و `is_customer`.
- رجیستر کردن مدل در `admin.py`.
- اجرای موفقیت‌آمیز اولین `makemigrations` و `migrate` روی PostgreSQL.

## 🔐 سیستم احراز هویت (Authentication)
- نصب پکیج `djangorestframework-simplejwt`.
- کانفیگ `REST_FRAMEWORK` برای استفاده از `JWTAuthentication` به عنوان پیش‌فرض.
- تنظیم زمان انقضای `ACCESS_TOKEN` (۶۰ دقیقه) و `REFRESH_TOKEN` (۱ روز).
- ایجاد Endpoint های لاگین و رفرش توکن در مسیر `api/v1/auth/`.

```
## 🚀 توسعه API ثبت‌نام (Registration)
- ساخت `RegisterSerializer` با هندل کردن هشینگ پسورد از طریق `create_user`.
- استفاده از `CreateAPIView` برای حفظ ساختار Clean Code.
- تنظیم `AllowAny` برای باز بودن دسترسی فرم ثبت‌نام.
- ساخت Endpoint ثبت‌نام در مسیر `api/v1/users/register/`.`

## 🧩 شخصی‌سازی توکن‌ها (Custom JWT Claims)
- ساخت `CustomTokenObtainPairSerializer` برای اضافه کردن اطلاعات اختصاصی کاربر به Payload توکن.
- جلوگیری از درخواست‌های اضافی به سرور با تزریق فیلدهای `username`, `phone_number` و `is_customer` درون توکن.
- جایگزینی View پیش‌فرض با `CustomTokenObtainPairView` در روتر اصلی.

## 💎 ارتقای معماری مدل کاربر (Production-Ready User Models)
- تفکیک زیرساخت احراز هویت از اطلاعات شخصی با تعریف مدل `UserProfile` (رابطه OneToOne).
- پیاده‌سازی سیستم چندآدرسه پیشرفته با مدل `UserAddress` (رابطه ForeignKey).
- اضافه شدن فهرست نقش‌ها (`is_vendor`, `is_customer`) و فیلدهای راستی‌آزمایی (`is_phone_verified`).
- راه‌اندازی مکانیزم Django Signals برای ساخت خودکار ردیف پروفایل بلافاصله پس از ثبت‌نام کاربر.

## 🎛️ تکمیل پنل کاربری (Dashboard APIs)
- ساخت API پروفایل (`UserProfileView`) با قابلیت ادغام و آپدیت هم‌زمان جدول `User` و `UserProfile`.
- پیاده‌سازی API تغییر رمز عبور امن (`ChangePasswordView`) با تایید رمز قبلی.
- پیاده‌سازی کامل CRUD برای آدرس‌ها با استفاده از `ModelViewSet` و ایزوله کردن نمایش آدرس‌ها برای هر کاربر.

## 🎨 شخصی‌سازی پنل مدیریت (Django Unfold)
- ادغام پکیج `django-unfold` برای ارتقای رابط کاربری ادمین جنگو به استانداردهای مدرن.
- تنظیم پالت رنگی Dark Matte Steel با افکت‌های Neon Blue (`#00f0ff`).
- پیاده‌سازی سیستم Inline Models برای ویرایش هم‌زمان پروفایل و آدرس در صفحه کاربر (`CustomUserAdmin`).
- ساخت منوی میانبر سایدبار برای دسترسی سریع به Swagger، Frontend و GitHub.

## 🛒 APIهای کاتالوگ محصولات و بهینه‌سازی دیتابیس
- ساخت سریالایزرهای `CategorySerializer` و `ProductSerializer` با خروجی دوزبانه.
- پیاده‌سازی `ReadOnlyModelViewSet` برای نمایش عمومی محصولات.
- حل قطعی مشکل N+1 Problem در کوئری محصولات با استفاده از `select_related('category')` برای بهینه‌سازی سرعت پاسخگویی.

## 🔎 سیستم جستجو، فیلتر و صفحه‌بندی (Search & Pagination)
- نصب `django-filter` و کانفیگ گلوبال `PageNumberPagination` (سایز ۱۲ آیتم در هر صفحه).
- پیاده‌سازی `DjangoFilterBackend` برای فیلتر دقیق بر اساس دسته‌بندی محصولات.
- راه‌اندازی `SearchFilter` برای جستجوی متنی در عنوان و توضیحات محصولات.
- اضافه کردن `OrderingFilter` جهت مرتب‌سازی بر اساس قیمت و تاریخ ثبت.

## 🛒 Phase 3: Redis-Backed Shopping Cart
- نصب `django-redis` و کانفیگ `CACHES` برای استفاده از Redis به عنوان بک‌اند.
- ساخت اپ `cart` و اضافه کردن آن به `INSTALLED_APPS`.
- پیاده‌سازی `Cart` class در `cart/cart.py` برای مدیریت منطق سبد خرید.
- ساخت `AddCartItemSerializer` و `CartSerializer` برای اعتبارسنجی و نمایش داده‌های سبد خرید.
- پیاده‌سازی `CartView` و `CartClearView` برای مدیریت APIهای سبد خرید.
- ساخت `cart/urls.py` و اضافه کردن آن به `core/urls.py`.
- نوشتن تست‌های جامع برای APIهای سبد خرید در `cart/tests.py`.
