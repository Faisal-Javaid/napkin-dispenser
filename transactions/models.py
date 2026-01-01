from django.db import models
import uuid
from django.db.models import F

class Transaction(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='transactions')
    dispenser = models.ForeignKey('dispensers.Dispenser', on_delete=models.CASCADE, related_name='transactions')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='transactions')
    row_number = models.IntegerField()
    credits_used = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.user.phone_number} - {self.product.product_name} - {self.status}'
    
    @classmethod
    def create_transaction(cls, user, dispenser, product, row_number, status=Status.SUCCESS):
        """Create transaction with proper inventory and wallet updates"""
        from dispensers.models import DispenserProduct
        from users.models import Wallet
        
        with models.transaction.atomic():
            # Create transaction record
            transaction = cls.objects.create(
                user=user,
                dispenser=dispenser,
                product=product,
                row_number=row_number,
                credits_used=product.credit_cost,
                status=status
            )
            
            if status == cls.Status.SUCCESS:
                # Update dispenser inventory
                dispenser_product = DispenserProduct.objects.select_for_update().get(
                    dispenser=dispenser,
                    row_number=row_number,
                    product=product
                )
                dispenser_product.current_inventory = F('current_inventory') - 1
                dispenser_product.save()
                
                # Update user wallet
                wallet = Wallet.objects.select_for_update().get(user=user)
                wallet.balance = F('balance') - product.credit_cost
                wallet.save()
            
            return transaction