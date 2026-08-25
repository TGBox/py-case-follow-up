"""Tests for Colleague model absence tracking, holiday reasons, and serialization."""

import pytest
from models.profile import Colleague


def test_colleague_absence_fields():
    """Verify Colleague model tracks is_absent and absence_reason correctly through serialization."""
    col = Colleague(
        username="mmueller",
        name="Max Müller",
        department="Support",
        is_absent=True,
        absence_reason="Urlaub bis 30.08.",
    )
    col_dict = col.to_dict()
    assert col_dict["is_absent"] is True
    assert col_dict["absence_reason"] == "Urlaub bis 30.08."

    loaded_col = Colleague.from_dict(col_dict)
    assert loaded_col.is_absent is True
    assert loaded_col.absence_reason == "Urlaub bis 30.08."
