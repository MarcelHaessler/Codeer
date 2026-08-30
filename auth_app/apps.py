from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Registration and login. Has no models of its own."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
