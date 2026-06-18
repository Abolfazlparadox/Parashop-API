from celery import shared_task
from .models import Order


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
