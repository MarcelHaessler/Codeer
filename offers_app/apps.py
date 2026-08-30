from django.apps import AppConfig


class OffersAppConfig(AppConfig):
    """Offers and the three pricing tiers that belong to each of them."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'offers_app'
