"""Customer model round-trip and CustomerService lookup, search, update and removal."""

from models.customer import Contact, Customer
from services.customer_service import CustomerService


def test_customer_round_trip_keeps_all_fields_and_contacts():
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
            Contact(name="Dr. Weiss", role="Inhaber", email="weiss@zahnarzt.de"),
        ],
    )
    data = c.to_dict()
    assert data["contacts"][1]["role"] == "Inhaber"

    restored = Customer.from_dict(data)
    assert (restored.customer_id, restored.practice_name, restored.is_vip, restored.website,
            restored.vm_number, restored.instance_number) == (
        "K-99999", "Zahnarztpraxis Dr. Weiss", True, "https://zahnarzt-weiss.de", 104, 2)
    assert [(k.name, k.phone, k.email) for k in restored.contacts] == [
        ("Fr. Schmidt", "089-123456", ""), ("Dr. Weiss", "", "weiss@zahnarzt.de")]


def test_customer_service_save_find_search_update_delete(storage):
    service = CustomerService(storage)
    a = Customer(customer_id="K-101", practice_name="Praxis A", website="https://praxis-a.de",
                 vm_number=101, instance_number=1, contacts=[Contact(name="Dr. A", role="Arzt")])
    b = Customer(customer_id="K-102", practice_name="Praxis B (VIP)", is_vip=True,
                 website="https://praxis-b.com", vm_number=102, instance_number=3,
                 contacts=[Contact(name="Dr. B", role="Leitung", email="b@praxis.de"),
                           Contact(name="Fr. C", role="Abrechnung", email="c@praxis.de")])
    service.save_customer(a)
    service.save_customer(b)

    found = service.get_customer_by_id("K-102")
    assert found is not None and found.is_vip and len(found.contacts) == 2

    # Search hits name, website and contact role.
    for query, expected in (("VIP", "K-102"), ("praxis-a.de", "K-101"), ("Abrechnung", "K-102")):
        assert [c.customer_id for c in service.search_customers(query)] == [expected]

    # Saving an existing id updates in place.
    a.practice_name = "Praxis A (Umbenannt)"
    service.save_customer(a)
    assert service.get_customer_by_id("K-101").practice_name == "Praxis A (Umbenannt)"
    assert len(storage.load_customers()) == 2

    storage.save_customers([c for c in storage.load_customers() if c.customer_id != "K-101"])
    assert service.get_customer_by_id("K-101") is None
