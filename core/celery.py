import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# ---------------------------------------------------------
# ⏰ تنظیمات Celery Beat برای اجرای خودکار تسک‌ها
# ---------------------------------------------------------
app.conf.beat_schedule = {
    'cancel-unpaid-orders-every-5-minutes': {
        'task': 'orders.tasks.cancel_unpaid_orders',
        # هر ۵ دقیقه این تسک اجرا می‌شود تا دیتابیس را اسکن کند
        'schedule': crontab(minute='*/5'),
    },
}