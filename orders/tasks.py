from celery import shared_task
from .models import Order
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_order_confirmation_email(order_id):
    """
    Asynchronously sends an order confirmation email to the user.
    """
    try:
        order = Order.objects.get(id=order_id)
        print(f"Sending email for order {order.id} to {order.user.email}...")
        # In a real-world scenario, you would use Django's mail functions here
        # from django.core.mail import send_mail
        # send_mail(
        #     f"Your Parashop Order #{order.id} is confirmed!",
        #     "Thank you for your purchase. We are processing your order.",
        #     "no-reply@parashop.com",
        #     [order.user.email],
        #     fail_silently=False,
        # )
        print("Email sent successfully (simulation).")
    except Order.DoesNotExist:
        print(f"Error: Order with ID {order_id} does not exist.")

@shared_task
def cancel_unpaid_orders():
    """
    پیدا کردن سفارش‌های پرداخت‌نشده بعد از ۱۵ دقیقه،
    لغو آن‌ها و برگرداندن موجودی به انبار.
    """
    # زمان 15 دقیقه پیش رو محاسبه می‌کنیم
    time_threshold = timezone.now() - timedelta(minutes=15)

    # کوئری: سفارشاتی که وضعیتشون pending هست و قبل از 15 دقیقه پیش ساخته شدن
    unpaid_orders = Order.objects.filter(status='pending', created_at__lte=time_threshold)

    if not unpaid_orders.exists():
        return "هیچ سفارش پرداخت‌نشده‌ای یافت نشد."

    canceled_count = 0
    for order in unpaid_orders:
        try:
            with transaction.atomic():
                # دوباره رکورد رو قفل می‌کنیم تا مطمئن شیم دقیقاً تو همین میلی‌ثانیه کاربر در حال پرداخت نباشه
                locked_order = Order.objects.select_for_update().get(id=order.id)

                if locked_order.status == 'pending':
                    # ۱. برگرداندن موجودی به انبار
                    for item in locked_order.items.all():
                        product = item.product
                        product.inventory += item.quantity
                        product.save()

                    # ۲. تغییر وضعیت سفارش
                    locked_order.status = 'canceled'
                    locked_order.save()
                    canceled_count += 1
                    logger.info(f"Order {locked_order.id} was canceled due to timeout. Inventory restored.")

        except Exception as e:
            logger.error(f"Error canceling order {order.id}: {str(e)}")

    return f"{canceled_count} سفارش لغو و موجودی‌ها برگردانده شد."