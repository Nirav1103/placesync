from django.apps import AppConfig


class PlacementsConfig(AppConfig):
    name = 'placements'

    def ready(self):
        import placements.signals
