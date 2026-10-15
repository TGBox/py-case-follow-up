"""P2P sync with colleagues: timestamp comparison, diff, reading peer files, import, and the diff dialog."""

import json
from pathlib import Path

import pytest

from models.case import Case, CaseCustomer, Classification
from models.profile import Colleague
from services.p2p_sync_service import P2PSyncService


def _colleague_with_cases(tmp_path: Path, content: str) -> Colleague:
    share = tmp_path / "colleague_share"
    share.mkdir(exist_ok=True)
    (share / "cases.json").write_text(content, encoding="utf-8")
    return Colleague(username="aschmidt", name="Anna Schmidt", cases_path=str(share / "cases.json"))


@pytest.mark.parametrize(
    ("remote", "local", "expected"),
    [
        ("2026-08-23T12:00:00", "2026-08-23T10:00:00", "REMOTE_NEWER"),
        ("2026-08-23T10:00:00", "2026-08-23T12:00:00", "LOCAL_NEWER"),
        # Same instant, different spelling -> IDENTICAL
        ("2026-08-23T10:00:00", "2026-08-23T10:00:00.000000", "IDENTICAL"),
        ("2026-08-23T10:00:00+02:00", "2026-08-23T08:00:00+00:00", "IDENTICAL"),
        # Offsets decide, not string order
        ("2026-08-23T10:00:00+02:00", "2026-08-23T09:30:00+00:00", "LOCAL_NEWER"),
        # Missing or unparseable values: remote gets reviewed
        ("", "2026-08-23T10:00:00", "REMOTE_NEWER"),
        ("2026-08-23T10:00:00", "", "REMOTE_NEWER"),
        ("kaputt", "2026-08-23T10:00:00", "REMOTE_NEWER"),
    ],
)
def test_compare_timestamps(remote: str, local: str, expected: str):
    """Regression: diff status was decided by string order instead of the actual instant."""
    assert P2PSyncService._compare_timestamps(remote, local) == expected


def _valid(case_id: str, updated_at: str, title: str = "Fall", **kw) -> Case:
    return Case(case_id=case_id, updated_at=updated_at,
                customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Sync"),
                classification=Classification(schema_id="schema_standard", title=title), **kw)


def test_read_diff_and_import_colleague_cases(storage, tmp_path: Path):
    storage.save_cases([
        _valid("T-100", "2026-08-23T10:00:00", "Alt"),
        _valid("T-200", "2026-08-23T14:00:00"),
        _valid("T-300", "2026-08-23T12:00:00"),
    ])
    remote = [
        _valid("T-100", "2026-08-23T12:00:00", "Neu von Kollegin", created_by="Colleague"),
        _valid("T-200", "2026-08-23T10:00:00"),
        _valid("T-300", "2026-08-23T12:00:00"),
        _valid("T-400", "2026-08-23T15:00:00", created_by="Colleague"),
        Case(case_id="T-INVALID"),  # fails validation -> skipped
    ]
    colleague = _colleague_with_cases(tmp_path, json.dumps([c.to_dict() for c in remote]))
    p2p = P2PSyncService(storage)

    ok, _msg, read = p2p.read_colleague_cases(colleague)
    assert ok is True
    assert {item.case_id: item.status for item in p2p.compute_diff(read)} == {
        "T-100": "REMOTE_NEWER", "T-200": "LOCAL_NEWER", "T-300": "IDENTICAL", "T-400": "NEW",
    }

    assert p2p.import_selected_cases([read[0], read[3]]) == 2
    local = {c.case_id: c for c in storage.load_cases()}
    assert set(local) == {"T-100", "T-200", "T-300", "T-400"}
    assert local["T-100"].updated_at == "2026-08-23T12:00:00"
    assert local["T-100"].classification.title == "Neu von Kollegin"
    assert local["T-400"].created_by == "Colleague"


def test_corrupted_colleague_file_reads_as_empty(storage, tmp_path: Path):
    colleague = _colleague_with_cases(tmp_path, "CORRUPTED_JSON_CONTENT")
    ok, _msg, remote = P2PSyncService(storage).read_colleague_cases(colleague)
    assert ok is True  # safe_read_json renames the corrupted file and returns []
    assert remote == []


def test_p2p_diff_dialog_imports_selected(root, storage, tmp_path: Path):
    from ui.dialogs.p2p_diff_dialog import P2PDiffDialog

    remote = Case(
        case_id="T-P2P-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis P2P"),
        classification=Classification(schema_id="schema_standard", title="P2P Fall"),
        updated_at="2026-08-25T12:00:00",
    )
    colleague = _colleague_with_cases(tmp_path, json.dumps([remote.to_dict()]))
    synced: list[bool] = []
    dialog = P2PDiffDialog(root, colleagues=[colleague], p2p_service=P2PSyncService(storage),
                           on_sync_completed=lambda: synced.append(True))
    dialog.update_idletasks()
    assert [d.case_id for d in dialog.diff_items] == ["T-P2P-01"]

    dialog.on_import_selected()
    assert synced == [True]
    assert [c.case_id for c in storage.load_cases()] == ["T-P2P-01"]
    dialog.destroy()
