import pytest
from unittest.mock import MagicMock
from models.customer import Customer
from utils.ui_utils import enable_textbox_cursor_autoscroll


def sort_customers_helper(customers: list[Customer], criterion: str, asc: bool = True, parent_cases: list | None = None) -> list[Customer]:
    res = list(customers)
    reverse = not asc

    def get_last_contact(customer: Customer) -> str:
        if not parent_cases:
            return ""
        customer_cases = [c for c in parent_cases if hasattr(c, "customer") and getattr(c.customer, "customer_id", "") == customer.customer_id]
        if not customer_cases:
            return ""
        latest_ts = ""
        for c in customer_cases:
            ts = getattr(c, "updated_at", "") or getattr(c, "created_at", "")
            if ts > latest_ts:
                latest_ts = ts
            for t in getattr(c, "timeline", []):
                if getattr(t, "timestamp", "") > latest_ts:
                    latest_ts = t.timestamp
        return latest_ts

    if "ID" in criterion or "nummer" in criterion:
        res.sort(key=lambda c: c.customer_id.lower(), reverse=reverse)
    elif "Kontakt" in criterion:
        res.sort(key=get_last_contact, reverse=reverse)
    else:
        res.sort(key=lambda c: c.practice_name.lower(), reverse=reverse)

    return res


def test_customer_sorting_logic():
    c1 = Customer(customer_id="C-003", practice_name="Zahnarzt Praxis Z")
    c2 = Customer(customer_id="C-001", practice_name="Ergotherapie A")
    c3 = Customer(customer_id="C-002", practice_name="Physio B")

    # Name A-Z asc
    sorted_name = sort_customers_helper([c1, c2, c3], "Name (A-Z)", asc=True)
    assert [c.practice_name for c in sorted_name] == ["Ergotherapie A", "Physio B", "Zahnarzt Praxis Z"]

    # ID asc
    sorted_id = sort_customers_helper([c1, c2, c3], "Praxisnummer / ID", asc=True)
    assert [c.customer_id for c in sorted_id] == ["C-001", "C-002", "C-003"]

    # ID desc
    sorted_id_desc = sort_customers_helper([c1, c2, c3], "Praxisnummer / ID", asc=False)
    assert [c.customer_id for c in sorted_id_desc] == ["C-003", "C-002", "C-001"]


def test_autoscroll_helper_binding():
    mock_textbox = MagicMock()
    inner_text = MagicMock()
    mock_textbox._textbox = inner_text

    enable_textbox_cursor_autoscroll(mock_textbox)

    assert inner_text.bind.call_count == 3
