from django.contrib.auth.models import User
from django.db import models


class Order(models.Model):
    """A booked offer tier, stored as a snapshot of the tier at booking time."""

    STATUS_CHOICES = [
        ('in_progress', 'In progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders_as_customer'
    )
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders_as_business'
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        """Includes the status, the field most often checked in the admin."""
        return f'{self.title} ({self.status})'
