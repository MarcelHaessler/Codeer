from django.apps import AppConfig


class BaseInfoAppConfig(AppConfig):
    """Aggregated platform statistics. Has no models of its own."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base_info_app'
