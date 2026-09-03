import json
from pathlib import Path
from typing import Any, Callable

SUPPORTED_LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "sv": "Svenska",
}

LANGUAGE_DISPLAY_TO_CODE = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
LANGUAGE_CODE_TO_DISPLAY = dict(SUPPORTED_LANGUAGES)


class I18nService:
    """Central translation service for managing multi-language strings."""

    def __init__(self, locales_dir: Path | str | None = None) -> None:
        if locales_dir is None:
            # Default: project_root/locales
            self.locales_dir = Path(__file__).resolve().parent.parent.parent / "locales"
        else:
            self.locales_dir = Path(locales_dir)

        self._current_language: str = "de"
        self._translations: dict[str, dict[str, Any]] = {}
        self._listeners: list[Callable[[str], None]] = []

        self.load_all_translations()

    def load_all_translations(self) -> None:
        """Load all translation JSON files from locales_dir."""
        self._translations.clear()
        if not self.locales_dir.exists():
            self.locales_dir.mkdir(parents=True, exist_ok=True)

        for lang_code in SUPPORTED_LANGUAGES:
            file_path = self.locales_dir / f"{lang_code}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang_code] = json.load(f)
                except Exception:
                    self._translations[lang_code] = {}
            else:
                self._translations[lang_code] = {}

    @property
    def current_language(self) -> str:
        return self._current_language

    @current_language.setter
    def current_language(self, lang_code: str) -> None:
        if lang_code in SUPPORTED_LANGUAGES and lang_code != self._current_language:
            self._current_language = lang_code
            self._notify_listeners()

    def register_listener(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def clear_listeners(self) -> None:
        self._listeners.clear()

    def _notify_listeners(self) -> None:
        for callback in self._listeners:
            try:
                callback(self._current_language)
            except Exception:
                pass

    def tr(self, key: str, default: Any = None, **kwargs: Any) -> Any:
        """Translate a dot-separated key (e.g., 'menu.master_data').

        Fallback chain: current_language -> 'de' -> default -> key.
        """
        result = self._get_nested_val(self._translations.get(self._current_language, {}), key)
        if result is None and self._current_language != "de":
            result = self._get_nested_val(self._translations.get("de", {}), key)

        if result is None:
            if default is not None:
                result = default
            else:
                result = key

        if kwargs and isinstance(result, str):
            try:
                return result.format(**kwargs)
            except Exception:
                return result
        return str(result) if isinstance(result, str) else result

    def _get_nested_val(self, data: dict[str, Any], key: str) -> Any:
        keys = key.split(".")
        curr = data
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return None
        return curr


# Global singleton instance
_i18n_instance: I18nService | None = None
_SENTINEL = object()


def get_i18n() -> I18nService:
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nService()
    return _i18n_instance


def tr(key: str, default: Any = None, **kwargs: Any) -> Any:
    return get_i18n().tr(key, default=default, **kwargs)


class LocalizedDict(dict):
    """Dictionary proxy that dynamically translates keys using I18nService."""

    def __init__(self, prefix: str, initial_dict: dict[str, str] | None = None, **kwargs: Any) -> None:
        if initial_dict:
            super().__init__(initial_dict, **kwargs)
        else:
            super().__init__(**kwargs)
        self._prefix = prefix

    def __getitem__(self, key: str) -> str:
        default = super().get(key, str(key))
        try:
            res = tr(f"{self._prefix}.{key}", default=_SENTINEL)
            if res is _SENTINEL and isinstance(key, str):
                alt_key = key.lower() if key.isupper() else key.upper()
                res = tr(f"{self._prefix}.{alt_key}", default=_SENTINEL)
            if res is _SENTINEL:
                return default
            return res
        except Exception:
            return default

    def get(self, key: str, default: Any = None) -> Any:
        try:
            fallback = super().get(key, default)
            res = tr(f"{self._prefix}.{key}", default=_SENTINEL)
            if res is _SENTINEL and isinstance(key, str):
                alt_key = key.lower() if key.isupper() else key.upper()
                res = tr(f"{self._prefix}.{alt_key}", default=_SENTINEL)
            if res is _SENTINEL:
                return fallback
            return res
        except Exception:
            return super().get(key, default)

    def values(self) -> list[str]:
        return [self[k] for k in self.keys()]

    def items(self) -> list[tuple[str, str]]:
        return [(k, self[k]) for k in self.keys()]

