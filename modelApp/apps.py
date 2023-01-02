from django.apps import AppConfig


class ModelappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modelApp'
    def ready(self):
        from events import updater
        updater.start()