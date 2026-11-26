from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Rojgar Setu Core Engine (P2P)'

    def ready(self):
        pass
