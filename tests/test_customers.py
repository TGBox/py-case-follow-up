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
        website="https://zahnarzt-weiss.de",
        vm_number=104,
        instance_number=2,
        general_notes="Besondere Anforderungen an PVS-Export",
        contacts=[
            Contact(name="Fr. Schmidt", role="Empfang", phone="089-123456"),
            Contact(name="Dr. Weiss", role="Inhaber", email="weiss@zahnarzt.de")
        ],
    )

    c_dict = c.to_dict()
    assert c_dict["customer_id"] == "K-99999"
    assert c_dict["is_vip"] is True
    assert c_dict["website"] == "https://zahnarzt-weiss.de"
    assert c_dict["vm_number"] == 104
    assert c_dict["instance_number"] == 2
    assert len(c_dict["contacts"]) == 2
    assert c_dict["contacts"][0]["name"] == "Fr. Schmidt"
    assert c_dict["contacts"][1]["role"] == "Inhaber"

    restored = Customer.from_dict(c_dict)
    assert restored.customer_id == "K-99999"
    assert restored.practice_name == "Zahnarztpraxis Dr. Weiss"
    assert restored.is_vip is True
    assert restored.website == "https://zahnarzt-weiss.de"
    assert restored.vm_number == 104
    assert restored.instance_number == 2
    assert len(restored.contacts) == 2
    assert restored.contacts[0].phone == "089-123456"
    assert restored.contacts[1].email == "weiss@zahnarzt.de"


def test_customer_service_crud_operations(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    service = CustomerService(storage)

    # 1. Save new customers with website, vm_number, instance_number & multiple contacts
    c1 = Customer(
        customer_id="K-101",
        practice_name="Praxis A",
        website="https://praxis-a.de",
        vm_number=101,
        instance_number=1,
        is_vip=False,
        contacts=[Contact(name="Dr. A", role="Arzt")]
    )
    c2 = Customer(
        customer_id="K-102",
        practice_name="Praxis B (VIP)",
        is_vip=True,
        website="https://praxis-b.com",
        vm_number=102,
        instance_number=3,
        contacts=[
            Contact(name="Dr. B", role="Leitung", email="b@praxis.de"),
            Contact(name="Fr. C", role="Abrechnung", email="c@praxis.de")
        ]
    )

    service.save_customer(c1)
    service.save_customer(c2)

    # 2. Get customer by ID
    found1 = service.get_customer_by_id("K-101")
    assert found1 is not None
    assert found1.practice_name == "Praxis A"
    assert found1.website == "https://praxis-a.de"

    found2 = service.get_customer_by_id("K-102")
    assert found2 is not None
    assert found2.is_vip is True
    assert len(found2.contacts) == 2

    # 3. Search customers by website and contact role/email
    search_res_vip = service.search_customers("VIP")
    assert len(search_res_vip) == 1
    assert search_res_vip[0].customer_id == "K-102"

    search_res_web = service.search_customers("praxis-a.de")
    assert len(search_res_web) == 1
    assert search_res_web[0].customer_id == "K-101"

    search_res_contact = service.search_customers("Abrechnung")
    assert len(search_res_contact) == 1
    assert search_res_contact[0].customer_id == "K-102"

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
