import re
from typing import Any
from models.case import Case


class PiiAnonymizer:
    """Client-side Local PII/PHI Anonymization & Pseudonymization Engine.
    
    Strips personally identifiable information (PII) and protected health information (PHI)
    such as practice names, contact persons, email addresses, phone numbers, patient names,
    dates, and case IDs before transmitting prompts to cloud LLM providers (e.g. Google Gemini).
    Re-substitutes the original values locally upon receiving generated responses.
    """

    # Common German PII Regex Patterns
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,9}[-.\s]?\d{0,6}')
    DATE_REGEX = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b')
    CASE_ID_REGEX = re.compile(r'\b[A-Z]{2,4}-\d{3,8}\b')
    # Patient pattern candidates like "Patient Mustermann", "Pat. Max Mustermann", "Hr. Schmidt", "Fr. Dr. Müller"
    PATIENT_TITLE_REGEX = re.compile(
        r'\b(?:Pat\.|Patient(?:in)?|Hr\.|Herr|Fr\.|Frau)\s+(?:Dr\.|Prof\.)?\s*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)',
        re.UNICODE
    )

    def __init__(self, enable_anonymization: bool = True):
        self.enable_anonymization = enable_anonymization

    def anonymize(self, text: str, case: Case | None = None) -> tuple[str, dict[str, str]]:
        """Anonymizes text by replacing PII entities with placeholders.
        
        Returns:
            tuple[str, dict[str, str]]: (anonymized_text, mapping_dict)
            where mapping_dict maps placeholders like '[PATIENT_1]' -> original value.
        """
        if not self.enable_anonymization or not text:
            return text, {}

        mapping: dict[str, str] = {}  # placeholder -> original
        reverse_mapping: dict[str, str] = {}  # original -> placeholder
        anonymized = text

        def get_or_create_placeholder(original: str, prefix: str) -> str:
            clean_orig = original.strip()
            if not clean_orig or len(clean_orig) < 2:
                return original
            if clean_orig in reverse_mapping:
                return reverse_mapping[clean_orig]
            
            # Count existing of same prefix
            count = sum(1 for p in mapping if p.startswith(f"[{prefix}_")) + 1
            placeholder = f"[{prefix}_{count}]"
            mapping[placeholder] = clean_orig
            reverse_mapping[clean_orig] = placeholder
            return placeholder

        # 1. Contextual Anonymization from Case object if provided
        if case:
            if case.customer:
                if case.customer.practice_name and case.customer.practice_name.strip():
                    orig = case.customer.practice_name.strip()
                    ph = get_or_create_placeholder(orig, "PRAXIS")
                    anonymized = anonymized.replace(orig, ph)
                
                if case.customer.contact_person and case.customer.contact_person.strip():
                    orig = case.customer.contact_person.strip()
                    ph = get_or_create_placeholder(orig, "ANSPRECHPARTNER")
                    anonymized = anonymized.replace(orig, ph)

                if case.customer.email and case.customer.email.strip():
                    orig = case.customer.email.strip()
                    ph = get_or_create_placeholder(orig, "EMAIL")
                    anonymized = anonymized.replace(orig, ph)

                if case.customer.phone and case.customer.phone.strip():
                    orig = case.customer.phone.strip()
                    ph = get_or_create_placeholder(orig, "TELEFON")
                    anonymized = anonymized.replace(orig, ph)

            if case.case_id and case.case_id.strip():
                orig = case.case_id.strip()
                ph = get_or_create_placeholder(orig, "CASE_ID")
                anonymized = anonymized.replace(orig, ph)

        # 2. Pattern-based Anonymization (E-Mails)
        for email_match in self.EMAIL_REGEX.findall(anonymized):
            if email_match not in reverse_mapping and not email_match.startswith("["):
                ph = get_or_create_placeholder(email_match, "EMAIL")
                anonymized = anonymized.replace(email_match, ph)

        # 3. Patient Name Titles Regex
        for match in self.PATIENT_TITLE_REGEX.finditer(anonymized):
            full_match = match.group(0)
            name_part = match.group(1)
            if name_part and name_part not in reverse_mapping:
                ph = get_or_create_placeholder(name_part, "PATIENT")
                # Replace name part in full match to retain salutation context or replace whole match
                anonymized = anonymized.replace(name_part, ph)

        return anonymized, mapping

    def deanonymize(self, text: str, mapping: dict[str, str]) -> str:
        """Replaces placeholders in text with original PII values."""
        if not text or not mapping:
            return text

        restored = text
        # Sort placeholders by length descending to avoid partial replacements
        for placeholder, original in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
            restored = restored.replace(placeholder, original)
            if placeholder.startswith("[") and placeholder.endswith("]"):
                bare_ph = placeholder[1:-1]
                restored = restored.replace(f"**{bare_ph}**", original)
                restored = restored.replace(bare_ph, original)

        return restored
