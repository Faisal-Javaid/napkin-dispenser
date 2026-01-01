from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Dispenser, DispenserProduct

@receiver(post_save, sender=Dispenser)
def create_dispenser_rows(sender, instance, created, **kwargs):
    """Create 4 empty rows when a new dispenser is created"""
    if created:
        for row_number in range(1, 5):
            DispenserProduct.objects.create(
                dispenser=instance,
                row_number=row_number,
                current_inventory=0,
                max_capacity=0
            )