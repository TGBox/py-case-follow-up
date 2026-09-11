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
                or (c.website and q_lower in c.website.lower())
                or (c.vm_number is not None and q_lower in str(c.vm_number))
                or (c.instance_number is not None and q_lower in str(c.instance_number))
                or any(
                    q_lower in contact.name.lower()
                    or q_lower in contact.role.lower()
                    or q_lower in contact.email.lower()
                    or q_lower in contact.phone.lower()
                    for contact in c.contacts
                )
            ):
                results.append(c)
        return results

    @staticmethod
    def extract_customer_search_match_summary(
        customer: Customer,
        query: str,
        max_matches: int = 3,
        max_chars: int = 50,
    ) -> str | None:
        """Extracts matching words from non-primary customer fields (contacts, website, VM/instance numbers).

        Returns a comma-separated string of unique matching words with match count / character
        length caps, appending '...' when truncated, or None if no matches are found outside name/ID.
        """
        q = query.strip()
        if not q:
            return None

        q_lower = q.lower()
        fields_to_check: list[str] = []

        if customer.website:
            fields_to_check.append(customer.website)
        if customer.vm_number is not None:
            fields_to_check.append(str(customer.vm_number))
        if customer.instance_number is not None:
            fields_to_check.append(str(customer.instance_number))

        for contact in customer.contacts:
            if contact.name:
                fields_to_check.append(contact.name)
            if contact.role:
                fields_to_check.append(contact.role)
            if contact.email:
                fields_to_check.append(contact.email)
            if contact.phone:
                fields_to_check.append(contact.phone)

        unique_matches: list[str] = []
        seen: set[str] = set()
        has_more_matches = False
        strip_chars = ",;:()[]{}<>\"'\t\r\n"

        for field_text in fields_to_check:
            words = field_text.split()
            for w in words:
                clean_w = w.strip(strip_chars)
                if not clean_w:
                    continue
                if q_lower in clean_w.lower():
                    w_key = clean_w.lower()
                    if w_key in seen:
                        continue
                    seen.add(w_key)
                    if len(unique_matches) < max_matches:
                        unique_matches.append(clean_w)
                    else:
                        has_more_matches = True

        if not unique_matches:
            return None

        result_parts: list[str] = []
        current_len = 0
        truncated = has_more_matches

        for i, word in enumerate(unique_matches):
            add_len = len(word) + (2 if i > 0 else 0)
            if current_len + add_len > max_chars:
                if i == 0:
                    result_parts.append(word[: max(1, max_chars - 3)])
                    truncated = True
                else:
                    truncated = True
                break
            result_parts.append(word)
            current_len += add_len

        summary = ", ".join(result_parts)
        if truncated:
            summary += "..."
        return summary

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
