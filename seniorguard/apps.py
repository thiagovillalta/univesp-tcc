from django.apps import AppConfig
from django.db.models.signals import post_migrate

class seniorguardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seniorguard'

    def ready(self):
        from .signals import create_sensor_type
        post_migrate.connect(create_sensor_type, sender=self)
