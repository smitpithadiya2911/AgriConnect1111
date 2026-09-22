from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order
from django.utils import timezone

@receiver(pre_save, sender=Order)
def capture_and_log_order_status(sender, instance, **kwargs):
    if hasattr(instance, 'status_history'):
        if instance.pk:
            try:
                old_order = Order.objects.get(pk=instance.pk)
                if old_order.status != instance.status:
                    entry = {
                        "status": instance.status,
                        "notes": f"Status updated from {old_order.status} to {instance.status}.",
                        "timestamp": timezone.now().isoformat()
                    }
                    if not isinstance(instance.status_history, list):
                        instance.status_history = []
                    instance.status_history.append(entry)
            except Order.DoesNotExist:
                pass
        else:
            entry = {
                "status": instance.status,
                "notes": "Order placed.",
                "timestamp": timezone.now().isoformat()
            }
            if not isinstance(instance.status_history, list):
                instance.status_history = []
            instance.status_history.append(entry)
