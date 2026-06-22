from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Order, OrderItem, UserAddress, Payment, Coupon  # 👈 Coupon اضافه شد
from .serializers import OrderSerializer, CreateOrderSerializer
from cart.cart import Cart
from .tasks import send_order_confirmation_email
from .services.zarinpal import ZarinPalService
from django.utils import timezone

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # این کوئری‌ست تضمین می‌کند که هر کاربر فقط سفارشات خودش را می‌بیند
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        cart = Cart(request)
        if len(cart) == 0:
            return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        address_id = serializer.validated_data['address_id']
        address = UserAddress.objects.get(id=address_id)

        order = Order.objects.create(user=request.user, address=address)
        total_paid = 0

        for item in cart:
            order_item = OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )
            total_paid += order_item.get_cost()

        order.total_paid = total_paid
        order.save()

        # Trigger the asynchronous task

        cart.clear()

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # -----------------------------------------------------------------
    # 💳 API درخواست پرداخت (مسیر خودکار: POST /api/v1/orders/{id}/pay/)
    # -----------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        # متد self.get_object() به صورت امن سفارش کاربر را پیدا می‌کند
        # اگر سفارش مال این کاربر نباشد، خودکار ارور 404 می‌دهد
        order = self.get_object()

        # لایه امنیتی: جلوگیری از پرداخت مجدد
        if order.status != 'pending':
            return Response(
                {"error": "این سفارش قابل پرداخت نیست (وضعیت نامعتبر)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ایجاد یک رکورد حسابداری برای این تلاش
        payment = Payment.objects.create(
            order=order,
            amount=order.total_paid,
        )

        # ارسال به سرویس زرین‌پال
        zarinpal = ZarinPalService()
        desc = f"پرداخت سفارش شماره {order.id}"

        result = zarinpal.send_request(
            amount=int(payment.amount),
            description=desc,
            mobile=request.user.phone_number
        )

        if result['success']:
            payment.authority = result['authority']
            payment.save()
            return Response({"payment_url": result['payment_url']}, status=status.HTTP_200_OK)
        else:
            payment.status = 'failed'
            payment.save()
            return Response({"error": result['error']}, status=status.HTTP_400_BAD_REQUEST)

    # -----------------------------------------------------------------
    # 🎁 API اعمال کد تخفیف (مسیر خودکار: POST /api/v1/orders/{id}/apply_coupon/)
    # -----------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='apply_coupon')
    def apply_coupon(self, request, pk=None):
        order = self.get_object()

        # لایه امنیتی ۱: فقط سفارشات پرداخت‌نشده قابلیت تخفیف دارند
        if order.status != 'pending':
            return Response(
                {"error": "فقط روی سفارشات در انتظار پرداخت می‌توان کد تخفیف اعمال کرد."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # لایه امنیتی ۲: جلوگیری از اعمال چندباره تخفیف روی یک سفارش
        if order.coupon:
            return Response(
                {"error": "یک کد تخفیف قبلاً روی این سفارش اعمال شده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = request.data.get('code')
        if not code:
            return Response({"error": "لطفاً کد تخفیف را ارسال کنید."}, status=status.HTTP_400_BAD_REQUEST)

        # جستجوی کوپن
        try:
            coupon = Coupon.objects.get(code__iexact=code)  # iexact یعنی به بزرگی و کوچکی حروف حساس نباشد
        except Coupon.DoesNotExist:
            return Response({"error": "کد تخفیف نامعتبر است."}, status=status.HTTP_404_NOT_FOUND)

        # بررسی اعتبار (تاریخ و وضعیت)
        if not coupon.is_valid():
            return Response({"error": "این کد تخفیف منقضی یا غیرفعال شده است."}, status=status.HTTP_400_BAD_REQUEST)

        # محاسبه و اعمال تخفیف
        with transaction.atomic():
            # قفل کردن رکورد سفارش برای جلوگیری از باگ‌های همزمانی
            order = Order.objects.select_for_update().get(id=order.id)

            # محاسبه مبلغ تخفیف (مثلاً 20 درصدِ 100 هزار تومان میشه 20 هزار تومان)
            discount_amount = (order.total_paid * coupon.discount) / Decimal('100')

            order.coupon = coupon
            order.discount_amount = discount_amount
            order.total_paid -= discount_amount  # کسر تخفیف از مبلغ نهایی قابل پرداخت
            order.save()

        return Response({
            "message": "کد تخفیف با موفقیت اعمال شد.",
            "discount_applied": discount_amount,
            "new_total": order.total_paid
        }, status=status.HTTP_200_OK)
    # -----------------------------------------------------------------
    # 🔄 API تایید پرداخت (مسیر خودکار: POST /api/v1/orders/payment/verify/)
    # -----------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='payment/verify', permission_classes=[AllowAny])
    def verify_payment(self, request):
        authority = request.data.get('Authority')
        payment_status = request.data.get('Status')

        if not authority:
            return Response({"error": "شناسه Authority ارسال نشده است."}, status=status.HTTP_400_BAD_REQUEST)

        payment = get_object_or_404(Payment, authority=authority)

        # Idempotency: جلوگیری از اجرای دوبار تایید برای یک تراکنش
        if payment.status != 'pending':
            return Response({"error": "این تراکنش قبلاً تعیین تکلیف شده است."}, status=status.HTTP_400_BAD_REQUEST)

        # اگر کاربر در درگاه دکمه "انصراف" را زده باشد
        if payment_status != 'OK':
            payment.status = 'failed'
            payment.save()
            return Response({"error": "پرداخت لغو شد یا ناموفق بود."}, status=status.HTTP_400_BAD_REQUEST)

        zarinpal = ZarinPalService()
        result = zarinpal.verify_payment(amount=int(payment.amount), authority=authority)

        if result['success']:
            # قفل کردن ردیف دیتابیس برای جلوگیری از Race Condition
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=payment.order.id)

                payment.status = 'success'
                payment.ref_id = result['ref_id']
                payment.save()

                order.status = 'processing'
                order.save()
            send_order_confirmation_email.delay(order.id)
            return Response({
                "message": result['message'],
                "ref_id": result['ref_id'],
                "order_id": order.id
            }, status=status.HTTP_200_OK)

        else:
            payment.status = 'failed'
            payment.save()
            return Response({"error": result['error']}, status=status.HTTP_400_BAD_REQUEST)