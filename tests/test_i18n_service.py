import pytest
from pathlib import Path
from services.i18n_service import I18nService, tr, SUPPORTED_LANGUAGES
from models.profile import UISettings


def test_i18n_supported_languages():
    assert "de" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert "sv" in SUPPORTED_LANGUAGES


def test_i18n_service_translations(tmp_path: Path):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()

    (locales_dir / "de.json").write_text('{"greeting": "Hallo {name}", "only_de": "Nur Deutsch"}', encoding="utf-8")
    (locales_dir / "en.json").write_text('{"greeting": "Hello {name}"}', encoding="utf-8")
    (locales_dir / "sv.json").write_text('{"greeting": "Hej {name}"}', encoding="utf-8")

    service = I18nService(locales_dir=locales_dir)

    # Test German default
    service.current_language = "de"
    assert service.tr("greeting", name="Anna") == "Hallo Anna"
    assert service.tr("only_de") == "Nur Deutsch"

    # Test English
    service.current_language = "en"
    assert service.tr("greeting", name="Anna") == "Hello Anna"
    # Fallback to German for missing key in English
    assert service.tr("only_de") == "Nur Deutsch"

    # Test Swedish
    service.current_language = "sv"
    assert service.tr("greeting", name="Anna") == "Hej Anna"

    # Test missing key in all languages with default parameter
    assert service.tr("non_existent_key", default="Default Text") == "Default Text"


def test_i18n_listener_notification(tmp_path: Path):
    service = I18nService(locales_dir=tmp_path)
    notifications = []

    def on_change(lang):
        notifications.append(lang)

    service.register_listener(on_change)
    service.current_language = "en"
    service.current_language = "sv"

    assert notifications == ["en", "sv"]

    service.unregister_listener(on_change)
    service.current_language = "de"
    assert notifications == ["en", "sv"]  # No new notifications after unregistering


def test_ui_settings_language_serialization():
    settings = UISettings(language="en")
    data = settings.to_dict()
    assert data["language"] == "en"

    restored = UISettings.from_dict(data)
    assert restored.language == "en"

    # Invalid language falls back to 'de'
    invalid = UISettings.from_dict({"language": "invalid_lang"})
    assert invalid.language == "de"
