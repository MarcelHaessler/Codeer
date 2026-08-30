from django.apps import AppConfig


class ReviewsAppConfig(AppConfig):
    """Ratings that customers give to business users."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews_app'
