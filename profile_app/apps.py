from django.apps import AppConfig


class ProfileAppConfig(AppConfig):
    """Profiles that extend the built-in user with marketplace data."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile_app'
