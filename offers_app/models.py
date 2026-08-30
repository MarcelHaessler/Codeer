from django.contrib.auth.models import User
from django.db import models


class Offer(models.Model):
    """A service package published by a business user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-updated_at']

    def __str__(self):
        """The title is what identifies an offer in the admin list."""
        return self.title


class OfferDetail(models.Model):
    """One pricing tier (basic, standard or premium) of an offer."""

    OFFER_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='details')
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

    class Meta:
        verbose_name = 'Offer detail'
        verbose_name_plural = 'Offer details'
        ordering = ['price']

    def __str__(self):
        """Names the offer too, since tier names repeat across all offers."""
        return f'{self.offer.title} - {self.offer_type}'
