from django.apps import AppConfig

class SuiviProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'suivi_production'

    # CETTE FONCTION EST LA CLÉ DE LA SOLUTION
    def ready(self):
        """
        Cette méthode est appelée par Django lorsque l'application est chargée.
        En important les signaux ici, on s'assure qu'ils sont connectés.
        """
        import suivi_production.models  # Ceci importe les signaux définis dans models.py