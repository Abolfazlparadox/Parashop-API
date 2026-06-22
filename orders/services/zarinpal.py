import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ZarinPalService:
    """
    سرویس ارتباط با درگاه پرداخت زرین‌پال (نسخه 4)
    مستندات: https://docs.zarinpal.com/
    """

    # برای تست، از محیط Sandbox (شبیه‌ساز) زرین‌پال استفاده می‌کنیم
    # اگر مرچنت کد واقعی داشتی، پیشوند sandbox. رو از این آدرس‌ها پاک کن
    ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"

    def __init__(self):
        # این مرچنت کد تستی زرین‌پال است (36 کاراکتر). بعداً از settings می‌خونیم
        self.merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', "00000000-0000-0000-0000-000000000000")
        # آدرسی که کاربر بعد از پرداخت باید به اونجا برگرده
        self.callback_url = getattr(settings, 'ZARINPAL_CALLBACK_URL',
                                    "http://localhost:8000/api/v1/orders/payment/verify/")

    def send_request(self, amount: int, description: str, email: str = None, mobile: str = None):
        """
        ارسال درخواست به زرین‌پال برای گرفتن Authority (شناسه پرداخت)
        توجه: واحد پول در API نسخه 4 زرین‌پال، ریال است! پس تومان را به ریال تبدیل می‌کنیم.
        """
        amount_rial = amount * 10  # تبدیل تومان به ریال

        req_data = {
            "merchant_id": self.merchant_id,
            "amount": amount_rial,
            "callback_url": self.callback_url,
            "description": description,
            "metadata": {
                "mobile": mobile,
                "email": email
            }
        }
        req_header = {"accept": "application/json", "content-type": "application/json'"}

        try:
            response = requests.post(
                url=self.ZP_API_REQUEST,
                data=json.dumps(req_data),
                headers=req_header,
                timeout=10  # ست کردن تایم‌اوت برای جلوگیری از قفل شدن سرور ما اگر زرین‌پال قطع بود
            )
            data = response.json()

            if len(data['errors']) == 0:
                authority = data['data']['authority']
                return {
                    "success": True,
                    "authority": authority,
                    "payment_url": f"{self.ZP_API_STARTPAY}{authority}"
                }
            else:
                logger.error(f"ZarinPal Request Error: {data['errors']}")
                return {"success": False, "error": data['errors']['message']}

        except requests.exceptions.Timeout:
            logger.error("ZarinPal Request Timeout")
            return {"success": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            logger.error("ZarinPal Connection Error")
            return {"success": False, "error": "Connection Error"}

    def verify_payment(self, amount: int, authority: str):
        """
        تایید نهایی پرداخت (Verify) بعد از بازگشت کاربر از بانک
        """
        amount_rial = amount * 10

        req_data = {
            "merchant_id": self.merchant_id,
            "amount": amount_rial,
            "authority": authority
        }
        req_header = {"accept": "application/json", "content-type": "application/json'"}

        try:
            response = requests.post(
                url=self.ZP_API_VERIFY,
                data=json.dumps(req_data),
                headers=req_header,
                timeout=10
            )
            data = response.json()

            if len(data['errors']) == 0:
                # کد 100 یعنی پرداخت موفق، 101 یعنی پرداخت قبلاً تایید شده
                if data['data']['code'] == 100:
                    return {
                        "success": True,
                        "ref_id": data['data']['ref_id'],
                        "message": "پرداخت با موفقیت انجام شد."
                    }
                elif data['data']['code'] == 101:
                    return {
                        "success": True,
                        "ref_id": data['data']['ref_id'],
                        "message": "این تراکنش قبلاً با موفقیت تایید شده است."
                    }
                else:
                    return {"success": False, "error": data['data']['message']}
            else:
                logger.error(f"ZarinPal Verify Error: {data['errors']}")
                return {"success": False, "error": data['errors']['message']}

        except Exception as e:
            logger.error(f"ZarinPal Verify Exception: {str(e)}")
            return {"success": False, "error": "Internal Server Error"}