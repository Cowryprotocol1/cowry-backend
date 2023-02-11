from django.apps import AppConfig

class StablecoinConfig(AppConfig):
    name = 'stablecoin'

    def ready(self):
        from polaris.integrations import register_integrations
        from .integrations import toml_file

        register_integrations(
            toml=toml_file
        )