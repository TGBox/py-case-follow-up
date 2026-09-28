"""Regression tests for P2P diff status classification by updated_at."""

import pytest

from services.p2p_sync_service import P2PSyncService


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
    assert P2PSyncService._compare_timestamps(remote, local) == expected
