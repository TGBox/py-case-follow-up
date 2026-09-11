from services.i18n_service import I18nService
import json
import sys
from pathlib import Path
import pytest



def test_i18n_locales_dir_when_frozen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that I18nService correctly discovers locales in sys._MEIPASS when frozen."""
    fake_meipass = tmp_path / "mei_bundle"
    bundled_locales = fake_meipass / "locales"
    bundled_locales.mkdir(parents=True)

    de_content = {"common": {"ok": "OK_DE", "cancel": "Abbrechen"}}
    en_content = {"common": {"ok": "OK_EN", "cancel": "Cancel"}}
    sv_content = {"common": {"ok": "OK_SV", "cancel": "Avbryt"}}

    (bundled_locales / "de.json").write_text(json.dumps(de_content), encoding="utf-8")
    (bundled_locales / "en.json").write_text(json.dumps(en_content), encoding="utf-8")
    (bundled_locales / "sv.json").write_text(json.dumps(sv_content), encoding="utf-8")

    # Simulate PyInstaller frozen environment
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(fake_meipass), raising=False)

    service = I18nService(locales_dir=None)
    assert service.locales_dir == bundled_locales
    assert service.tr("common.ok") == "OK_DE"

    # Test language switching in frozen environment
    service.current_language = "en"
    assert service.tr("common.ok") == "OK_EN"
    assert service.tr("common.cancel") == "Cancel"

    service.current_language = "sv"
    assert service.tr("common.ok") == "OK_SV"
    assert service.tr("common.cancel") == "Avbryt"

    service.current_language = "de"
    assert service.tr("common.ok") == "OK_DE"


def test_i18n_locales_dir_fallback_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that I18nService falls back to project root locales in normal source mode."""
    # Ensure not frozen
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    if hasattr(sys, "_MEIPASS"):
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    service = I18nService(locales_dir=None)
    # Locales dir should point to project root locales/
    expected_root_locales = Path(__file__).resolve().parent.parent / "locales"
    assert service.locales_dir == expected_root_locales
    assert (service.locales_dir / "de.json").exists()
    assert (service.locales_dir / "en.json").exists()
    assert (service.locales_dir / "sv.json").exists()


def test_spec_file_includes_locales() -> None:
    """Validate that py-case-follow-up.spec includes ('locales', 'locales')."""
    spec_path = Path(__file__).resolve().parent.parent / "py-case-follow-up.spec"
    assert spec_path.exists(), "py-case-follow-up.spec must exist"

    spec_content = spec_path.read_text(encoding="utf-8")
    assert "('locales', 'locales')" in spec_content or '("locales", "locales")' in spec_content


def test_built_executable_contains_locales() -> None:
    """If dist/py-case-follow-up.exe has been built, verify all locale files are bundled."""
    exe_path = Path(__file__).resolve().parent.parent / "dist" / "py-case-follow-up.exe"
    if not exe_path.exists():
        pytest.skip("dist/py-case-follow-up.exe has not been built yet")

    from PyInstaller.archive.readers import CArchiveReader  # type: ignore

    reader = CArchiveReader(str(exe_path))
    locale_entries = [k for k in reader.toc if "locale" in k.lower()]
    assert any("de.json" in k for k in locale_entries), "de.json must be in bundle"
    assert any("en.json" in k for k in locale_entries), "en.json must be in bundle"
    assert any("sv.json" in k for k in locale_entries), "sv.json must be in bundle"

    # Verify content extraction and translation differentiation
    translations = {}
    for k in locale_entries:
        if k.endswith(".json"):
            lang = Path(k).stem
            content = json.loads(reader.extract(k).decode("utf-8"))
            translations[lang] = content

    assert translations["de"]["common"]["save"] == "Speichern"
    assert translations["en"]["common"]["save"] == "Save"
    assert translations["sv"]["common"]["save"] == "Spara"
