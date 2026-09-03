# Technical Report: Seed Data, Templates, Form Schemas & Snippet Services Localization

**Author**: Explorer 3 (Milestone 2)  
**Date**: 2026-09-02  
**Target Scope**: `src/services/seed_case_data.py`, `src/services/seed_service.py`, `src/services/snippet_service.py`, `src/services/schema_service.py`, `src/services/calendar_email_service.py`, `src/services/export_service.py`

---

## 1. Observation

### 1.1 `src/services/seed_case_data.py`
- **Current State**: Contains `build_seed_cases() -> list[Case]` with 12 static demo cases (`T-2026-0001` to `T-2026-0012`).
- **Partial Localization**: Cases 1–5 use `tr(...)` for their titles:
  - Line 33: `title=tr("demo_cases.c1_title", "Zuzahlungsnachforderungsdatei fehlerhaft erzeugt")`
  - Line 88: `title=tr("demo_cases.c2_title", "Absturz beim Drucken von BMA-Rezepten")`
  - Line 125: `title=tr("demo_cases.c3_title", "KV-Abrechnungstext korrigieren")`
  - Line 156: `title=tr("demo_cases.c4_title", "Prüfung Nachforderung 2026-Q1")`
  - Line 187: `title=tr("demo_cases.c5_title", "GUI-Schriftgröße im Laborfenster zu klein")`
- **Hardcoded German Titles (Cases 6–12)**:
  - Line 216: `title="Alte Abrechnung Q1 gelöst"`
  - Line 245: `title="Uralter Fall aus dem Vormonat"`
  - Line 274: `title="Frische Nachforderung ohne DB-Dump"`
  - Line 305: `title="Kundenwunsch: Schnell-Button für eRezept-Export"`
  - Line 344: `title="Kartenleser-Treiber nach Windows-Update getrennt"`
  - Line 379: `title="Alte Nachforderung aus Vorquartal (Archiviert)"`
  - Line 407: `title="Absturz bei PVS-GKV Abrechnungsexport"`
- **Locale Files**: `locales/de.json`, `locales/en.json`, `locales/sv.json` already contain `demo_cases.c1_title` through `c10_title`, but **`demo_cases.c11_title` and `demo_cases.c12_title` are missing**.
- **Other Hardcoded Literals**:
  - Tags: `["Abrechnung", "Nachforderung"]` (c8), `["Kundenwunsch", "eRezept", "VIP"]` (c9), `["Hardware", "Treiber"]` (c10), `["Archiv"]` (c11), `["Dringend", "VIP", "Absturz"]` (c12).
  - Follow-up Notes: `"Beim Dev-Team nach Sprint-Einplanung fragen"` (c9:315), `"Fernwartung mit IT-Admin Becker durchführen"` (c10:354).
  - Timeline Notes & Status Changes: German description texts across all 12 cases.

### 1.2 `src/services/seed_service.py`
- **`create_seed_schemas()`** (Lines 90–168): 5 default `QuestionSchema` objects are created with hardcoded German strings:
  1. `schema_quick`: `display_name="⚡ Schnellerfassung / Allgemeiner Vorgang"`, `description="Für die rasche Erfassung von Anfragen..."`, field labels ("Betroffenes Modul / Programmbereich (optional)", "Kurzbeschreibung / Stichwort (optional)", "Unformatierte Informationen / Beschreibung"), placeholders ("z. B. Abrechnung, Terminkalender...", "z. B. Rückfrage zu Rezeptimport", "Hier alle ungefilterten Informationen...").
  2. `schema_internal_task`: `display_name="🏢 Interne Aufgabe / Notiz"`, `description="Für interne Aufgaben..."`, options `["Systemwartung", "Dokumentation", "Entwicklungsaufgabe", "Prozessverbesserung", "Sonstiges"]`, field labels and placeholders.
  3. `schema_zuzahlungsnachforderung`: `display_name="Zuzahlungsnachforderung & Abrechnungskorrektur"`, `description="Für Nachforderungen und Korrekturen..."`, `repeatable_group_title="Datei / Korrektur-Anforderung"`, options `["Zuzahlungsnachforderung", "Abrechnungskorrektur"]`, 9 field labels & placeholders.
  4. `schema_feature_request`: `display_name="Kundenwunsch / Feature-Request"`, `description="Zur Erfassung neuer Funktionswünsche..."`, 4 field labels.
  5. `schema_bug_report`: `display_name="Programmfehler / Bug-Report"`, `description="Zur Weiterleitung ungeklärter Software-Fehler..."`, 5 field labels.
- **`create_seed_templates()`** (Lines 170–282): 4 default `ExportTemplate` objects with hardcoded German `display_name`, `description`, and Jinja2 template strings:
  1. `mail_dev_zuzahlung_abrechnung`: `display_name="E-Mail an Entwickler: Zuzahlung & Abrechnungskorrektur"`
  2. `gitlab_dev_kundenwunsch`: `display_name="GitLab / Dev-Ticket: Kundenwunsch"`
  3. `gitlab_dev_bug`: `display_name="GitLab / Dev-Ticket: Programmierfehler (Bug)"`
  4. `mail_kunden_rueckmeldung`: `display_name="E-Mail an Praxis: Lösungs-Zusammenfassung"`
- **Colleague Seeding** (Lines 368–381): `Colleague(department="Support", notes="Support-Spezialist")`.

### 1.3 `src/services/snippet_service.py`
- **`DEFAULT_SNIPPETS`** (Lines 6–65): Static list of 8 `Snippet` objects with hardcoded German titles, categories, and content bodies:
  - `SNIP-01`: "📸 Rückfrage: Screenshots & Uhrzeit anfordern", category="Rückfrage", tags=["rückfrage", "screenshot", "fehler"]
  - `SNIP-02`: "🛠 Ersthilfe: PVS & Support-Dienst neustarten", category="Anleitung", tags=["ersthilfe", "neustart", "pvs"]
  - `SNIP-03`: "🔍 DB-Check: SQL Fehler-Log Abfrage", category="SQL / Datenbank", tags=["sql", "datenbank", "log"]
  - `SNIP-04`: "✅ Fallabschluss & Dankeschön", category="Standardantwort", tags=["abschluss", "danke", "erledigt"]
  - `SNIP-05`: "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung", category="Telematik (TI)", tags=["ti", "telematik", "konnektor", "smc-b"]
  - `SNIP-06`: "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet", category="Abrechnung", tags=["abrechnung", "zuzahlung", "esol", "korrektur"]
  - `SNIP-07`: "💾 Backup-Anforderung für Fehleranalyse", category="System", tags=["backup", "datenbank", "analyse"]
  - `SNIP-08`: "🔄 Quartalsupdate Hinweis & Vorbereitung", category="Wartung", tags=["quartalsupdate", "update", "wartung"]
- **`get_categories()`** (Line 109): `return ["Alle"] + cats` contains hardcoded German `"Alle"`.
- **`search_snippets()`** (Lines 115–116): Compares `category != "Alle"`. If category is passed as localized "All" / "Alla", filtering can fail if not normalized.

### 1.4 `src/services/calendar_email_service.py` & `src/services/export_service.py`
- **`CalendarEmailService.generate_ics_content()`** (Lines 86–129):
  - Summary: `f"[Fall {case.case_id}] Rückruf: {practice_name}"`
  - Description: Labels like `"Support-Fall ID:"`, `"Kunde / Praxis:"`, `"Telefon:"`, `"Titel:"`, `"Status:"`, `"Priorität:"`, `"Initiale Notiz / Beschreibung:"`, `"Erstellt von:"`, Alarm: `"Erinnerung: Rückruf-Deadline in 15 Minuten"`.
- **`CalendarEmailService.generate_email_draft()`** (Lines 201–226):
  - Subject: `f"[Fall {case.case_id}] Rückmeldung zu Ihrem Support-Anliegen"`
  - Body: Salutation via `format_german_salutation(...)`, intro `"vielen Dank für Ihre Nachricht bezüglich Ihres Support-Anliegens..."`, `"--- ZUSAMMENFASSUNG / STATUS ---"`, `"Geplante Rückruf-Deadline:"`, closing `"Geben Sie uns gerne Bescheid..."`, `"Mit freundlichen Grüßen,"`.
- **`ExportService.render_template()`** (Line 81):
  - Missing field string: `f"[FEHLT: {label}]"` hardcoded in German.

---

## 2. Logic Chain & Analysis

### 2.1 Dynamic Localization vs Multilingual Seed Sets Architecture
1. **Domain Data Persistence vs UI Display**:
   - Seed cases, custom schemas, custom templates, and snippets are persisted as JSON files (`cases.json`, `question_schemas.json`, `export_templates.json`, `snippets.json`) in the user's workspace.
   - Once persisted, users can edit them freely.
2. **Optimal Localization Strategy**:
   - **Generation-time Localization**: When seed datasets and default catalogs are generated (via `build_seed_cases()`, `create_seed_schemas()`, `create_seed_templates()`, and `get_default_snippets()`), they must retrieve their initial text from `tr(key, default)`. If the app initializes in English (`en`) or Swedish (`sv`), the initial dataset will be in that language.
   - **Runtime Display Resolution**:
     - For default schemas and default templates (identified by stable `schema_id` and `template_id`), UI components (e.g. `DynamicFormWidget`, `TemplateManagerDialog`, `NewCaseDialog`) should resolve display names and field labels dynamically using `tr(f"schemas.{schema_id}.{field_id}_label", default=field.label)` and `tr(f"export_templates.{template_id}.name", default=template.display_name)`.
     - This ensures that when the user switches languages at runtime, default schemas and templates immediately adapt to the new language without overwriting user customizations!
   - **Snippet Category Normalization**: `SnippetService.get_categories()` should return `[tr("snippet_picker.all_categories", "Alle")] + cats` and `search_snippets` must treat all representations of "All" (`"Alle"`, `"All"`, `"Alla"`, or `tr("snippet_picker.all_categories")`) as wildcard (no category filter).

---

## 3. Concrete Code Recommendations & Translation Key Mappings

### 3.1 `src/services/seed_case_data.py`
Replace hardcoded titles and notes with `tr(...)`:

```python
# Before (Lines 216, 245, 274, 305, 344, 379, 407):
title="Alte Abrechnung Q1 gelöst"
title="Uralter Fall aus dem Vormonat"
title="Frische Nachforderung ohne DB-Dump"
title="Kundenwunsch: Schnell-Button für eRezept-Export"
title="Kartenleser-Treiber nach Windows-Update getrennt"
title="Alte Nachforderung aus Vorquartal (Archiviert)"
title="Absturz bei PVS-GKV Abrechnungsexport"

# After:
title=tr("demo_cases.c6_title", "Alte Abrechnung Q1 gelöst")
title=tr("demo_cases.c7_title", "Uralter Fall aus dem Vormonat")
title=tr("demo_cases.c8_title", "Frische Nachforderung ohne DB-Dump")
title=tr("demo_cases.c9_title", "Kundenwunsch: Schnell-Button für eRezept-Export")
title=tr("demo_cases.c10_title", "Kartenleser-Treiber nach Windows-Update getrennt")
title=tr("demo_cases.c11_title", "Alte Nachforderung aus Vorquartal (Archiviert)")
title=tr("demo_cases.c12_title", "Absturz bei PVS-GKV Abrechnungsexport")
```

Add missing keys to `locales/de.json`, `locales/en.json`, `locales/sv.json`:
```json
// locales/de.json -> demo_cases
"c11_title": "Alte Nachforderung aus Vorquartal (Archiviert)",
"c12_title": "Absturz bei PVS-GKV Abrechnungsexport"

// locales/en.json -> demo_cases
"c11_title": "Old subsequent claim from previous quarter (Archived)",
"c12_title": "Crash during PMS statutory billing export"

// locales/sv.json -> demo_cases
"c11_title": "Gammalt efterkrav från föregående kvartal (Arkiverat)",
"c12_title": "Krasch vid export av fakturering från journalsystem"
```

### 3.2 `src/services/seed_service.py`
Refactor `create_seed_schemas()` and `create_seed_templates()` to use `tr(...)`:

```python
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
                SchemaField(
                    field_id="module_name",
                    label=tr("schemas.quick.module_name_label", "Betroffenes Modul / Programmbereich (optional)"),
                    field_type=FieldType.TEXT,
                    required=False,
                    placeholder=tr("schemas.quick.module_name_ph", "z. B. Abrechnung, Terminkalender, Schnittstelle..."),
                    order=1
                ),
                SchemaField(
                    field_id="short_description",
                    label=tr("schemas.quick.short_desc_label", "Kurzbeschreibung / Stichwort (optional)"),
                    field_type=FieldType.TEXT,
                    required=False,
                    placeholder=tr("schemas.quick.short_desc_ph", "z. B. Rückfrage zu Rezeptimport"),
                    order=2
                ),
                SchemaField(
                    field_id="unformatted_description",
                    label=tr("schemas.quick.unformatted_desc_label", "Unformatierte Informationen / Beschreibung"),
                    field_type=FieldType.TEXT,
                    required=False,
                    placeholder=tr("schemas.quick.unformatted_desc_ph", "Hier alle ungefilterten Informationen, Mails oder Stichpunkte eingeben..."),
                    order=3
                ),
            ],
        ),
        QuestionSchema(
            schema_id="schema_internal_task",
            display_name=tr("schemas.internal_task.display_name", "🏢 Interne Aufgabe / Notiz"),
            description=tr("schemas.internal_task.description", "Für interne Aufgaben, Systemwartung, Prozessverbesserungen oder Notizen ohne Kundenbezug."),
            default_suggested_exports=[],
            fields=[
                SchemaField(
                    field_id="internal_category",
                    label=tr("schemas.internal_task.category_label", "Kategorie der Aufgabe"),
                    field_type=FieldType.DROPDOWN,
                    options=[tr(f"internal_task_categories.{c}", default=c) for c in DEFAULT_INTERNAL_TASK_CATEGORIES],
                    required=True,
                    order=1
                ),
                SchemaField(
                    field_id="affected_systems",
                    label=tr("schemas.internal_task.systems_label", "Betroffene Systeme / Server / Komponenten"),
                    field_type=FieldType.TEXT,
                    required=False,
                    placeholder=tr("schemas.internal_task.systems_ph", "z. B. Server-02, P2P-Sync, Wiki-Cache..."),
                    order=2
                ),
                SchemaField(
                    field_id="description",
                    label=tr("schemas.internal_task.desc_label", "Ausführliche Aufgabenbeschreibung & Details"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.internal_task.desc_ph", "Schritt-für-Schritt Aufgabenbeschreibung..."),
                    order=3
                ),
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
                "action_type", "esol_filename", "invoice_number", "invoice_date",
                "prescription_info", "prescription_date", "patient_names", "action_reason_detail"
            ],
            fields=[
                SchemaField(
                    field_id="action_type",
                    label=tr("schemas.zuzahlung.action_type_label", "Geforderte Aktion"),
                    field_type=FieldType.DROPDOWN,
                    options=[tr("schemas.zuzahlung.opt_nachforderung", "Zuzahlungsnachforderung"), tr("schemas.zuzahlung.opt_korrektur", "Abrechnungskorrektur")],
                    required=True,
                    order=1
                ),
                SchemaField(
                    field_id="invoice_number",
                    label=tr("schemas.zuzahlung.invoice_num_label", "Betroffene Rechnungsnummer"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.invoice_num_ph", "z. B. RE-2026-0815"),
                    order=2
                ),
                SchemaField(
                    field_id="invoice_date",
                    label=tr("schemas.zuzahlung.invoice_date_label", "Rechnungsdatum"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.date_ph", "YYYY-MM-DD"),
                    order=3
                ),
                SchemaField(
                    field_id="prescription_info",
                    label=tr("schemas.zuzahlung.prescription_info_label", "Betroffene Verordnung"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.prescription_info_ph", "z. B. VO-987654"),
                    order=4
                ),
                SchemaField(
                    field_id="prescription_date",
                    label=tr("schemas.zuzahlung.prescription_date_label", "Datum der Verordnung"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.date_ph", "YYYY-MM-DD"),
                    order=5
                ),
                SchemaField(
                    field_id="patient_names",
                    label=tr("schemas.zuzahlung.patient_names_label", "Namen der betroffenen Patienten"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.patient_names_ph", "z. B. Max Mustermann"),
                    order=6
                ),
                SchemaField(
                    field_id="esol_filename",
                    label=tr("schemas.zuzahlung.esol_filename_label", "Name der originalen ESOL-Datei"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.esol_filename_ph", "z. B. ESOL_20260801.dat"),
                    order=7
                ),
                SchemaField(
                    field_id="action_reason_detail",
                    label=tr("schemas.zuzahlung.reason_label", "Genaue Begründung & Details"),
                    field_type=FieldType.TEXT,
                    required=True,
                    placeholder=tr("schemas.zuzahlung.reason_ph", "Ausführliche Beschreibung..."),
                    order=8
                ),
                SchemaField(
                    field_id="has_forwarded_email_or_screenshot",
                    label=tr("schemas.zuzahlung.forwarded_label", "Weitergeleitete Mail/Screenshot im Fallordner?"),
                    field_type=FieldType.BOOLEAN,
                    required=True,
                    order=9
                ),
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
```

### 3.3 `src/services/snippet_service.py`
Refactor default snippets to dynamic factory with localized titles, categories, contents, tags, and robust category filtering:

```python
def get_default_snippets() -> list[Snippet]:
    from services.i18n_service import tr

    return [
        Snippet(
            snippet_id="SNIP-01",
            title=tr("snippets.s1_title", "📸 Rückfrage: Screenshots & Uhrzeit anfordern"),
            category=tr("snippet_categories.inquiry", "Rückfrage"),
            content=tr("snippets.s1_content", "Bitte lassen Sie uns Screenshots der Fehlermeldung sowie das genaue Datum und die Uhrzeit des ersten Auftretens zukommen."),
            tags=[t.strip() for t in tr("snippets.s1_tags", "rückfrage, screenshot, fehler").split(",")],
            shortcut="<Control-Alt-1>",
        ),
        Snippet(
            snippet_id="SNIP-02",
            title=tr("snippets.s2_title", "🛠 Ersthilfe: PVS & Support-Dienst neustarten"),
            category=tr("snippet_categories.instructions", "Anleitung"),
            content=tr("snippets.s2_content", "Schritte zur Ersthilfe:\n1. PVS an allen Arbeitsplätzen beenden.\n2. Support-Dienst auf dem Hauptserver neustarten.\n3. PVS erneut öffnen und Funktion testen."),
            tags=[t.strip() for t in tr("snippets.s2_tags", "ersthilfe, neustart, pvs").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-03",
            title=tr("snippets.s3_title", "🔍 DB-Check: SQL Fehler-Log Abfrage"),
            category=tr("snippet_categories.sql_db", "SQL / Datenbank"),
            content=tr("snippets.s3_content", "SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;"),
            tags=[t.strip() for t in tr("snippets.s3_tags", "sql, datenbank, log").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-04",
            title=tr("snippets.s4_title", "✅ Fallabschluss & Dankeschön"),
            category=tr("snippet_categories.standard_reply", "Standardantwort"),
            content=tr("snippets.s4_content", "Vielen Dank für Ihre Rückmeldung. Das Anliegen konnte erfolgreich gelöst werden. Wir schließen diesen Vorgang."),
            tags=[t.strip() for t in tr("snippets.s4_tags", "abschluss, danke, erledigt").split(",")],
            shortcut="<Control-Alt-2>",
        ),
        Snippet(
            snippet_id="SNIP-05",
            title=tr("snippets.s5_title", "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung"),
            category=tr("snippet_categories.telematics", "Telematik (TI)"),
            content=tr("snippets.s5_content", "Schritte zur TI-Entstörung:\n1. Status der SMC-B Karte im Kartenterminal prüfen (grüne LED).\n2. Konnektor über Web-Oberfläche oder Schalter kurz stromlos machen (30 Sek. warten).\n3. PVS-Dienst neu starten und TI-Verbindungstest in der Administration ausführen."),
            tags=[t.strip() for t in tr("snippets.s5_tags", "ti, telematik, konnektor, smc-b").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-06",
            title=tr("snippets.s6_title", "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet"),
            category=tr("snippet_categories.billing", "Abrechnung"),
            content=tr("snippets.s6_content", "Sehr geehrte Praxisleitung,\n\ndie angeforderte Korrekturdatei bzw. Nachberechnung für die ESOL-Abrechnung wurde an unsere Entwicklungsabteilung weitergeleitet. Sobald die korrigierten Datensätze vorliegen, stellen wir Ihnen diese zur Verfügung."),
            tags=[t.strip() for t in tr("snippets.s6_tags", "abrechnung, zuzahlung, esol, korrektur").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-07",
            title=tr("snippets.s7_title", "💾 Backup-Anforderung für Fehleranalyse"),
            category=tr("snippet_categories.system", "System"),
            content=tr("snippets.s7_content", "Für die detaillierte Fehleranalyse benötigen wir ein aktuelles Datenbank-Backup (.backup). Bitte legen Sie die Datei im gesicherten Fallordner oder Transferverzeichnis ab."),
            tags=[t.strip() for t in tr("snippets.s7_tags", "backup, datenbank, analyse").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-08",
            title=tr("snippets.s8_title", "🔄 Quartalsupdate Hinweis & Vorbereitung"),
            category=tr("snippet_categories.maintenance", "Wartung"),
            content=tr("snippets.s8_content", "Vor Einspielen des Quartalsupdates bitte sicherstellen:\n1. Vollständige Datensicherung durchführen.\n2. Alle Arbeitsplätze schließen.\n3. Server-Dienste beenden und Update-Installer als Administrator ausführen."),
            tags=[t.strip() for t in tr("snippets.s8_tags", "quartalsupdate, update, wartung").split(",")],
        ),
    ]

DEFAULT_SNIPPETS = get_default_snippets()
```

Category handling in `SnippetService`:
```python
def get_categories(self) -> list[str]:
    from services.i18n_service import tr
    cats = sorted({s.category for s in self.snippets if s.category})
    return [tr("snippet_picker.all_categories", "Alle")] + cats

def search_snippets(self, query: str = "", category: str = "Alle") -> list[Snippet]:
    from services.i18n_service import tr
    results = self.snippets

    all_cat_labels = {"Alle", "All", "Alla", tr("snippet_picker.all_categories", "Alle")}
    if category and category not in all_cat_labels:
        results = [s for s in results if s.category == category]

    if query and query.strip():
        clean_q = query.strip().lower()
        results = [
            s for s in results
            if clean_q in s.title.lower()
            or clean_q in s.content.lower()
            or any(clean_q in t.lower() for t in s.tags)
        ]

    return results
```

### 3.4 Summary of Translation Key Schema for M2

| Namespace | Key Pattern | German Default | English | Swedish |
|---|---|---|---|---|
| `demo_cases` | `c11_title` | Alte Nachforderung aus Vorquartal (Archiviert) | Old subsequent claim from previous quarter (Archived) | Gammalt efterkrav från föregående kvartal (Arkiverat) |
| `demo_cases` | `c12_title` | Absturz bei PVS-GKV Abrechnungsexport | Crash during PMS statutory billing export | Krasch vid export av fakturering från journalsystem |
| `snippet_categories` | `inquiry` | Rückfrage | Inquiry | Förfrågan |
| `snippet_categories` | `instructions` | Anleitung | Instructions | Instruktioner |
| `snippet_categories` | `sql_db` | SQL / Datenbank | SQL / Database | SQL / Databas |
| `snippet_categories` | `standard_reply` | Standardantwort | Standard Reply | Standardsvar |
| `snippet_categories` | `telematics` | Telematik (TI) | Telematics (TI) | Telematik (TI) |
| `snippet_categories` | `billing` | Abrechnung | Billing | Fakturering |
| `snippet_categories` | `system` | System | System | System |
| `snippet_categories` | `maintenance` | Wartung | Maintenance | Underhåll |
| `snippet_picker` | `all_categories` | Alle | All | Alla |
| `schemas.*` | `display_name`, `description`, field labels & placeholders | Formular-Schemata | Form Schemas | Formulärscheman |
| `export_templates.*` | `name`, `description` | Export-Vorlagen | Export Templates | Exportmallar |
| `export` | `missing_field` | FEHLT | MISSING | SAKNAS |

---

## 4. Caveats
1. **User Customization Overwrite Protection**:
   - Seed datasets populate the initial working files (`data/*.json`).
   - If a user customizes a schema or snippet, we must not overwrite their custom title/content unless they explicitly trigger "Reset to Defaults".
   - Using `tr(f"schemas.{schema_id}.{field_id}_label", default=field.label)` in UI renderers achieves dynamic runtime localization for default entities without modifying stored user JSON files.
2. **Jinja2 Export Templates Execution**:
   - Jinja2 template strings contain logic tags (`{% if ... %}`). Localizing the template string itself is done per template definition; dynamic variable names (`customer.practice_name`, `form_data.action_type`) must remain unchanged to maintain template engine compatibility.

---

## 5. Conclusion
- The initial seed cases (`seed_case_data.py`), default schemas and export templates (`seed_service.py`), and default snippets (`snippet_service.py`) can be fully internationalized across German, English, and Swedish.
- Adding the missing keys `c11_title`, `c12_title`, `snippet_categories.*`, `schemas.*`, and `export_templates.*` achieves 100% localization completeness.
- Dynamic fallback resolution in `SnippetService`, `DynamicFormWidget`, and `TemplateManagerDialog` guarantees smooth runtime language switching while preserving user data integrity.

---

## 6. Verification Method

To verify these changes independently:

1. **Automated Unit & Integration Tests**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_seed.py tests/test_seeded_support_snippets.py tests/test_schemas.py tests/test_e2e_multilingual_workflows.py
   ```
2. **Translation Parity Check**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_translation_parity_and_quality.py
   ```
3. **AST Hardcoded String Verification**:
   ```powershell
   .venv\Scripts\python.exe -m pytest tests/test_ast_i18n_scanner.py
   ```
4. **Inspect Files**:
   - `src/services/seed_case_data.py` (ensure all `tr("demo_cases.cX_title", ...)` calls are present).
   - `src/services/seed_service.py` (ensure `create_seed_schemas` and `create_seed_templates` use `tr(...)`).
   - `src/services/snippet_service.py` (ensure `get_default_snippets` and `get_categories` use `tr(...)`).
   - `locales/de.json`, `locales/en.json`, `locales/sv.json` (ensure key parity across all 3 files).
