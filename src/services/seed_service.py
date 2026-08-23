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
                general_notes="Neukunde seit Anfang 2026.",
                contacts=[
                    Contact(name="Dipl.-Med. Petra Fischer", role="Ärztin", phone="+49 341 889900", email="fischer@hausarzt-leipzig.de"),
                ],
            ),
        ]

    def create_seed_schemas(self) -> list[QuestionSchema]:
        return [
            QuestionSchema(
                schema_id="schema_zuzahlungsnachforderung",
                display_name="Zuzahlungsnachforderung / Abrechnungskorrektur",
                description="Erforderlich für manuelle Nachberechnungen und Datenbankanpassungen durch Devs.",
                default_suggested_exports=["gitlab_dev_ticket", "mail_abrechnung_team"],
                fields=[
                    SchemaField(field_id="billing_quarter", label="Abrechnungsquartal", field_type=FieldType.DROPDOWN, options=["2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"], required=True, order=1),
                    SchemaField(field_id="affected_patients_count", label="Anzahl betroffener Fälle", field_type=FieldType.NUMBER, required=False, order=2),
                    SchemaField(field_id="error_code", label="Fehlermeldung / Code", field_type=FieldType.TEXT, required=True, placeholder="z. B. ERR_EXPORT_01", order=3),
                    SchemaField(field_id="database_dump_provided", label="Datenbank-Backup im Fallordner abgelegt?", field_type=FieldType.BOOLEAN, required=True, order=4),
                ],
            ),
            QuestionSchema(
                schema_id="schema_abrechnungskorrektur",
                display_name="Allgemeine Abrechnungskorrektur",
                description="Für Korrekturdateien und KV-Abrechnungs-Support.",
                default_suggested_exports=["cobra_note"],
                fields=[
                    SchemaField(field_id="kv_region", label="KV-Region", field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="correction_reason", label="Korrekturgrund", field_type=FieldType.TEXT, required=True, order=2),
                ],
            ),
            QuestionSchema(
                schema_id="schema_bug_report",
                display_name="Programmfehler / Bug-Report",
                description="Zur Weiterleitung ungeklärter Abstürze an die Entwicklungsabteilung.",
                default_suggested_exports=["gitlab_dev_ticket"],
                fields=[
                    SchemaField(field_id="module_name", label="Betroffenes Modul", field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="reproduction_steps", label="Schritte zur Reproduktion", field_type=FieldType.TEXT, required=True, order=2),
                    SchemaField(field_id="stack_trace", label="Stack-Trace / Logauszug", field_type=FieldType.TEXT, required=False, order=3),
                ],
            ),
        ]

    def create_seed_templates(self) -> list[ExportTemplate]:
        return [
            ExportTemplate(
                template_id="gitlab_dev_ticket",
                display_name="GitLab / Dev-Ticket: DB-Korrektur",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_zuzahlungsnachforderung", "schema_bug_report"],
                description="Erzeugt formatierten Markdown-Text für ein neues Entwickler-Ticket im Issue-Tracker.",
                required_schema_fields=["billing_quarter", "error_code", "database_dump_provided"],
                template_string=(
                    "### Support-Übergabe: {{ customer.practice_name }} ({{ customer.customer_id }})\n"
                    "**VIP-Status:** {{ 'JA' if customer.is_vip else 'NEIN' }}\n"
                    "**Rückruf-Deadline:** {{ classification.deadline_callback }}\n\n"
                    "#### Technische Parameter\n"
                    "* **Quartal:** {{ form_data.billing_quarter }}\n"
                    "* **Fehlercode:** {{ form_data.error_code }}\n"
                    "* **DB-Dump:** {{ 'Vorhanden im Ordner ' ~ attachment_directory if form_data.database_dump_provided else '[FEHLT: DB-Dump]' }}\n\n"
                    "#### Letzte Notiz\n"
                    "{{ timeline[-1].note if timeline else 'Keine Notiz vorhanden' }}\n\n"
                    "*Erfasst durch Support: {{ created_by }}*"
                ),
            ),
            ExportTemplate(
                template_id="cobra_note",
                display_name="Cobra CRM Notiz / Übergabe",
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_abrechnungskorrektur", "schema_zuzahlungsnachforderung"],
                description="Formatierter Text für den Eintrag in die Cobra CRM Kundenhistorie.",
                required_schema_fields=["billing_quarter"],
                template_string=(
                    "SUPPORT-HISTORIE - {{ case.case_id }}\n"
                    "Praxis: {{ customer.practice_name }}\n"
                    "Ansprechpartner: {{ customer.contact_person }} ({{ customer.phone }})\n"
                    "Status: {{ workflow_status.board_column }} / Bearbeiter: {{ workflow_status.current_actor }}\n"
                    "Notiz: {{ timeline[-1].note if timeline else '' }}"
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
                    is_data_complete=False,
                ),
                form_data={
                    "billing_quarter": "2026-Q2",
                    "affected_patients_count": 14,
                    "error_code": "ERR_DB_EXPORT_902",
                    "database_dump_provided": False,
                },
                missing_required_fields=["database_dump_provided"],
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
                ),
                workflow_status=WorkflowStatus(
                    is_completed=False,
                    is_archived=False,
                    board_column=BoardColumn.ACTION_REQUIRED,
                    current_actor=Actor.SUPPORT,
                    actor_since="2026-08-23T14:00:00",
                    is_data_complete=False,
                ),
                form_data={"billing_quarter": "2026-Q3", "error_code": "ERR_EXPORT_99"},
                missing_required_fields=["database_dump_provided"],
                attachment_directory="attachments/T-2026-0008_Zahnarztpraxis_Schmidt/",
                timeline=[TimelineEntry(timestamp="2026-08-23T14:00:00", author="Daniel Rösch", note="Neu erfasst")],
            ),
        ]

        # Update scoring on all cases
        for c in cases:
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
            Colleague(username="mmueller", name="Max Müller", extension="245", email="m.mueller@softwarehersteller.de", cases_path=str(self.config.workspace_dir / "colleagues" / "mmueller_cases.json"))
        ]
        self.storage.save_colleagues(colleagues)

        self.create_seed_wiki_db()

        return {
            "customers": len(customers),
            "schemas": len(schemas),
            "templates": len(templates),
            "cases": len(cases),
        }
