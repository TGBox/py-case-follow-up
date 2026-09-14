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


REBUILD_HINT = "uv run pyinstaller py-case-follow-up.spec"


def _stale_build_inputs(exe_path: Path, project_root: Path) -> list[str]:
    """Returns the build inputs that are newer than the executable.

    dist/ is gitignored, so the .exe is always a local leftover that nobody
    rebuilds on checkout. An executable predating the spec or the locale files
    cannot possibly contain their current content, and the resulting failure
    says nothing about whether bundling actually works.
    """
    exe_mtime = exe_path.stat().st_mtime
    inputs = [project_root / "py-case-follow-up.spec", *sorted((project_root / "locales").glob("*.json"))]
    return [
        str(p.relative_to(project_root)) for p in inputs if p.exists() and p.stat().st_mtime > exe_mtime
    ]


def test_built_executable_contains_locales() -> None:
    """If a current dist/py-case-follow-up.exe exists, verify all locale files are bundled.

    Skips when there is no build, or when the build predates the spec/locales it
    would have to contain - in both cases there is simply nothing to verify yet.
    A build that IS current but misses a locale is a real packaging bug and fails.
    """
    project_root = Path(__file__).resolve().parent.parent
    exe_path = project_root / "dist" / "py-case-follow-up.exe"
    if not exe_path.exists():
        pytest.skip(f"dist/py-case-follow-up.exe has not been built yet - build it with: {REBUILD_HINT}")

    stale_inputs = _stale_build_inputs(exe_path, project_root)
    if stale_inputs:
        pytest.skip(
            "dist/py-case-follow-up.exe is older than "
            f"{', '.join(stale_inputs)} - it cannot contain their current content. "
            f"Rebuild to make this test meaningful: {REBUILD_HINT}"
        )

    from PyInstaller.archive.readers import CArchiveReader  # type: ignore

    reader = CArchiveReader(str(exe_path))
    locale_entries = [k for k in reader.toc if "locale" in k.lower()]

    # Reaching here means the build is current, so a missing locale is a genuine
    # packaging failure, not a stale artefact - rebuilding will not fix it.
    for lang in ("de", "en", "sv"):
        assert any(f"{lang}.json" in k for k in locale_entries), (
            f"{lang}.json missing from an up-to-date build - check the datas entry in "
            f"py-case-follow-up.spec. Bundled locale entries: {sorted(locale_entries)}"
        )

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
