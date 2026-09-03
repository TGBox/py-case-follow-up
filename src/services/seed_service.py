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
from services.seed_case_data import build_seed_cases


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
        from services.i18n_service import tr
        from constants import DEFAULT_INTERNAL_TASK_CATEGORIES

        return [
            QuestionSchema(
                schema_id="schema_quick",
                display_name=tr("schemas.quick.display_name", "⚡ Schnellerfassung / Allgemeiner Vorgang"),
                description=tr("schemas.quick.description", "Für die rasche Erfassung von Anfragen und Problemen ohne detaillierte Vorab-Spezifizierung."),
                default_suggested_exports=["mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label=tr("schemas.quick.module_name_label", "Betroffenes Modul / Programmbereich (optional)"), field_type=FieldType.TEXT, required=False, placeholder=tr("schemas.quick.module_name_ph", "z. B. Abrechnung, Terminkalender, Schnittstelle..."), order=1),
                    SchemaField(field_id="short_description", label=tr("schemas.quick.short_desc_label", "Kurzbeschreibung / Stichwort (optional)"), field_type=FieldType.TEXT, required=False, placeholder=tr("schemas.quick.short_desc_ph", "z. B. Rückfrage zu Rezeptimport"), order=2),
                    SchemaField(field_id="unformatted_description", label=tr("schemas.quick.unformatted_desc_label", "Unformatierte Informationen / Beschreibung"), field_type=FieldType.TEXT, required=False, placeholder=tr("schemas.quick.unformatted_desc_ph", "Hier alle ungefilterten Informationen, Mails oder Stichpunkte eingeben..."), order=3),
                ],
            ),
            QuestionSchema(
                schema_id="schema_internal_task",
                display_name=tr("schemas.internal_task.display_name", "🏢 Interne Aufgabe / Notiz"),
                description=tr("schemas.internal_task.description", "Für interne Aufgaben, Systemwartung, Prozessverbesserungen oder Notizen ohne Kundenbezug."),
                default_suggested_exports=[],
                fields=[
                    SchemaField(field_id="internal_category", label=tr("schemas.internal_task.category_label", "Kategorie der Aufgabe"), field_type=FieldType.DROPDOWN, options=[tr(f"internal_task_categories.{c}", default=c) for c in DEFAULT_INTERNAL_TASK_CATEGORIES], required=True, order=1),
                    SchemaField(field_id="affected_systems", label=tr("schemas.internal_task.systems_label", "Betroffene Systeme / Server / Komponenten"), field_type=FieldType.TEXT, required=False, placeholder=tr("schemas.internal_task.systems_ph", "z. B. Server-02, P2P-Sync, Wiki-Cache..."), order=2),
                    SchemaField(field_id="description", label=tr("schemas.internal_task.desc_label", "Ausführliche Aufgabenbeschreibung & Details"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.internal_task.desc_ph", "Schritt-für-Schritt Aufgabenbeschreibung..."), order=3),
                ],
            ),
            QuestionSchema(
                schema_id="schema_zuzahlungsnachforderung",
                display_name=tr("schemas.zuzahlung.display_name", "Zuzahlungsnachforderung & Abrechnungskorrektur"),
                description=tr("schemas.zuzahlung.description", "Für Nachforderungen und Korrekturen gegenüber Abrechnungszentrum, Krankenkasse oder KV."),
                default_suggested_exports=["mail_dev_zuzahlung_abrechnung", "mail_kunden_rueckmeldung"],
                is_repeatable_group=True,
                repeatable_group_title=tr("schemas.zuzahlung.repeatable_title", "Datei / Korrektur-Anforderung"),
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
                    SchemaField(field_id="action_type", label=tr("schemas.zuzahlung.action_type_label", "Geforderte Aktion"), field_type=FieldType.DROPDOWN, options=[tr("schemas.zuzahlung.opt_nachforderung", "Zuzahlungsnachforderung"), tr("schemas.zuzahlung.opt_korrektur", "Abrechnungskorrektur")], required=True, order=1),
                    SchemaField(field_id="invoice_number", label=tr("schemas.zuzahlung.invoice_num_label", "Betroffene Rechnungsnummer"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.invoice_num_ph", "z. B. RE-2026-0815"), order=2),
                    SchemaField(field_id="invoice_date", label=tr("schemas.zuzahlung.invoice_date_label", "Rechnungsdatum"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.date_ph", "YYYY-MM-DD"), order=3),
                    SchemaField(field_id="prescription_info", label=tr("schemas.zuzahlung.prescription_info_label", "Betroffene Verordnung"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.prescription_info_ph", "z. B. VO-987654"), order=4),
                    SchemaField(field_id="prescription_date", label=tr("schemas.zuzahlung.prescription_date_label", "Datum der Verordnung"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.date_ph", "YYYY-MM-DD"), order=5),
                    SchemaField(field_id="patient_names", label=tr("schemas.zuzahlung.patient_names_label", "Namen der betroffenen Patienten"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.patient_names_ph", "z. B. Max Mustermann"), order=6),
                    SchemaField(field_id="esol_filename", label=tr("schemas.zuzahlung.esol_filename_label", "Name der originalen ESOL-Datei"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.esol_filename_ph", "z. B. ESOL_20260801.dat"), order=7),
                    SchemaField(field_id="action_reason_detail", label=tr("schemas.zuzahlung.reason_label", "Genaue Begründung & Details"), field_type=FieldType.TEXT, required=True, placeholder=tr("schemas.zuzahlung.reason_ph", "Ausführliche Beschreibung..."), order=8),
                    SchemaField(field_id="has_forwarded_email_or_screenshot", label=tr("schemas.zuzahlung.forwarded_label", "Weitergeleitete Mail/Screenshot im Fallordner?"), field_type=FieldType.BOOLEAN, required=True, order=9),
                ],
            ),
            QuestionSchema(
                schema_id="schema_feature_request",
                display_name=tr("schemas.feature_request.display_name", "Kundenwunsch / Feature-Request"),
                description=tr("schemas.feature_request.description", "Zur Erfassung neuer Funktionswünsche von Praxen für die Entwicklungsabteilung."),
                default_suggested_exports=["gitlab_dev_kundenwunsch", "mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label=tr("schemas.feature_request.module_label", "Betroffenes Modul / Programmbereich"), field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="feature_description", label=tr("schemas.feature_request.desc_label", "Beschreibung des Kundenwunsches"), field_type=FieldType.TEXT, required=True, order=2),
                    SchemaField(field_id="practice_benefit", label=tr("schemas.feature_request.benefit_label", "Gewünschter Nutzen / Ziel für die Praxis"), field_type=FieldType.TEXT, required=True, order=3),
                    SchemaField(field_id="has_mockup_or_screenshot", label=tr("schemas.feature_request.mockup_label", "Screenshot/Skizze im Fallordner?"), field_type=FieldType.BOOLEAN, required=False, order=4),
                ],
            ),
            QuestionSchema(
                schema_id="schema_bug_report",
                display_name=tr("schemas.bug_report.display_name", "Programmfehler / Bug-Report"),
                description=tr("schemas.bug_report.description", "Zur Weiterleitung ungeklärter Software-Fehler an die Entwicklungsabteilung."),
                default_suggested_exports=["gitlab_dev_bug", "mail_kunden_rueckmeldung"],
                fields=[
                    SchemaField(field_id="module_name", label=tr("schemas.bug_report.module_label", "Betroffenes Modul"), field_type=FieldType.TEXT, required=True, order=1),
                    SchemaField(field_id="error_message", label=tr("schemas.bug_report.error_msg_label", "Fehlermeldung / Code"), field_type=FieldType.TEXT, required=True, order=2),
                    SchemaField(field_id="reproduction_steps", label=tr("schemas.bug_report.repro_steps_label", "Schritte zur Reproduktion"), field_type=FieldType.TEXT, required=True, order=3),
                    SchemaField(field_id="stack_trace", label=tr("schemas.bug_report.stack_trace_label", "Stack-Trace / Logauszug"), field_type=FieldType.TEXT, required=False, order=4),
                    SchemaField(field_id="database_dump_provided", label=tr("schemas.bug_report.db_dump_label", "Datenbank-Backup im Fallordner abgelegt?"), field_type=FieldType.BOOLEAN, required=True, order=5),
                ],
            ),
        ]

    def create_seed_templates(self) -> list[ExportTemplate]:
        from services.i18n_service import tr

        return [
            ExportTemplate(
                template_id="mail_dev_zuzahlung_abrechnung",
                display_name=tr("export_templates.mail_dev_zuzahlung_abrechnung_name", "E-Mail an Entwickler: Zuzahlung & Abrechnungskorrektur"),
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_zuzahlungsnachforderung"],
                description=tr("export_templates.mail_dev_zuzahlung_abrechnung_desc", "Erzeugt eine vollständige E-Mail an das Entwicklerteam zur Nachberechnung oder Abrechnungskorrektur mit allen Pflichtdaten."),
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
                display_name=tr("export_templates.gitlab_dev_kundenwunsch_name", "GitLab / Dev-Ticket: Kundenwunsch"),
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_feature_request"],
                description=tr("export_templates.gitlab_dev_kundenwunsch_desc", "Formatiertes Markdown-Ticket für neue Funktionswünsche an die Entwicklungsabteilung."),
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
                display_name=tr("export_templates.gitlab_dev_bug_name", "GitLab / Dev-Ticket: Programmierfehler (Bug)"),
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_bug_report"],
                description=tr("export_templates.gitlab_dev_bug_desc", "Entwickler-Ticket für Softwarefehler, Abstürze und Schnittstellenprobleme."),
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
                display_name=tr("export_templates.mail_kunden_rueckmeldung_name", "E-Mail an Praxis: Lösungs-Zusammenfassung"),
                target_type=TargetType.CLIPBOARD_TEXT,
                applicable_cases=["schema_zuzahlungsnachforderung", "schema_feature_request", "schema_bug_report"],
                description=tr("export_templates.mail_kunden_rueckmeldung_desc", "Kunden-E-Mail mit Zusammenfassung der Lösung und Kontaktdaten."),
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
        cases = build_seed_cases()

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
        self.storage.flush_all_saves()

        return {
            "customers": len(customers),
            "schemas": len(schemas),
            "templates": len(templates),
            "cases": len(cases),
        }
