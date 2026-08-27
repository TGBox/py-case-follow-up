import sqlite3
from pathlib import Path
from config import AppConfig
from enums import UrgencyLevel, BoardColumn, Actor, FieldType, TargetType, Channel, SyncMode, LayoutMode
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.schema import QuestionSchema, SchemaField
from models.export_template import ExportTemplate
from models.profile import UserProfile, UserInfo, UISettings, ShortcutSettings, ReminderSettings, ScoringMatrix, WikiSettings, Colleague
from services.storage_service import StorageService
from services.scoring_service import ScoringService


class SeedService:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
        self.config = storage_service.config

    def create_seed_customers(self) -> list[Customer]:
        return [
            Customer(
                customer_id="K-10482",
                practice_name="Gemeinschaftspraxis Dr. Müller & Partner",
                is_vip=True,
                system_version="v2026.2.4",
                website="https://praxis-ulm.de",
                vm_number=104,
                instance_number=1,
                general_notes="Abrechnungsleitung bevorzugt telefonischen Kontakt morgens vor 10:00 Uhr.",
                contacts=[
                    Contact(name="Dr. Hans Müller", role="Inhaber / Arzt", phone="+49 731 123456-0", email="mueller@praxis-ulm.de"),
                    Contact(name="Frau Sabine Weber", role="Abrechnungsleitung", phone="+49 731 123456-12", email="weber@praxis-ulm.de"),
                ],
            ),
            Customer(
                customer_id="K-10890",
                practice_name="Praxisklinik am Stadtgarten",
                is_vip=True,
                system_version="v2026.1.9",
                website="https://stadtgarten-praxis.de",
                vm_number=108,
                instance_number=2,
                general_notes="Großpraxis mit 8 Behandlungsstühlen.",
                contacts=[
                    Contact(name="Dr. Elena Rossi", role="Ärztliche Leitung", phone="+49 89 987654-0", email="rossi@stadtgarten-praxis.de"),
                ],
            ),
            Customer(
                customer_id="K-10211",
                practice_name="Zahnarztpraxis Dr. Schmidt",
                is_vip=False,
                system_version="v2025.4.1",
                website="https://schmidt-zahnarzt.de",
                vm_number=102,
                instance_number=1,
                general_notes="Nutzt Standard-Abrechnungsmodul.",
                contacts=[
                    Contact(name="Herr Thomas Schmidt", role="Praxisinhaber", phone="+49 30 5551234", email="info@schmidt-zahnarzt.de"),
                ],
            ),
            Customer(
                customer_id="K-10554",
                practice_name="MVZ Kardiologie Rhein-Neckar",
                is_vip=False,
                system_version="v2026.2.0",
                website="https://mvz-rhein-neckar.de",
                vm_number=105,
                instance_number=3,
                general_notes="Ansprechpartner IT: Herr Becker.",
                contacts=[
                    Contact(name="Klaus Becker", role="IT-Administrator", phone="+49 621 443322", email="it@mvz-rhein-neckar.de"),
                ],
            ),
            Customer(
                customer_id="K-10777",
                practice_name="Hausarztpraxis Dipl.-Med. Fischer",
                is_vip=False,
                system_version="v2026.2.4",
                website="https://hausarzt-leipzig.de",
                vm_number=107,
                instance_number=1,
                general_notes="Neukunde seit Anfang 2026.",
                contacts=[
                    Contact(name="Dipl.-Med. Petra Fischer", role="Ärztin", phone="+49 341 889900", email="fischer@hausarzt-leipzig.de"),
                ],
            ),
        ]

    def create_seed_schemas(self) -> list[QuestionSchema]:
        return [
            QuestionSchema(
                schema_id="schema_quick",
                display_name="⚡ Schnellerfassung / Allgemeiner Vorgang",
                description="Für die rasche Erfassung von Anfragen und Problemen ohne detaillierte Vorab-Spezifizierung.",
                default_suggested_exports=["mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label="Betroffenes Modul / Programmbereich (optional)", field_type=FieldType.TEXT, required=False, placeholder="z. B. Abrechnung, Terminkalender, Schnittstelle...", order=1),
                    SchemaField(field_id="short_description", label="Kurzbeschreibung / Stichwort (optional)", field_type=FieldType.TEXT, required=False, placeholder="z. B. Rückfrage zu Rezeptimport", order=2),
                    SchemaField(field_id="unformatted_description", label="Unformatierte Informationen / Beschreibung", field_type=FieldType.TEXT, required=False, placeholder="Hier alle ungefilterten Informationen, Mails oder Stichpunkte eingeben...", order=3),
                ],
            ),
            QuestionSchema(
                schema_id="schema_internal_task",
                display_name="🏢 Interne Aufgabe / Notiz",
                description="Für interne Aufgaben, Systemwartung, Prozessverbesserungen oder Notizen ohne Kundenbezug.",
                default_suggested_exports=[],
                fields=[
                    SchemaField(field_id="internal_category", label="Kategorie der Aufgabe", field_type=FieldType.DROPDOWN, options=["Systemwartung", "Dokumentation", "Entwicklungsaufgabe", "Prozessverbesserung", "Sonstiges"], required=True, order=1),
                    SchemaField(field_id="affected_systems", label="Betroffene Systeme / Server / Komponenten", field_type=FieldType.TEXT, required=False, placeholder="z. B. Server-02, P2P-Sync, Wiki-Cache...", order=2),
                    SchemaField(field_id="description", label="Ausführliche Aufgabenbeschreibung & Details", field_type=FieldType.TEXT, required=True, placeholder="Schritt-für-Schritt Aufgabenbeschreibung...", order=3),
                ],
            ),
            QuestionSchema(
                schema_id="schema_zuzahlungsnachforderung",
                display_name="Zuzahlungsnachforderung & Abrechnungskorrektur",
                description="Für Nachforderungen und Korrekturen gegenüber Abrechnungszentrum, Krankenkasse oder KV.",
                default_suggested_exports=["mail_dev_zuzahlung_abrechnung", "mail_kunden_rueckmeldung"],
                is_repeatable_group=True,
                repeatable_group_title="Datei / Korrektur-Anforderung",
                repeatable_field_ids=[
                    "action_type",
                    "esol_filename",
                    "invoice_number",
                    "invoice_date",
                    "prescription_info",
                    "prescription_date",
                    "patient_names",
                    "action_reason_detail",
                ],
                fields=[
                    SchemaField(field_id="action_type", label="Geforderte Aktion", field_type=FieldType.DROPDOWN, options=["Zuzahlungsnachforderung", "Abrechnungskorrektur"], required=True, order=1),
                    SchemaField(field_id="invoice_number", label="Betroffene Rechnungsnummer", field_type=FieldType.TEXT, required=True, placeholder="z. B. RE-2026-0815", order=2),
                    SchemaField(field_id="invoice_date", label="Rechnungsdatum", field_type=FieldType.TEXT, required=True, placeholder="YYYY-MM-DD", order=3),
                    SchemaField(field_id="prescription_info", label="Betroffene Verordnung", field_type=FieldType.TEXT, required=True, placeholder="z. B. VO-987654", order=4),
                    SchemaField(field_id="prescription_date", label="Datum der Verordnung", field_type=FieldType.TEXT, required=True, placeholder="YYYY-MM-DD", order=5),
                    SchemaField(field_id="patient_names", label="Namen der betroffenen Patienten", field_type=FieldType.TEXT, required=True, placeholder="z. B. Max Mustermann", order=6),
                    SchemaField(field_id="esol_filename", label="Name der originalen ESOL-Datei", field_type=FieldType.TEXT, required=True, placeholder="z. B. ESOL_20260801.dat", order=7),
                    SchemaField(field_id="action_reason_detail", label="Genaue Begründung & Details", field_type=FieldType.TEXT, required=True, placeholder="Ausführliche Beschreibung...", order=8),
                    SchemaField(field_id="has_forwarded_email_or_screenshot", label="Weitergeleitete Mail/Screenshot im Fallordner?", field_type=FieldType.BOOLEAN, required=True, order=9),
                ],
            ),
            QuestionSchema(
                schema_id="schema_feature_request",
                display_name="Kundenwunsch / Feature-Request",
                description="Zur Erfassung neuer Funktionswünsche von Praxen für die Entwicklungsabteilung.",
                default_suggested_exports=["gitlab_dev_kundenwunsch", "mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label="Betroffenes Modul / Programmbereich", field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="feature_description", label="Beschreibung des Kundenwunsches", field_type=FieldType.TEXT, required=True, order=2),
                    SchemaField(field_id="practice_benefit", label="Gewünschter Nutzen / Ziel für die Praxis", field_type=FieldType.TEXT, required=True, order=3),
                    SchemaField(field_id="has_mockup_or_screenshot", label="Screenshot/Skizze im Fallordner?", field_type=FieldType.BOOLEAN, required=False, order=4),
                ],
            ),
            QuestionSchema(
                schema_id="schema_bug_report",
                display_name="Programmfehler / Bug-Report",
                description="Zur Weiterleitung ungeklärter Software-Fehler an die Entwicklungsabteilung.",
                default_suggested_exports=["gitlab_dev_bug", "mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label="Betroffenes Modul", field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="error_message", label="Fehlermeldung / Code", field_type=FieldType.TEXT, required=True, order=2),
                    SchemaField(field_id="reproduction_steps", label="Schritte zur Reproduktion", field_type=FieldType.TEXT, required=True, order=3),
                    SchemaField(field_id="stack_trace", label="Stack-Trace / Logauszug", field_type=FieldType.TEXT, required=False, order=4),
                    SchemaField(field_id="database_dump_provided", label="Datenbank-Backup im Fallordner abgelegt?", field_type=FieldType.BOOLEAN, required=True, order=5),
                ],
            ),
        ]

    def create_seed_templates(self) -> list[ExportTemplate]:
        return [
            ExportTemplate(
                template_id="mail_dev_zuzahlung_abrechnung",
                display_name="E-Mail an Entwickler: Zuzahlung & Abrechnungskorrektur",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_zuzahlungsnachforderung"],
                description="Erzeugt eine vollständige E-Mail an das Entwicklerteam zur Nachberechnung oder Abrechnungskorrektur mit allen Pflichtdaten.",
                required_schema_fields=[
                    "action_type",
                    "invoice_number",
                    "invoice_date",
                    "prescription_info",
                    "prescription_date",
                    "patient_names",
                    "esol_filename",
                    "action_reason_detail",
                    "has_forwarded_email_or_screenshot",
                ],
                template_string=(
                    "Betreff: [{{ form_data.action_type | default('Abrechnungskorrektur') }}] {{ customer.practice_name }} (BSNR/Kundennr: {{ customer.customer_id }})\n\n"
                    "Hallo Entwicklerteam,\n\n"
                    "für die Praxis {{ customer.practice_name }} (Kundennummer: {{ customer.customer_id }}, Ansprechpartner: {{ customer.contact_person }}) liegt eine Anforderung zur Zuzahlungsnachforderung / Abrechnungskorrektur vor.\n\n"
                    "{% if form_data.file_requests and form_data.file_requests | length > 0 %}\n"
                    "### Details zu den erfassten Datei-Anforderungen ({{ form_data.file_requests | length }} Anfragen):\n"
                    "{% for req in form_data.file_requests %}\n"
                    "--- Datei-Anforderung #{{ loop.index }} ---\n"
                    "* **Aktions-Typ:** {{ req.action_type | default(form_data.action_type) }}\n"
                    "* **Original ESOL-Datei:** {{ req.esol_filename | default(form_data.esol_filename) }}\n"
                    "* **Rechnungsnummer:** {{ req.invoice_number | default(form_data.invoice_number) }} (vom {{ req.invoice_date | default(form_data.invoice_date) }})\n"
                    "* **Verordnung:** {{ req.prescription_info | default(form_data.prescription_info) }} (vom {{ req.prescription_date | default(form_data.prescription_date) }})\n"
                    "* **Betroffene Patienten:** {{ req.patient_names | default(form_data.patient_names) }}\n"
                    "* **Begründung & Details:** {{ req.action_reason_detail | default(form_data.action_reason_detail) }}\n\n"
                    "{% endfor %}\n"
                    "{% else %}\n"
                    "### Details zur Anforderung:\n"
                    "* **Aktions-Typ:** {{ form_data.action_type }}\n"
                    "* **Original ESOL-Datei:** {{ form_data.esol_filename }}\n"
                    "* **Rechnungsnummer:** {{ form_data.invoice_number }} (vom {{ form_data.invoice_date }})\n"
                    "* **Verordnung:** {{ form_data.prescription_info }} (vom {{ form_data.prescription_date }})\n"
                    "* **Betroffene Patienten:** {{ form_data.patient_names }}\n"
                    "* **Begründung & Details:** {{ form_data.action_reason_detail }}\n\n"
                    "{% endif %}\n"
                    "### Belege & Anhänge:\n"
                    "* **Weitergeleitete Mail / Screenshot im Fallordner:** {{ 'JA (siehe Fallordner ' ~ attachment_directory ~ ')' if form_data.has_forwarded_email_or_screenshot else 'NEIN' }}\n\n"
                    "---\n"
                    "*Erfasst durch Support: {{ created_by }}*"
                ),
            ),
            ExportTemplate(
                template_id="gitlab_dev_kundenwunsch",
                display_name="GitLab / Dev-Ticket: Kundenwunsch",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_feature_request"],
                description="Formatiertes Markdown-Ticket für neue Funktionswünsche an die Entwicklungsabteilung.",
                required_schema_fields=["module_name", "feature_description", "practice_benefit"],
                template_string=(
                    "### Feature-Request: {{ classification.title }}\n"
                    "**Praxis:** {{ customer.practice_name }} (Kundennr: {{ customer.customer_id }}) {{ '★ VIP-Kunde' if customer.is_vip else '' }}\n"
                    "**Betroffenes Modul:** {{ form_data.module_name }}\n\n"
                    "#### Beschreibung des Kundenwunsches:\n"
                    "{{ form_data.feature_description }}\n\n"
                    "#### Gewünschter Nutzen / Ziel für die Praxis:\n"
                    "{{ form_data.practice_benefit }}\n\n"
                    "#### Mockups / Screenshots:\n"
                    "{{ 'Screenshots / Skizzen sind im Fallordner hinterlegt (' ~ attachment_directory ~ ')' if form_data.has_mockup_or_screenshot else 'Keine Screenshots hinterlegt' }}\n\n"
                    "---\n"
                    "*Erfasst durch Support: {{ created_by }}*"
                ),
            ),
            ExportTemplate(
                template_id="gitlab_dev_bug",
                display_name="GitLab / Dev-Ticket: Programmierfehler (Bug)",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_bug_report"],
                description="Entwickler-Ticket für Softwarefehler, Abstürze und Schnittstellenprobleme.",
                required_schema_fields=["module_name", "error_message", "reproduction_steps", "database_dump_provided"],
                template_string=(
                    "### Bug-Report: {{ classification.title }}\n"
                    "**Praxis:** {{ customer.practice_name }} (Kundennr: {{ customer.customer_id }})\n"
                    "**Modul:** {{ form_data.module_name }}\n"
                    "**Fehlermeldung:** {{ form_data.error_message }}\n\n"
                    "#### Schritte zur Reproduktion:\n"
                    "{{ form_data.reproduction_steps }}\n\n"
                    "#### Stack-Trace / Logauszug:\n"
                    "```\n"
                    "{{ form_data.stack_trace if form_data.stack_trace else 'Kein Stack-Trace angegeben' }}\n"
                    "```\n\n"
                    "#### DB-Backup / Logfiles:\n"
                    "{{ 'Vorhanden im Ordner ' ~ attachment_directory if form_data.database_dump_provided else '[FEHLT: DB-Dump / Logfile]' }}\n\n"
                    "---\n"
                    "*Erfasst durch Support: {{ created_by }}*"
                ),
            ),
            ExportTemplate(
                template_id="mail_kunden_rueckmeldung",
                display_name="E-Mail an Praxis: Lösungs-Zusammenfassung",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_zuzahlungsnachforderung", "schema_feature_request", "schema_bug_report"],
                description="Kunden-E-Mail mit Zusammenfassung der Lösung und Kontaktdaten.",
                required_schema_fields=[],
                template_string=(
                    "Sehr geehrte/r {{ customer.contact_person if customer.contact_person else 'Damen und Herren' }},\n\n"
                    "vielen Dank für Ihre Anfrage bezüglich \"{{ classification.title }}\" (Fall-ID: {{ case.case_id }}).\n\n"
                    "### Status / Zusammenfassung:\n"
                    "{{ timeline[-1].note if timeline else 'Ihr Anliegen befindet sich derzeit in Bearbeitung.' }}\n\n"
                    "Sollten Sie hierzu Fragen haben, erreichen Sie uns jederzeit unter Angabe der Fall-ID {{ case.case_id }}.\n\n"
                    "Mit freundlichen Grüßen\n"
                    "{{ created_by }}\n"
                    "Support-Team"
                ),
            ),
        ]

    def create_seed_cases(self) -> list[Case]:
        scoring_service = ScoringService()
        cases = [
            Case(
                case_id="T-2026-0001",
                created_at="2026-08-23T09:15:00",
                updated_at="2026-08-23T14:30:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10482",
                    practice_name="Gemeinschaftspraxis Dr. Müller & Partner",
                    is_vip=True,
                    contact_person="Frau Weber",
                    phone="+49 731 123456-12",
                ),
                classification=Classification(
                    schema_id="schema_zuzahlungsnachforderung",
                    title="Zuzahlungsnachforderungsdatei fehlerhaft erzeugt",
                    deadline_callback="2026-08-23T16:00:00",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.DEVELOPMENT,
                    actor_since="2026-08-23T10:00:00",
                ),
                form_data={
                    "action_type": "Zuzahlungsnachforderung",
                    "invoice_number": "RE-2026-0815",
                    "invoice_date": "2026-08-01",
                    "prescription_info": "VO-987654 (Physiotherapie)",
                    "prescription_date": "2026-07-15",
                    "patient_names": "Max Mustermann, Maria Muster",
                    "esol_filename": "ESOL_20260801_Praxis.dat",
                    "action_reason_detail": "Nachforderung von 14 Zuzahlungsbeträgen nach Abrechnungskorrektur.",
                    "has_forwarded_email_or_screenshot": True,
                },
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0001_Gemeinschaftspraxis_Dr_Mueller/",
                timeline=[
                    TimelineEntry(
                        timestamp="2026-08-23T09:15:00",
                        author="Daniel Rösch",
                        channel=Channel.PHONE_INBOUND,
                        note="Praxis meldet Abbruch beim Erzeugen der Zuzahlungsdatei. Rückruf bis 16:00 versprochen.",
                        status_change="NEW -> ACTION_REQUIRED (SUPPORT)",
                    ),
                    TimelineEntry(
                        timestamp="2026-08-23T10:00:00",
                        author="Daniel Rösch",
                        channel=Channel.DEV_TICKET,
                        note="Ticket via GitLab-Template an Dev übergeben. Warte auf Prüfung der Abrechnungs-Engine.",
                        status_change="ACTION_REQUIRED (SUPPORT) -> ACTION_REQUIRED (DEVELOPMENT)",
                    ),
                ],
            ),
            Case(
                case_id="T-2026-0002",
                created_at="2026-08-20T11:00:00",
                updated_at="2026-08-20T11:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10890",
                    practice_name="Praxisklinik am Stadtgarten",
                    is_vip=True,
                    contact_person="Dr. Elena Rossi",
                    phone="+49 89 987654-0",
                ),
                classification=Classification(
                    schema_id="schema_bug_report",
                    title="Absturz beim Drucken von BMA-Rezepten",
                    deadline_callback="2026-08-21T10:00:00",  # Overdue
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-20T11:00:00",
                    is_data_complete=True,
                ),
                form_data={
                    "module_name": "Rezeptdruck",
                    "reproduction_steps": "Drucken -> BMA auswählen -> Vorschau klicken",
                    "stack_trace": "Access Violation at 0x0045A1",
                },
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0002_Praxisklinik_Stadtgarten/",
                timeline=[
                    TimelineEntry(timestamp="2026-08-20T11:00:00", author="Daniel Rösch", note="Rezeptdruck stürzt ab"),
                ],
            ),
            Case(
                case_id="T-2026-0003",
                created_at="2026-08-23T12:00:00",
                updated_at="2026-08-23T12:00:00",
                created_by="Max Müller",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10211",
                    practice_name="Zahnarztpraxis Dr. Schmidt",
                    is_vip=False,
                    contact_person="Herr Schmidt",
                    phone="+49 30 5551234",
                ),
                classification=Classification(
                    schema_id="schema_abrechnungskorrektur",
                    title="KV-Abrechnungstext korrigieren",
                    deadline_callback="",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.NEW,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-23T12:00:00",
                    is_data_complete=True,
                ),
                form_data={"kv_region": "KV Berlin", "correction_reason": "Falsche KV-Nummer"},
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0003_Zahnarztpraxis_Schmidt/",
                timeline=[TimelineEntry(timestamp="2026-08-23T12:00:00", author="Max Müller", note="Anfrage zur Korrektur")],
            ),
            Case(
                case_id="T-2026-0004",
                created_at="2026-08-22T15:00:00",
                updated_at="2026-08-22T15:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10554",
                    practice_name="MVZ Kardiologie Rhein-Neckar",
                    is_vip=False,
                    contact_person="Klaus Becker",
                    phone="+49 621 443322",
                ),
                classification=Classification(
                    schema_id="schema_zuzahlungsnachforderung",
                    title="Prüfung Nachforderung 2026-Q1",
                    deadline_callback="",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.WAITING,
                    current_actor=Actor.CUSTOMER,
                    actor_since="2026-08-22T15:00:00",
                    is_data_complete=False,
                ),
                form_data={"billing_quarter": "2026-Q1", "error_code": "ERR_CHECK_04"},
                missing_required_fields=["database_dump_provided"],
                attachment_directory="attachments/T-2026-0004_MVZ_Kardiologie/",
                timeline=[TimelineEntry(timestamp="2026-08-22T15:00:00", author="Daniel Rösch", note="Warten auf DB-Dump der Praxis")],
            ),
            Case(
                case_id="T-2026-0005",
                created_at="2026-08-23T13:00:00",
                updated_at="2026-08-23T13:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10777",
                    practice_name="Hausarztpraxis Dipl.-Med. Fischer",
                    is_vip=False,
                    contact_person="Dipl.-Med. Fischer",
                    phone="+49 341 889900",
                ),
                classification=Classification(
                    schema_id="schema_bug_report",
                    title="GUI-Schriftgröße im Laborfenster zu klein",
                    deadline_callback="",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.NEW,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-23T13:00:00",
                    is_data_complete=True,
                ),
                form_data={"module_name": "Labor", "reproduction_steps": "Laborblatt öffnen auf 4K Monitor"},
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0005_Hausarztpraxis_Fischer/",
                timeline=[TimelineEntry(timestamp="2026-08-23T13:00:00", author="Daniel Rösch", note="Feedback erfasst")],
            ),
            Case(
                case_id="T-2026-0006",
                created_at="2026-08-15T08:00:00",
                updated_at="2026-08-16T10:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10482",
                    practice_name="Gemeinschaftspraxis Dr. Müller & Partner",
                    is_vip=True,
                ),
                classification=Classification(
                    schema_id="schema_abrechnungskorrektur",
                    title="Alte Abrechnung Q1 gelöst",
                    deadline_callback="",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=True,
                    is_archived=False,
                    board_column=BoardColumn.DONE,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-16T10:00:00",
                    is_data_complete=True,
                ),
                form_data={"kv_region": "KV BW", "correction_reason": "Korrektur abgeschlossen"},
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0006_Gemeinschaftspraxis_Dr_Mueller/",
                timeline=[TimelineEntry(timestamp="2026-08-16T10:00:00", author="Daniel Rösch", note="Erfolgreich abgeschlossen")],
            ),
            Case(
                case_id="T-2026-0007",
                created_at="2026-07-01T09:00:00",
                updated_at="2026-07-05T12:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10890",
                    practice_name="Praxisklinik am Stadtgarten",
                    is_vip=True,
                ),
                classification=Classification(
                    schema_id="schema_bug_report",
                    title="Uralter Fall aus dem Vormonat",
                    deadline_callback="",
                ),
                workflow_status=WorkflowStatus(
                    is_completed=True,
                    is_archived=False,
                    board_column=BoardColumn.DONE,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-07-05T12:00:00",
                    is_data_complete=True,
                ),
                form_data={"module_name": "System", "reproduction_steps": "Behoben"},
                missing_required_fields=[],
                attachment_directory="attachments/T-2026-0007_Praxisklinik_Stadtgarten/",
                timeline=[TimelineEntry(timestamp="2026-07-05T12:00:00", author="Daniel Rösch", note="Geklärt")],
            ),
            Case(
                case_id="T-2026-0008",
                created_at="2026-08-23T14:00:00",
                updated_at="2026-08-23T14:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10211",
                    practice_name="Zahnarztpraxis Dr. Schmidt",
                    is_vip=False,
                ),
                classification=Classification(
                    schema_id="schema_zuzahlungsnachforderung",
                    title="Frische Nachforderung ohne DB-Dump",
                    deadline_callback="2026-08-23T18:00:00",
                    tags=["Abrechnung", "Nachforderung"],
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-23T14:00:00",
                    is_data_complete=False,
                ),
                form_data={"action_type": "Zuzahlungsnachforderung", "invoice_number": "RE-999"},
                missing_required_fields=["prescription_info"],
                attachment_directory="attachments/T-2026-0008_Zahnarztpraxis_Schmidt/",
                timeline=[TimelineEntry(timestamp="2026-08-23T14:00:00", author="Daniel Rösch", note="Neu erfasst")],
            ),
            Case(
                case_id="T-2026-0009",
                created_at="2026-08-22T08:30:00",
                updated_at="2026-08-23T11:00:00",
                created_by="Max Müller",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10482",
                    practice_name="Gemeinschaftspraxis Dr. Müller & Partner",
                    is_vip=True,
                    contact_person="Dr. Müller",
                ),
                classification=Classification(
                    schema_id="schema_feature_request",
                    title="Kundenwunsch: Schnell-Button für eRezept-Export",
                    tags=["Kundenwunsch", "eRezept", "VIP"],
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.IN_PROGRESS,
                    current_actor=Actor.DEVELOPMENT,
                    actor_since="2026-08-22T10:00:00",
                    followup_at="2026-08-25T09:00:00",
                    followup_note="Beim Dev-Team nach Sprint-Einplanung fragen",
                    is_data_complete=True,
                ),
                form_data={
                    "module_name": "eRezept / Verordnung",
                    "feature_description": "Praxis wünscht sich 1-Klick-Button in der Patientenakte.",
                    "practice_benefit": "Zeitersparnis von ca. 30 Min pro Tag bei Rezeptausgabe.",
                    "has_mockup_or_screenshot": True,
                },
                attachment_directory="attachments/T-2026-0009_Feature_eRezept/",
                timeline=[
                    TimelineEntry(timestamp="2026-08-22T08:30:00", author="Max Müller", note="Kundenwunsch am Telefon erfasst"),
                    TimelineEntry(timestamp="2026-08-22T10:00:00", author="Daniel Rösch", note="An Produktmanagement/Dev übergeben", status_change="ZUSTÄNDIGKEIT: Support -> Entwicklung"),
                ],
            ),
            Case(
                case_id="T-2026-0010",
                created_at="2026-08-23T15:20:00",
                updated_at="2026-08-23T15:20:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10554",
                    practice_name="MVZ Kardiologie Rhein-Neckar",
                    is_vip=False,
                    contact_person="Klaus Becker",
                ),
                classification=Classification(
                    schema_id="schema_bug_report",
                    title="Kartenleser-Treiber nach Windows-Update getrennt",
                    tags=["Hardware", "Treiber"],
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.TECH,
                    actor_since="2026-08-23T15:20:00",
                    followup_at="2026-08-24T10:00:00",
                    followup_note="Fernwartung mit IT-Admin Becker durchführen",
                    is_data_complete=True,
                ),
                form_data={
                    "module_name": "EGK-Kartenleser",
                    "error_message": "DEVICE_NOT_FOUND (Code 43)",
                    "reproduction_steps": "Leser an USB 3.0 anschließen -> Dienst startet nicht",
                    "database_dump_provided": False,
                },
                attachment_directory="attachments/T-2026-0010_Kartenleser/",
                timeline=[TimelineEntry(timestamp="2026-08-23T15:20:00", author="Daniel Rösch", note="Fernwartungs-Termin vereinbart")],
            ),
            Case(
                case_id="T-2026-0011",
                created_at="2026-08-01T10:00:00",
                updated_at="2026-08-02T12:00:00",
                created_by="Daniel Rösch",
                assigned_to="Daniel Rösch",
                customer=CaseCustomer(
                    customer_id="K-10777",
                    practice_name="Hausarztpraxis Dipl.-Med. Fischer",
                    is_vip=False,
                ),
                classification=Classification(
                    schema_id="schema_zuzahlungsnachforderung",
                    title="Alte Nachforderung aus Vorquartal (Archiviert)",
                    tags=["Archiv"],
                ),
                workflow_status=WorkflowStatus(
                    is_completed=True,
                    is_archived=True,
                    board_column=BoardColumn.DONE,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-02T12:00:00",
                    is_data_complete=True,
                ),
                form_data={"action_type": "Zuzahlungsnachforderung", "invoice_number": "RE-OLD-01"},
                attachment_directory="attachments/T-2026-0011_Archiv/",
                timeline=[TimelineEntry(timestamp="2026-08-02T12:00:00", author="Daniel Rösch", note="Fall abgeschlossen und archiviert")],
            ),
            Case(
                case_id="T-2026-0012",
                created_at="2026-08-23T16:00:00",
                updated_at="2026-08-23T16:00:00",
                created_by="Max Müller",
                assigned_to="Max Müller",
                customer=CaseCustomer(
                    customer_id="K-10890",
                    practice_name="Praxisklinik am Stadtgarten",
                    is_vip=True,
                ),
                classification=Classification(
                    schema_id="schema_bug_report",
                    title="Absturz bei PVS-GKV Abrechnungsexport",
                    deadline_callback="2026-08-23T17:30:00",  # Overdue
                    tags=["Dringend", "VIP", "Absturz"],
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.DEVELOPMENT,
                    actor_since="2026-08-23T16:00:00",
                    is_data_complete=False,
                ),
                form_data={"module_name": "GKV-Export", "error_message": "ERR_ACCESS_VIOLATION_0x00FF"},
                missing_required_fields=["reproduction_steps", "database_dump_provided"],
                attachment_directory="attachments/T-2026-0012_Absturz_PVS/",
                timeline=[TimelineEntry(timestamp="2026-08-23T16:00:00", author="Max Müller", note="Kritischer Fehler bei Abrechnung")],
            ),
        ]

        # Update scoring on all cases
        for c in cases:
            c.is_demo_data = True
            scoring_service.update_case_scoring(c)

        return cases

    def create_seed_wiki_db(self) -> Path:
        db_path = self.config.wiki_db_path
        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create relational tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wiki_pages (
                page_id INTEGER PRIMARY KEY,
                book_id INTEGER,
                title TEXT,
                slug TEXT,
                url TEXT,
                updated_at TEXT,
                content_markdown TEXT
            )
        """)

        # Create FTS5 table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
                page_id UNINDEXED,
                title,
                content
            )
        """)

        # Insert seed articles
        articles = [
            (1, 10, "Abrechnungs-Engine: Fehlercodes & Korrekturen", "abrechnungs-engine-fehlercodes", "https://wiki.intern.software.de/books/abrechnung/page/fehlercodes", "2026-08-01T10:00:00", "Handbuch für Zuzahlungsdateien und DB-Export Fehler ERR_DB_EXPORT_902. Bei Abbruch muss die Tabelle tb_zuzahlung geprüft werden."),
            (2, 10, "GitLab Issue-Tracker Richtlinien", "gitlab-issue-tracker-richtlinien", "https://wiki.intern.software.de/books/dev/page/gitlab-issues", "2026-07-15T14:20:00", "Entwickler-Tickets müssen stets Praxis-Name, Kunden-ID, Quartal und DB-Dump Pfad im Attachment-Ordner enthalten."),
            (3, 12, "Cobra CRM Anbindung & Historie", "cobra-crm-anbindung", "https://wiki.intern.software.de/books/crm/page/cobra-anbindung", "2026-08-10T11:00:00", "Anleitung für die Übernahme von Support-Notizen in Cobra CRM Kontakte."),
        ]

        for p_id, b_id, title, slug, url, updated_at, content in articles:
            cursor.execute(
                "INSERT INTO wiki_pages (page_id, book_id, title, slug, url, updated_at, content_markdown) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (p_id, b_id, title, slug, url, updated_at, content),
            )
            cursor.execute(
                "INSERT INTO wiki_fts (page_id, title, content) VALUES (?, ?, ?)",
                (p_id, title, content),
            )

        conn.commit()
        conn.close()
        return db_path

    def run_seed(self, force: bool = False) -> dict[str, int]:
        """Runs complete seeding process."""
        self.config.ensure_directories()

        customers = self.create_seed_customers()
        schemas = self.create_seed_schemas()
        templates = self.create_seed_templates()
        cases = self.create_seed_cases()

        self.storage.save_customers(customers)
        self.storage.save_schemas(schemas)
        self.storage.save_templates(templates)
        self.storage.save_cases(cases)

        # Profile & Colleagues
        profile = UserProfile(
            user=UserInfo(name="Daniel Rösch", extension="244", email="d.roesch@softwarehersteller.de"),
            ui_settings=UISettings(theme="SYSTEM", default_layout=LayoutMode.COCKPIT),
            wiki_settings=WikiSettings(api_url="https://wiki.intern.software.de", sync_mode=SyncMode.METADATA_ONLY),
        )
        self.storage.save_profile(profile)

        colleagues = [
            Colleague(
                username="mmueller",
                name="Max Müller",
                department="Support",
                extension="245",
                email="m.mueller@softwarehersteller.de",
                notes="Support-Spezialist",
                cases_path=str(self.config.colleagues_dir / "mmueller_cases.json"),
                is_absent=False,
                absence_reason="",
            )
        ]
        self.storage.save_colleagues(colleagues)

        self.create_seed_wiki_db()

        return {
            "customers": len(customers),
            "schemas": len(schemas),
            "templates": len(templates),
            "cases": len(cases),
        }
