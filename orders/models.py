from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User, Address
from products.models import Product
import secrets
import string


def generate_order_number():
    """Generate a unique random order number in format PPGxxxxxxxxxx (12 random alphanumeric chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f'PPG{random_part}'

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('payment_pending', 'Payment Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('wave', 'Wave'),
        ('cod', 'Cash on Delivery'),
    ]

    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod'
    )
    payment_reference = models.CharField(max_length=255, blank=True, db_index=True)
    stock_deducted = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    # Delivery details. Gambian orders use delivery_location; international orders use the address fields.
    shipping_country = models.CharField(max_length=2, default='GM')
    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_phone = models.CharField(max_length=40, blank=True)
    shipping_email = models.EmailField(blank=True)
    delivery_location = models.CharField(max_length=255, blank=True, help_text='Gambian delivery area')
    shipping_address_line1 = models.CharField(max_length=255, blank=True, help_text='Street address')
    shipping_house_number = models.CharField(max_length=50, blank=True, help_text='House / apartment / unit')
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=120, blank=True)
    shipping_region = models.CharField(max_length=120, blank=True, help_text='State / province / region')
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_po_box = models.CharField(max_length=50, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.user.email}'

    @property
    def is_international(self):
        return (self.shipping_country or 'GM').upper() != 'GM'

    def shipping_address_lines(self):
        """The delivery address as display lines."""
        from .countries import country_name

        if not self.is_international:
            return [line for line in (self.shipping_name, self.delivery_location, 'The Gambia') if line]
        street = ' '.join(part for part in (self.shipping_house_number, self.shipping_address_line1) if part)
        city_line = ', '.join(part for part in (self.shipping_city, self.shipping_region, self.shipping_postal_code) if part)
        return [line for line in (
            self.shipping_name,
            street,
            self.shipping_address_line2,
            f'PO Box {self.shipping_po_box}' if self.shipping_po_box else '',
            city_line,
            country_name(self.shipping_country),
        ) if line]

    def save(self, *args, **kwargs):
        # Assign the number before the first insert so the in-memory instance has it too.
        # (Setting it afterwards with a queryset update left a blank number on the instance,
        # which later save() calls wrote back, breaking the unique constraint for the next order.)
        if not self.order_number:
            number = generate_order_number()
            while Order.objects.filter(order_number=number).exists():
                number = generate_order_number()
            self.order_number = number
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart - {self.user.email}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


@receiver(post_save, sender=Order)
def generate_order_number_signal(sender, instance, created, **kwargs):
    """Auto-generate random order number when order is created"""
    if created and not instance.order_number:
        # Generate unique random order number
        order_number = generate_order_number()
        Order.objects.filter(id=instance.id).update(order_number=order_number)
