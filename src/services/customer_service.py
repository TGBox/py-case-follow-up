from models.customer import Customer, Contact
from services.storage_service import StorageService


class CustomerService:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    def get_all_customers(self) -> list[Customer]:
        return self.storage_service.load_customers()

    def get_customer_by_id(self, customer_id: str) -> Customer | None:
        customers = self.get_all_customers()
        for c in customers:
            if c.customer_id == customer_id:
                return c
        return None

    def search_customers(self, query: str) -> list[Customer]:
        if not query:
            return self.get_all_customers()
        
        q_lower = query.lower()
        results = []
        for c in self.get_all_customers():
            if (
                q_lower in c.customer_id.lower()
                or q_lower in c.practice_name.lower()
                or any(q_lower in contact.name.lower() for contact in c.contacts)
            ):
                results.append(c)
        return results

    def save_customer(self, customer: Customer) -> None:
        customers = self.get_all_customers()
        existing_idx = next((i for i, c in enumerate(customers) if c.customer_id == customer.customer_id), -1)
        if existing_idx >= 0:
            customers[existing_idx] = customer
        else:
            customers.append(customer)
        self.storage_service.save_customers(customers)

    def add_contact(self, customer_id: str, contact: Contact) -> bool:
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False
        customer.contacts.append(contact)
        self.save_customer(customer)
        return True
