from django.apps import AppConfig


class OrdersAppConfig(AppConfig):
    """Booked offer tiers plus the two order count endpoints."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders_app'
