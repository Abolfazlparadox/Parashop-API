# استفاده از نسخه کامل پایتون به جای slim تا تمام ابزارهای لینوکسی برای نصب پکیج‌ها وجود داشته باشه
FROM python:3.11

# تنظیم متغیرهای محیطی برای عملکرد بهتر پایتون در داکر
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ساخت پوشه کاری
WORKDIR /app

# آپدیت کردن pip به آخرین نسخه قبل از هر کاری
RUN pip install --upgrade pip

# کپی کردن لیست نیازمندی‌ها
COPY requirements.txt .

# نصب پکیج‌ها
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کل کدهای پروژه
COPY . .