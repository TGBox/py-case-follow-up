import csv
import json
from pathlib import Path
from typing import Any
from models.customer import Customer, Contact
from constants import COBRA_FIELD_ALIAS_MAP

FIELD_ALIAS_MAP = COBRA_FIELD_ALIAS_MAP


class CobraCrmImportService:
    """Service for parsing and importing Cobra CRM customer/practice export files."""

    @staticmethod
    def parse_file(file_path: Path | str) -> tuple[list[dict[str, str]], list[str]]:
        """Parses a CSV, TXT, or JSON file and returns (rows_as_dicts, header_list)."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Import file not found: {p}")

        if p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    headers = list(data[0].keys())
                    rows = [{k: str(v) for k, v in item.items()} for item in data]
                    return rows, headers
                return [], []

        # CSV / TXT Parsing with delimiter auto-detection
        content = p.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            return [], []

        first_line = content.splitlines()[0]
        delimiter = ";"
        if ";" in first_line:
            delimiter = ";"
        elif "\t" in first_line:
            delimiter = "\t"
        elif "," in first_line:
            delimiter = ","
        elif "|" in first_line:
            delimiter = "|"

        lines = content.splitlines()
        reader = csv.reader(lines, delimiter=delimiter)
        raw_rows = [row for row in reader if row]

        if not raw_rows:
            return [], []

        headers = [h.strip() for h in raw_rows[0]]
        rows = []
        for r in raw_rows[1:]:
            row_dict = {}
            for idx, h in enumerate(headers):
                row_dict[h] = r[idx].strip() if idx < len(r) else ""
            rows.append(row_dict)

        return rows, headers

    @staticmethod
    def auto_detect_mapping(headers: list[str]) -> dict[str, str]:
        """Maps target Customer fields to the best matching source header column."""
        mapping: dict[str, str] = {}
        headers_lower = {h.lower().strip(): h for h in headers}

        for target_field, aliases in FIELD_ALIAS_MAP.items():
            found_header = ""
            for alias in aliases:
                if alias in headers_lower:
                    found_header = headers_lower[alias]
                    break

            if not found_header:
                # Partial match check
                for h_lower, orig_h in headers_lower.items():
                    if any(a in h_lower for a in aliases):
                        found_header = orig_h
                        break

            mapping[target_field] = found_header

        return mapping

    @staticmethod
    def map_rows_to_customers(rows: list[dict[str, str]], mapping: dict[str, str]) -> list[Customer]:
        """Converts raw row dicts into Customer objects based on column mapping."""
        customers: list[Customer] = []

        for idx, row in enumerate(rows, start=1):
            vnum1_val = row.get(mapping.get("vnum1", ""), "").strip()
            cust_id = row.get(mapping.get("customer_id", ""), "").strip() or vnum1_val
            prac_name = row.get(mapping.get("practice_name", ""), "").strip()
            prac_old = row.get(mapping.get("practice_name_old", ""), "").strip()
            salut = row.get(mapping.get("salutation", ""), "").strip()
            fname = row.get(mapping.get("first_name", ""), "").strip()
            lname = row.get(mapping.get("last_name", ""), "").strip()
            contact_name = row.get(mapping.get("contact_person", ""), "").strip()
            
            street = row.get(mapping.get("street", ""), "").strip()
            zip_code = row.get(mapping.get("zip_code", ""), "").strip()
            city = row.get(mapping.get("city", ""), "").strip()

            phone_m = row.get(mapping.get("phone_main", ""), "").strip() or row.get(mapping.get("phone", ""), "").strip()
            phone_dir = row.get(mapping.get("phone_direct", ""), "").strip()
            phone_priv = row.get(mapping.get("phone_private", ""), "").strip()
            phone2 = row.get(mapping.get("phone2", ""), "").strip()
            phone3 = row.get(mapping.get("phone3", ""), "").strip()
            mobile = row.get(mapping.get("mobile", ""), "").strip()
            mobile_priv = row.get(mapping.get("mobile_private", ""), "").strip()
            email = row.get(mapping.get("email_address", ""), "").strip() or row.get(mapping.get("email", ""), "").strip()
            email2 = row.get(mapping.get("email2", ""), "").strip()
            email3 = row.get(mapping.get("email3", ""), "").strip()

            vip_raw = row.get(mapping.get("is_vip", ""), "").strip().lower()
            sys_ver = row.get(mapping.get("system_version", ""), "").strip()
            dsc_val = row.get(mapping.get("dsc", ""), "").strip()
            dsc_neu_val = row.get(mapping.get("dsc_neu", ""), "").strip()

            vm_raw = row.get(mapping.get("vm_number", ""), "").strip()
            inst_raw = row.get(mapping.get("instance_number", ""), "").strip()
            notes = row.get(mapping.get("general_notes", ""), "").strip()

            if not prac_name:
                continue

            if not cust_id:
                cust_id = f"K-COBRA-{idx:04d}"

            is_vip = vip_raw in {"true", "1", "ja", "yes", "vip", "y"}

            vm_num = int(vm_raw) if vm_raw.isdigit() else (int(vnum1_val) if vnum1_val.isdigit() else None)
            inst_num = int(inst_raw) if inst_raw.isdigit() else None

            # Parse contact name into fname/lname if not given separately
            if not salut and not fname and not lname and contact_name:
                parts = contact_name.strip().split()
                if len(parts) == 1:
                    lname = parts[0]
                elif len(parts) == 2:
                    fname, lname = parts[0], parts[1]
                elif len(parts) >= 3:
                    salut, fname, lname = parts[0], parts[1], " ".join(parts[2:])

            contacts = []
            if contact_name or fname or lname or email or phone_m:
                disp_name = f"{salut} {fname} {lname}".strip() or contact_name or "Ansprechpartner"
                contacts.append(Contact(name=disp_name, phone=phone_m or phone_dir or mobile, email=email))

            c = Customer(
                customer_id=cust_id,
                vnum1=vnum1_val,
                practice_name=prac_name,
                practice_name_old=prac_old,
                salutation=salut,
                first_name=fname,
                last_name=lname,
                street=street,
                zip_code=zip_code,
                city=city,
                phone_main=phone_m,
                phone_direct=phone_dir,
                phone_private=phone_priv,
                phone2=phone2,
                phone3=phone3,
                mobile=mobile,
                mobile_private=mobile_priv,
                email_address=email,
                email2=email2,
                email3=email3,
                is_vip=is_vip,
                system_version=sys_ver,
                dsc=dsc_val,
                dsc_neu=dsc_neu_val,
                vm_number=vm_num,
                instance_number=inst_num,
                general_notes=notes,
                contacts=contacts,
            )
            customers.append(c)

        return customers

    @staticmethod
    def compare_with_existing(imported: list[Customer], existing: list[Customer]) -> dict[str, Any]:
        """Gleicht importierte Kunden mit bestehenden ab."""
        existing_ids = {c.customer_id: c for c in existing if c.customer_id}
        existing_names = {c.practice_name.lower(): c for c in existing if c.practice_name}

        new_customers: list[Customer] = []
        duplicates: list[dict[str, Customer]] = []

        for imp in imported:
            match = None
            if imp.customer_id in existing_ids:
                match = existing_ids[imp.customer_id]
            elif imp.practice_name.lower() in existing_names:
                match = existing_names[imp.practice_name.lower()]

            if match:
                duplicates.append({"existing": match, "imported": imp})
            else:
                new_customers.append(imp)

        return {
            "new": new_customers,
            "duplicates": duplicates,
            "total_imported": len(imported),
        }

    @staticmethod
    def merge_customers(existing: list[Customer], imported: list[Customer], mode: str = "update") -> list[Customer]:
        """Führt den Kundenstamm basierend auf dem gewählten Modus zusammen (update, skip, all_new)."""
        import copy
        existing_copies = copy.deepcopy(existing)
        result_map: dict[str, Customer] = {c.customer_id: c for c in existing_copies}

        for imp in imported:
            if imp.customer_id in result_map:
                if mode == "update":
                    old = result_map[imp.customer_id]
                    old.vnum1 = imp.vnum1 or old.vnum1
                    old.practice_name = imp.practice_name or old.practice_name
                    old.practice_name_old = imp.practice_name_old or old.practice_name_old
                    old.salutation = imp.salutation or old.salutation
                    old.first_name = imp.first_name or old.first_name
                    old.last_name = imp.last_name or old.last_name
                    old.street = imp.street or old.street
                    old.zip_code = imp.zip_code or old.zip_code
                    old.city = imp.city or old.city
                    old.phone_main = imp.phone_main or old.phone_main
                    old.phone_direct = imp.phone_direct or old.phone_direct
                    old.phone_private = imp.phone_private or old.phone_private
                    old.phone2 = imp.phone2 or old.phone2
                    old.phone3 = imp.phone3 or old.phone3
                    old.mobile = imp.mobile or old.mobile
                    old.mobile_private = imp.mobile_private or old.mobile_private
                    old.email_address = imp.email_address or old.email_address
                    old.email2 = imp.email2 or old.email2
                    old.email3 = imp.email3 or old.email3
                    old.is_vip = imp.is_vip if imp.is_vip else old.is_vip
                    old.system_version = imp.system_version or old.system_version
                    old.dsc = imp.dsc or old.dsc
                    old.dsc_neu = imp.dsc_neu or old.dsc_neu
                    old.vm_number = imp.vm_number if imp.vm_number is not None else old.vm_number
                    old.instance_number = imp.instance_number if imp.instance_number is not None else old.instance_number
                    old.general_notes = imp.general_notes or old.general_notes
                    if imp.additional_contacts:
                        for ac in imp.additional_contacts:
                            if ac not in old.additional_contacts:
                                old.additional_contacts.append(ac)
                    if imp.contacts:
                        old.contacts = imp.contacts
                elif mode == "skip":
                    continue
            else:
                result_map[imp.customer_id] = imp

        return list(result_map.values())
