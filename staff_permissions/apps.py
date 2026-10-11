from django.apps import AppConfig

class StaffPermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'staff_permissions'

    def ready(self):
        import staff_permissions.signals
