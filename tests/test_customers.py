import pytest
from pathlib import Path
from models.customer import Customer, Contact
from services.customer_service import CustomerService
from services.storage_service import StorageService, AppConfig


def test_customer_model_to_and_from_dict():
    c = Customer(
        customer_id="K-99999",
        practice_name="Zahnarztpraxis Dr. Weiss",
        is_vip=True,
        system_version="v4.2.1",
        general_notes="Besondere Anforderungen an PVS-Export",
        contacts=[Contact(name="Fr. Schmidt", role="Empfang", phone="089-123456")],
    )

    c_dict = c.to_dict()
    assert c_dict["customer_id"] == "K-99999"
    assert c_dict["is_vip"] is True
    assert len(c_dict["contacts"]) == 1
    assert c_dict["contacts"][0]["name"] == "Fr. Schmidt"

    restored = Customer.from_dict(c_dict)
    assert restored.customer_id == "K-99999"
    assert restored.practice_name == "Zahnarztpraxis Dr. Weiss"
    assert restored.is_vip is True
    assert restored.contacts[0].phone == "089-123456"


def test_customer_service_crud_operations(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    service = CustomerService(storage)

    # 1. Save new customers
    c1 = Customer(customer_id="K-101", practice_name="Praxis A", is_vip=False)
    c2 = Customer(customer_id="K-102", practice_name="Praxis B (VIP)", is_vip=True)

    service.save_customer(c1)
    service.save_customer(c2)

    # 2. Get customer by ID
    found1 = service.get_customer_by_id("K-101")
    assert found1 is not None
    assert found1.practice_name == "Praxis A"

    found2 = service.get_customer_by_id("K-102")
    assert found2 is not None
    assert found2.is_vip is True

    # 3. Search customers
    search_res = service.search_customers("VIP")
    assert len(search_res) == 1
    assert search_res[0].customer_id == "K-102"

    # 4. Update customer
    c1.practice_name = "Praxis A (Umbenannt)"
    service.save_customer(c1)
    updated = service.get_customer_by_id("K-101")
    assert updated is not None
    assert updated.practice_name == "Praxis A (Umbenannt)"

    # 5. Delete customer via storage
    current = storage.load_customers()
    remaining = [c for c in current if c.customer_id != "K-101"]
    storage.save_customers(remaining)

    deleted = service.get_customer_by_id("K-101")
    assert deleted is None
