from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypedDict

from django.conf import settings
from django.core.signals import setting_changed
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.settings import perform_import


class UnderscoreizeSettings(TypedDict, total=False):
    no_underscore_before_number: bool
    ignore_fields: list[str] | None
    ignore_keys: list[str] | None


class SettingsDict(TypedDict, total=False):
    RENDERER_CLASS: str
    PARSER_CLASS: str
    JSON_UNDERSCOREIZE: UnderscoreizeSettings


# USER_SETTINGS: SettingsDict = getattr(settings, "JSON_CAMEL_CASE", {})

DEFAULTS: SettingsDict = {
    "RENDERER_CLASS": "rest_framework.renderers.JSONRenderer",
    "PARSER_CLASS": "rest_framework.parsers.JSONParser",
    "JSON_UNDERSCOREIZE": {"no_underscore_before_number": False, "ignore_fields": None, "ignore_keys": None},
}

# List of settings that may be in string import notation.
IMPORT_STRINGS: Iterable[str] = ("RENDERER_CLASS", "PARSER_CLASS")


class APISettings:
    """
    A settings object that allows DRF Dromedary settings to be accessed as
    properties. For example:

        from drf_dromedary.settings import api_settings
        print(api_settings.DEFAULT_RENDERER_CLASSES)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.

    Note:
    This is an internal class that is only compatible with settings namespaced
    under the JSON_CAMEL_CASE name. It is not intended to be used by 3rd-party
    apps, and test helpers like `override_settings` may not work as expected.

    This class is originally from Django REST Framework but has been adjusted for
    this project.
    """

    RENDERER_CLASS: type[JSONRenderer]
    PARSER_CLASS: type[JSONParser]
    JSON_UNDERSCOREIZE: UnderscoreizeSettings

    def __init__(
        self,
        user_settings: SettingsDict | None = None,
        defaults: SettingsDict | None = None,
        import_strings: Iterable[str] | None = None,
    ):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs: set[str] = set()

    @property
    def user_settings(self) -> SettingsDict:
        if not hasattr(self, "_user_settings"):
            try:
                self._user_settings = settings.JSON_CAMEL_CASE
            except AttributeError:
                self._user_settings = {}
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '{attr}'")

        try:
            # Check if present in user settings
            val = self.user_settings[attr]  # type: ignore [literal-required]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]  # type: ignore [literal-required]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


api_settings = APISettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_settings(*args: Any, **kwargs: Any) -> None:
    setting = kwargs["setting"]
    if setting == "JSON_CAMEL_CASE":
        api_settings.reload()


setting_changed.connect(reload_settings)
