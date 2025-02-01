"""AppsConfig for gbp-fl"""

from importlib import import_module

from django.apps import AppConfig


class GBPFLConfig(AppConfig):
    """AppConfig for gbp-fl"""

    name = "gbp_fl"
    verbose_name = "File Lists for Gentoo Build Publisher"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        signals = import_module("gbp_fl.signals")
        signals.init()
