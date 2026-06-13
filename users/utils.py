import random
import logging

logger = logging.getLogger(__name__)


class SMSService:
    @staticmethod
    def generate_otp():
        """تولید یک کد ۶ رقمی تصادفی"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_otp(phone_number, code):
        """
        شبیه‌ساز ارسال پیامک
        در آینده کدهای اتصال به کاوه‌نگار، ملی‌پیامک یا قاصدک اینجا قرار می‌گیرد
        """
        # چاپ در کنسول برای اینکه خودت موقع تست بتونی کد رو ببینی
        print(f"\n{'=' * 40}")
        print(f"🚀 [MOCK SMS] Sending OTP to {phone_number}")
        print(f"🔑 Your Verification Code is: {code}")
        print(f"{'=' * 40}\n")

        # ثبت در لاگ سیستم
        logger.info(f"OTP sent to {phone_number}")
        return True