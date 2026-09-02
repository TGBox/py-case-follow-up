import json
import sys
from pathlib import Path

src_path = Path("src").resolve()
sys.path.insert(0, str(src_path))

from ui.dialogs.help_dialog import HELP_ARTICLES

en_articles = {
    "basics": {
        "title": "🚀 Basics & Layouts",
        "category": "Basics",
        "content": """### 🚀 User Interface Basics

The **Support Cockpit** assists you in efficiently tracking, categorizing, and prioritizing support cases and medical practice requests.

#### The 4 Views (Layout Modes)
In the top menu bar, you can switch between 4 views at any time (`Ctrl+1` to `Ctrl+4`):

1. **Cockpit View (Default, `Ctrl+1`)**:
   - Tri-pane main layout with case list, case details/form, and BookStack wiki.

2. **Kanban Board (`Ctrl+2`)**:
   - Board view organized by columns & responsibilities (*New*, *Action Required*, *Waiting*, *In Progress*, *Completed*).

3. **Table & Details (`Ctrl+3`)**:
   - Tabular matrix showing case details for a compact overview, sorting, and filtering.

4. **Analytics & Metrics (`Ctrl+4`)**:
   - Full statistics dashboard showing resolution times, overdue deadlines, VIP ratios, and report exports.

---

#### 🔍 Search & Filter Function
- Use the search bar at the top of the case list to filter cases by **Case ID**, **Practice Name**, **Subject**, or **Tags**.
- Shortcut to focus search: `Ctrl+F`"""
    },
    "ui_customization": {
        "title": "📅 Date Formats, Calendar & Column Widths",
        "category": "User Interface",
        "content": """### 📅 Date Formatting, Calendar Picker & Column Widths

#### 1. 📅 Date Formatting
- All dates in the Support Cockpit (deadlines, callbacks, follow-ups, timeline) are displayed consistently in standard date format (`DD.MM.YYYY` or `DD.MM.YYYY HH:MM`).

#### 2. 🗓 Interactive Calendar Picker
- An interactive calendar dialog is available for all date entries (e.g. scheduling follow-ups, setting callback deadlines).
- Click **📅 Calendar** next to the input field to open the monthly calendar and conveniently select the desired date with a click.
- Quick selection buttons for *Today*, *+ 1 Day*, and *+ 1 Week* speed up data entry."""
    },
    "praxis": {
        "title": "🏥 Practice & Customer Management",
        "category": "Customers",
        "content": """### 🏥 Practice & Customer Data Management

#### Central Practice Catalog
- Manage all customer entries centrally under **Stammdaten -> 🏥 Praxen**.
- Practice entries contain contact persons, phone numbers, email addresses, customer numbers, VIP status, and preferred support contacts."""
    },
    "scoring": {
        "title": "📊 Urgency Scoring & Prioritization",
        "category": "Workflow",
        "content": """### 📊 Automatic Urgency Scoring

The Support Cockpit automatically calculates an **Urgency Score** for every open case to help you identify urgent cases immediately."""
    },
    "schemas": {
        "title": "📄 Form Builder & Schemas",
        "category": "Forms",
        "content": """### 📄 Custom Dynamic Forms & Schemas

Create tailored input forms for specific medical device types, software modules, or support scenarios using the built-in Schema Builder."""
    },
    "export": {
        "title": "📤 Export Engine & Templates",
        "category": "Export",
        "content": """### 📤 Export & Handover Assistant

Generate summary reports, emails, or documentation for colleagues or external ticketing systems with a single click."""
    },
    "wiki": {
        "title": "📚 BookStack Wiki Integration",
        "category": "Wiki",
        "content": """### 📚 BookStack Wiki Integration

The Support Cockpit is directly connected to your BookStack Wiki to keep solution articles readily accessible."""
    },
    "p2p": {
        "title": "🔄 Peer-to-Peer Sync (Colleagues)",
        "category": "Sync",
        "content": """### 🔄 Peer-to-Peer (P2P) Synchronization

Collaborate with colleagues without a central server. P2P Sync allows matching case data directly between local workstations."""
    },
    "shortcuts": {
        "title": "⌨ Keyboard Shortcuts & Hotkeys",
        "category": "Shortcuts",
        "content": """### ⌨ Keyboard Shortcuts

- `Ctrl+N`: New Case
- `Ctrl+S`: Save Case
- `Ctrl+E`: Export Case
- `Ctrl+P`: Open Settings
- `Ctrl+1` - `Ctrl+4`: Switch Views
- `F1`: Open Help"""
    },
    "storage_paths": {
        "title": "📁 Storage Locations & File Paths",
        "category": "Configuration",
        "content": """### 📁 Storage Locations & Directory Structure

The Support Cockpit keeps application data separated from workspace files for clean portability and EXE execution."""
    },
    "template_editor": {
        "title": "📄 Export Template Editor",
        "category": "Export",
        "content": """### 📄 Export Template Editor & Live Preview

Customize existing templates or define new export formats with side-by-side live rendering."""
    },
    "handover_followup": {
        "title": "🔔 Case Handovers & Follow-ups",
        "category": "Workflow",
        "content": """### 🔔 Responsibility Handovers & Follow-up Reminders

Reassign cases to colleagues or departments with automated timeline logging and follow-up alerts."""
    },
    "email_calendar_outlook": {
        "title": "✉ Email, Calendar (.ics) & Outlook",
        "category": "Communication",
        "content": """### ✉ Email Drafts, iCalendar & Outlook Integration

Compose customer emails, export `.ics` calendar events, or transfer items directly to Microsoft Outlook."""
    },
    "case_print_reporting": {
        "title": "🖨 Case Print View, PDF & Images",
        "category": "Export",
        "content": """### 🖨 Case File Print & PDF Export

Generate print reports and PDF documents with embedded screenshots and complete timeline histories."""
    },
    "ai_ollama_management": {
        "title": "🤖 AI Assistant, Ollama Server & Model Control",
        "category": "AI & Ollama",
        "content": """### 🤖 Local AI Support Assistant & Ollama Management

100% local, privacy-compliant AI assistance using local Ollama LLMs (Qwen2.5 / Llama3) or Google Gemini Cloud API."""
    },
    "stepper_time_picker": {
        "title": "⏱ Time Selection (07:00-20:00) & Stepper",
        "category": "User Interface",
        "content": """### ⏱ Interactive Time Picker

Optimized time selection for medical practice office hours (07:00 to 20:00) with quick stepper arrows."""
    },
    "internal_cases": {
        "title": "🏢 Internal Cases & Tasks (Non-Customer)",
        "category": "Workflow",
        "content": """### 🏢 Internal Operations & Sub-Tasks

Manage internal IT tasks, server maintenance, or dev notes without requiring a customer assignment."""
    },
    "cobra_crm_import": {
        "title": "🐍 Cobra CRM Practice & Customer Import",
        "category": "Customers",
        "content": """### 🐍 Cobra CRM Import Assistant

Import customer databases directly from Cobra CRM exports (.csv, .txt, .json)."""
    },
    "snippets_manager": {
        "title": "📝 Text Snippets & Macro Manager",
        "category": "Communication",
        "content": """### 📝 Text Snippets & Quick Response Templates

Save time on recurring responses with reusable text snippet macros."""
    },
    "repeatable_sub_forms": {
        "title": "📂 Dynamic Multi-Card Forms",
        "category": "Forms",
        "content": """### 📂 Dynamic Multi-Card Forms & Repeatable Sub-Entries

Capture multiple billing items or claims within a single structured support case."""
    },
    "analytics_kpi_dashboard": {
        "title": "Auswertungs- & KPI-Dashboard",
        "category": "Analytics",
        "content": """### Analytics & KPI Dashboard

Comprehensive statistical overview of workload, average resolution times, VIP rates, and department distribution."""
    },
    "advanced_search_filters": {
        "title": "🔍 Advanced Search & Search Tokens",
        "category": "Basics",
        "content": """### 🔍 Search Tokens & Quick Filters

Filter cases using search tokens like `is:internal`, `vip:true`, `reminder:due`, or `actor:dev`."""
    },
    "attachments_and_screenshots": {
        "title": "📂 File Attachments & Screenshots (Ctrl+V)",
        "category": "Documents",
        "content": """### 📂 Attachment Management & Clipboard Screenshots

Paste screenshots directly into cases with `Ctrl+V` and view file previews."""
    },
    "zip_backup_restore": {
        "title": "📦 Complete ZIP Backup & Restoration",
        "category": "Configuration",
        "content": """### 📦 Full Workspace Backup & Restore

Backup all cases, customers, schemas, templates, and attachments into a compressed ZIP file."""
    },
    "email_webhook_integration": {
        "title": "🔌 Email Import & REST Webhooks (Jira/GitLab)",
        "category": "Integrations",
        "content": """### 🔌 Email IMAP Ingestion & Webhooks

Ingest emails via IMAP and trigger REST webhooks for external tools like GitLab or Jira."""
    }
}

sv_articles = {
    "basics": {
        "title": "🚀 Grundläggande & layouter",
        "category": "Grundläggande",
        "content": """### 🚀 Användargränssnittets grundläggande funktioner

**Support Cockpit** hjälper dig att effektivt spåra, kategorisera och prioritera supportärenden och mottagningsförfrågningar."""
    },
    "ui_customization": {
        "title": "📅 Datumformat, kalender & kolumnbredder",
        "category": "Användargränssnitt",
        "content": """### 📅 Datumformatering, kalenderväljare & kolumnbredder

Alla datum visas i standardiserat format DD.MM.YYYY."""
    },
    "praxis": {
        "title": "🏥 Mottagnings- & kundhantering",
        "category": "Kunder",
        "content": """### 🏥 Hantering av mottagningar och kunddata

Hantera alla kundposter centralt under Stamdata -> Mottagningar."""
    },
    "scoring": {
        "title": "📊 Poängsättning & prioritering",
        "category": "Arbetsflöde",
        "content": """### 📊 Automatisk poängsättning av brådskande ärenden

Systemet beräknar automatiskt poäng för öppna ärenden."""
    },
    "schemas": {
        "title": "📄 Formulärbyggare & scheman",
        "category": "Formulär",
        "content": """### 📄 Anpassade dynamiska formulär

Skapa skräddarsydda formulär för olika supportscenarier."""
    },
    "export": {
        "title": "📤 Exportmotor & mallar",
        "category": "Export",
        "content": """### 📤 Export- och överlämningsassistent

Generera rapportsammanfattningar och e-postmeddelanden med ett klick."""
    },
    "wiki": {
        "title": "📚 BookStack Wiki-integration",
        "category": "Wiki",
        "content": """### 📚 BookStack Wiki-integration

Anslut direkt till din BookStack-kunskapsbas."""
    },
    "p2p": {
        "title": "🔄 Peer-to-Peer-synk (kollegor)",
        "category": "Synk",
        "content": """### 🔄 P2P-datasynkronisering

Synkronisera ärenden direkt mellan kollegor på det lokala nätverket."""
    },
    "shortcuts": {
        "title": "⌨ Tangentbordsgenvägar & snabbknappar",
        "category": "Genvägar",
        "content": """### ⌨ Tangentbordsgenvägar

- `Ctrl+N`: Nytt ärende
- `Ctrl+S`: Spara ärende
- `Ctrl+E`: Exportera ärende
- `F1`: Hjälp"""
    },
    "storage_paths": {
        "title": "📁 Lagringsplatser, datamappar & EXE-drift",
        "category": "Konfiguration",
        "content": """### 📁 Lagringsplatser & mapplänkar

Separera arbetsdata från applikationsfiler för säker portabilitet."""
    },
    "template_editor": {
        "title": "📄 Mallredigerare för export",
        "category": "Export",
        "content": """### 📄 Redigera exportmallar i realtid

Redigera HTML/Jinja2-mallar med direkt förhandsgranskning."""
    },
    "handover_followup": {
        "title": "🔔 Ärendeöverlämningar & uppföljningar",
        "category": "Arbetsflöde",
        "content": """### 🔔 Överlämningar & uppföljningspåminnelser

Överlämna ärenden till kollegor eller ställ in påminnelser."""
    },
    "email_calendar_outlook": {
        "title": "✉ E-post, kalender (.ics) & Outlook",
        "category": "Kommunikation",
        "content": """### ✉ E-postutkast, kalender & Outlook-integration

Skriv e-postmeddelanden, exportera kalenderhändelser eller överför till Outlook."""
    },
    "case_print_reporting": {
        "title": "🖨 Utskriftsvy för ärende, PDF & bilder",
        "category": "Export",
        "content": """### 🖨 Utskrift & PDF-export

Generera utskriftsrapporter och PDF-dokument med inbäddade bildbilagor."""
    },
    "ai_ollama_management": {
        "title": "🤖 AI-assistent, Ollama-server & modellval",
        "category": "AI & Ollama",
        "content": """### 🤖 Lokal AI-supportassistent

Dataskyddsanpassad AI-support med Ollama eller Google Gemini Cloud API."""
    },
    "stepper_time_picker": {
        "title": "⏱ Tidsval (07:00-20:00) & stegreglage",
        "category": "Användargränssnitt",
        "content": """### ⏱ Interaktiv tidsväljare

Anpassade tidsval för mottagningstider med snabba stegknappar."""
    },
    "internal_cases": {
        "title": "🏢 Interna ärenden & uppgifter (utan kundkoppling)",
        "category": "Arbetsflöde",
        "content": """### 🏢 Interna ärenden & uppgifter

Hantera interna IT-uppgifter och underhåll utan kundkoppling."""
    },
    "cobra_crm_import": {
        "title": "🐍 Cobra CRM mottagnings- & kundimport",
        "category": "Kunder",
        "content": """### 🐍 Cobra CRM importassistent

Importera kunddatabaser direkt från Cobra CRM-exporter."""
    },
    "snippets_manager": {
        "title": "📝 Textbyggblock & snabbsvarsmallar",
        "category": "Kommunikation",
        "content": """### 📝 Hantera textbyggblock

Spara tid vid återkommande svar med mallbyggblock."""
    },
    "repeatable_sub_forms": {
        "title": "📂 Dynamiska flerkortsformulär",
        "category": "Formulär",
        "content": """### 📂 Dynamiska formulär med flera underkort

Registrera flera oberoende förfrågningar i ett enda ärende."""
    },
    "analytics_kpi_dashboard": {
        "title": "Analys & nyckeltalspanel",
        "category": "Analys",
        "content": """### Analys- och nyckeltalspanel

Fullständig statistisk översikt över arbetsbelastning och hanteringstider."""
    },
    "advanced_search_filters": {
        "title": "🔍 Avancerad sökning & söktokens",
        "category": "Grundläggande",
        "content": """### 🔍 Söktokens och snabbfilter

Filtrera ärenden med söktokens som `is:internal`, `vip:true`, `reminder:due`."""
    },
    "attachments_and_screenshots": {
        "title": "📂 Filbilagor & skärmdumpar (Ctrl+V)",
        "category": "Dokument",
        "content": """### 📂 Bilagshantering & skärmdumpar från urklipp

Klistra in skärmdumpar direkt med `Ctrl+V`."""
    },
    "zip_backup_restore": {
        "title": "📦 Fullständig ZIP-säkerhetskopia & återställning",
        "category": "Konfiguration",
        "content": """### 📦 Säkerhetskopiering av arbetsyta

Exportera alla ärenden och bilagor till ett ZIP-arkiv."""
    },
    "email_webhook_integration": {
        "title": "🔌 E-post IMAP-import & REST-webhooks",
        "category": "Integrationer",
        "content": """### 🔌 E-postimport & webhooks

Hämta e-post via IMAP och utlös REST-webhooks för Jira/GitLab."""
    }
}

# Update de.json
de_file = Path("locales/de.json")
with open(de_file, "r", encoding="utf-8") as f:
    de_data = json.load(f)

de_help_content = {}
for art in HELP_ARTICLES:
    art_id = art["id"]
    de_help_content[art_id] = {
        "title": art["title"],
        "category": art["category"],
        "content": art["content"]
    }
de_data["help_content"] = de_help_content

with open(de_file, "w", encoding="utf-8") as f:
    json.dump(de_data, f, ensure_ascii=False, indent=2)

# Update en.json
en_file = Path("locales/en.json")
with open(en_file, "r", encoding="utf-8") as f:
    en_data = json.load(f)

en_help_content = {}
for art in HELP_ARTICLES:
    art_id = art["id"]
    if art_id in en_articles:
        en_help_content[art_id] = en_articles[art_id]
    else:
        en_help_content[art_id] = {
            "title": art["title"],
            "category": art["category"],
            "content": art["content"]
        }
en_data["help_content"] = en_help_content

with open(en_file, "w", encoding="utf-8") as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

# Update sv.json
sv_file = Path("locales/sv.json")
with open(sv_file, "r", encoding="utf-8") as f:
    sv_data = json.load(f)

sv_help_content = {}
for art in HELP_ARTICLES:
    art_id = art["id"]
    if art_id in sv_articles:
        sv_help_content[art_id] = sv_articles[art_id]
    else:
        sv_help_content[art_id] = {
            "title": art["title"],
            "category": art["category"],
            "content": art["content"]
        }
sv_data["help_content"] = sv_help_content

with open(sv_file, "w", encoding="utf-8") as f:
    json.dump(sv_data, f, ensure_ascii=False, indent=2)

print("Help content for ALL 25 articles successfully updated across de.json, en.json, and sv.json!")
