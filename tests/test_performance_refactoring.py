from pathlib import Path

from config import AppConfig
from services.storage_service import StorageService
from services.search_service import parse_search_query
from services.deep_search_service import DeepSearchService
from models.case import Case, CaseCustomer


def test_storage_service_caching_and_update_single(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    c1 = Case(case_id="FALL-001", customer=CaseCustomer(customer_id="C1", practice_name="Praxis A"))
    storage.save_cases([c1])

    # First load populates cache
    loaded1 = storage.load_cases(use_cache=True)
    assert len(loaded1) == 1
    assert loaded1[0].case_id == "FALL-001"

    # Second load uses cache (same instance)
    loaded2 = storage.load_cases(use_cache=True)
    assert loaded1 is loaded2

    # Update single case
    c1.classification.title = "Updated Title"
    storage.update_single_case(c1)

    loaded_after = storage.load_cases(use_cache=True)
    assert len(loaded_after) == 1
    assert loaded_after[0].classification.title == "Updated Title"

    # Verify invalidation
    storage.invalidate_cache()
    fresh_loaded = storage.load_cases(use_cache=True)
    assert fresh_loaded is not loaded2
    assert fresh_loaded[0].classification.title == "Updated Title"


def test_search_query_lru_cache():
    q1 = parse_search_query("vip:true status:open")
    q2 = parse_search_query("vip:true status:open")
    assert q1 is q2


def test_deep_search_file_lines_cache(tmp_path: Path):
    att_dir = tmp_path / "data" / "attachments" / "FALL-001"
    att_dir.mkdir(parents=True)
    test_file = att_dir / "log.txt"
    test_file.write_text("Line 1: Error occurred\nLine 2: Fixed\n", encoding="utf-8")

    deep_svc = DeepSearchService(workspace_dir=tmp_path)
    c = Case(case_id="FALL-001", attachment_directory=str(att_dir))

    res1 = deep_svc.search_case_attachments(c, "Error")
    assert len(res1) == 1
    assert "Line 1" in res1[0]["snippet"]
    assert str(test_file) in deep_svc._file_lines_cache

    # Second search hits cache
    res2 = deep_svc.search_case_attachments(c, "Error")
    assert len(res2) == 1

    # Modify file mtime/content
    test_file.write_text("Line 1: No issue\nLine 2: Critical Error\n", encoding="utf-8")
    res3 = deep_svc.search_case_attachments(c, "Critical")
    assert len(res3) == 1
    assert "Line 2" in res3[0]["snippet"]


# --- Ansichtswechsel: die alte Ansicht bleibt stehen, bis die neue fertig ist ---
#
# Gemeldet: beim Umschalten ins Kanban-Board flackern die Bedienelemente oben,
# Beschriftungen liegen uebereinander, Spalten erscheinen als graue Bloecke.
# Ursache: die alte Ansicht wurde zuerst ausgeblendet, danach wurde die neue
# gebaut und gefuellt - mehrere hundert Millisekunden, in denen die App nicht
# zur Ereignisschleife zurueckkehrt und das Fenster halb gezeichnet dasteht.
# Gemessen (erster Wechsel ins Board): ohne sichtbare Ansicht 166 ms -> 1,5 ms.

def test_the_previous_view_stays_visible_until_the_new_one_is_filled(tmp_path: Path):
    from enums import LayoutMode, get_layout_display
    from services.seed_service import SeedService
    from ui.app import SupportCockpitApp

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    SeedService(storage).run_seed(force=True)

    app = SupportCockpitApp(config)
    try:
        app.update()
        ablauf: list[str] = []

        board = app._get_view(LayoutMode.BOARD.value)
        orig_set_cases = board.set_cases
        orig_forget = app.active_view.pack_forget

        def set_cases_spy(*args, **kwargs):
            ablauf.append("board gefuellt")
            return orig_set_cases(*args, **kwargs)

        def forget_spy(*args, **kwargs):
            ablauf.append("alte Ansicht ausgeblendet")
            return orig_forget(*args, **kwargs)

        board.set_cases = set_cases_spy
        app.active_view.pack_forget = forget_spy

        app.switch_layout(get_layout_display(LayoutMode.BOARD.value))
        app.update()

        assert "board gefuellt" in ablauf, "die neue Ansicht wurde nie befuellt"
        assert "alte Ansicht ausgeblendet" in ablauf, "die alte Ansicht blieb stehen"
        assert ablauf.index("board gefuellt") < ablauf.index("alte Ansicht ausgeblendet"), (
            f"Reihenfolge falsch: {ablauf} - der Inhaltsbereich ist waehrend des Aufbaus leer"
        )
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_switching_to_the_active_layout_does_not_hide_it(tmp_path: Path):
    """Sonst blinkt die Ansicht, wenn man das schon gewaehlte Layout erneut waehlt."""
    from enums import get_layout_display
    from ui.app import SupportCockpitApp

    config = AppConfig(workspace_dir=tmp_path)
    StorageService(config).save_profile(StorageService(config).load_profile())

    app = SupportCockpitApp(config)
    try:
        app.update()
        ausgeblendet: list[str] = []
        orig_forget = app.active_view.pack_forget
        app.active_view.pack_forget = lambda *a, **k: (ausgeblendet.append("x"), orig_forget(*a, **k))[1]

        app.switch_layout(get_layout_display(app._active_layout))
        app.update()

        assert ausgeblendet == [], "die bereits sichtbare Ansicht wurde ausgeblendet"
    finally:
        try:
            app.destroy()
        except Exception:
            pass
