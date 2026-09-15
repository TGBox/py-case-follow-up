"""Ein Absturz beim Start muss im Crash-Log stehen.

Der Tk-Fehlerbericht faengt nur Callbacks im laufenden Programm ab. Faellt der
Aufbau des Hauptfensters um, greift er nicht - und in der gepackten .exe ist
stdout None, die Meldung verschwindet also ersatzlos. Fuer den Nutzer sieht das
aus wie "die App startet einfach nicht", ohne eine einzige Spur zum Nachsehen.
"""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = str(Path(__file__).resolve().parent.parent)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _main_modul():
    return importlib.import_module("main")


def test_a_crash_while_building_the_window_lands_in_the_crash_log(tmp_path, monkeypatch):
    main_mod = _main_modul()

    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(tmp_path)])

    import ui.app as app_modul

    def _knallt(*args, **kwargs):
        raise RuntimeError("Fensteraufbau fehlgeschlagen (Testfall)")

    monkeypatch.setattr(app_modul, "SupportCockpitApp", _knallt)

    with pytest.raises(SystemExit) as beendet:
        main_mod.main()

    assert beendet.value.code == 1

    log = tmp_path / "logs" / "tkinter_error.log"
    assert log.exists(), "kein Crash-Log geschrieben - der Absturz waere spurlos"
    inhalt = log.read_text(encoding="utf-8")
    assert "Fensteraufbau fehlgeschlagen (Testfall)" in inhalt
    assert "RuntimeError" in inhalt


def test_the_log_goes_to_the_workspace_that_was_actually_used(tmp_path, monkeypatch):
    """Mit --workspace muss das Log dort liegen, nicht im Standardordner."""
    main_mod = _main_modul()
    arbeitsordner = tmp_path / "ablage"
    arbeitsordner.mkdir()

    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(arbeitsordner)])

    import ui.app as app_modul
    monkeypatch.setattr(app_modul, "SupportCockpitApp", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("Boom")))

    with pytest.raises(SystemExit):
        main_mod.main()

    assert (arbeitsordner / "logs" / "tkinter_error.log").exists()
