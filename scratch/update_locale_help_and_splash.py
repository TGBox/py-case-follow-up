import json
import os

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRATCH_DIR)
LOCALES_DIR = os.path.join(PROJECT_ROOT, "locales")

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

de_path = os.path.join(LOCALES_DIR, "de.json")
en_path = os.path.join(LOCALES_DIR, "en.json")
sv_path = os.path.join(LOCALES_DIR, "sv.json")

de_data = load_json(de_path)
en_data = load_json(en_path)
sv_data = load_json(sv_path)

# 1. Splash translations
de_data["splash"] = {
    "title": "🩺 Support-Cockpit",
    "loading": "⏳ Anwendungsdaten und Layouts werden geladen..."
}

en_data["splash"] = {
    "title": "🩺 Support Cockpit",
    "loading": "⏳ Loading application data and layouts..."
}

sv_data["splash"] = {
    "title": "🩺 Support-Cockpit",
    "loading": "⏳ Läser in applikationsdata och layouter..."
}

# 2. Comprehensive English Help Content
en_help = {
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
- Shortcut to focus search: `Ctrl+F`
"""
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
- Quick selection buttons for *Today*, *+ 1 Day*, and *+ 1 Week* speed up data entry.

#### 3. 📐 Individual & Persistent Column Widths
- Use the **📐 Columns** button in the top menu bar to freely adjust the widths of individual columns in the cockpit (case list, details/form, timeline) as well as the Kanban board.
- Your chosen widths are automatically saved in the user configuration (`user_config.json`) and persist across application restarts.
"""
    },
    "praxis": {
        "title": "🏥 Practice & Customer Management",
        "category": "Customers",
        "content": """### 🏥 Practice & Customer Management

Every support case is assigned to a specific medical practice (customer).

#### 1. Open Practice Management
- Click **🏥 Practices** in the top menu bar.
- Here you will see a complete list of all registered practices with customer number, practice name, primary contact person, email, and phone.

#### 2. Create New Practice
- Open **🏥 Practices** -> **+ Create New Practice**.
- Or directly when creating a new case in the **+ New Case** dialog: Click **+ New Practice** next to the practice selection. The new practice is immediately available for selection!

#### 3. Manage Contact Persons
- In the practice details, you can store multiple contact persons (e.g. practice owner, IT manager, medical assistants).
"""
    },
    "scoring": {
        "title": "📊 Case Scoring & Prioritization",
        "category": "Workflow",
        "content": """### 📊 Automatic Urgency Scoring

The Support Cockpit automatically calculates an **Urgency Score** (points) for every open case so that you can identify urgent cases immediately.

#### How is the score calculated?
- **Priority**: Critical (60 pts), High (40 pts), Medium (20 pts), Low (10 pts).
- **VIP Status**: VIP practices receive a bonus of +30 points.
- **Waiting Time**: The longer a case remains open, the higher the score rises (+2 pts / day).
- **Inactivity**: Cases without an update in the last 48 hours receive additional points.
- **Workflow Status**: In Progress (+10 pts), Waiting for Customer (+0 pts), On-site Appointment Needed (+20 pts).

#### Automatic Hourly Recalculation
A background timer updates the scores of all open cases hourly.
"""
    },
    "schemas": {
        "title": "📄 Form Builder (Schemas)",
        "category": "Forms",
        "content": """### 📄 Dynamic Form Schemas

Different support types (e.g. hardware replacement, billing inquiry, interface problem) require different information.

#### Create & Customize Custom Forms
1. Click **🛠 Form Builder** in the menu bar.
2. Create a new schema (e.g. *\"PVS Interface\"*) or edit an existing one.
3. Add custom fields:
   - **Text Fields** (e.g. error message)
   - **Number Fields** (e.g. port number)
   - **Yes/No Checkboxes** (e.g. service restarted)
   - **Dropdown Selection Fields** (e.g. PVS manufacturer)
4. Define required mandatory fields (*).

When completing a case in the cockpit, the form automatically adapts to the selected schema!
"""
    },
    "export": {
        "title": "📤 Export Engine & Templates",
        "category": "Export",
        "content": """### 📤 Handover & Export Engine

Generate ready-to-use handover protocols, emails, or documentation for colleagues or ticketing systems with a single click.

#### Export Case
1. Select the desired case and click **📤 Export (Ctrl+E)**.
2. Select a template (e.g. *\"Standard Handover\"*, *\"Customer Summary\"*, *\"Developer Bug Report\"*).
3. Select the output format:
   - **Markdown** (ideal for wikis / Jira / GitHub)
   - **HTML / Text** (ideal for emails)
   - **PDF** (for print / archiving)
4. Use the **📋 Copy to Clipboard** or **💾 Save as File** button.
"""
    },
    "wiki": {
        "title": "📚 BookStack Wiki Integration",
        "category": "Wiki",
        "content": """### 📚 BookStack Wiki Integration

The Support Cockpit is directly connected to your BookStack Wiki to keep solution articles readily accessible.

#### Features
- **Automatic Search**: Type search terms into the wiki search bar to find matching articles.
- **Article Preview**: Article content is rendered directly in the right cockpit panel.
- **Open in BookStack**: Open articles with one click in your default browser.
- **Case Linking**: Link resolved cases to the corresponding wiki article.
- **Configuration**: Enter your BookStack URL and API tokens in **Profile & Settings** (`👤`).
"""
    },
    "p2p": {
        "title": "🔄 Peer-to-Peer Sync (Colleagues)",
        "category": "Sync",
        "content": """### 🔄 Peer-to-Peer (P2P) Synchronization

Collaborate with colleagues without a central server! P2P Sync allows matching case data directly between local workstations.

#### Workflow
1. Click **🔄 P2P Sync**.
2. Select the colleague you want to sync with.
3. The system compares the version status of the cases.
4. In the **Diff Dialog**, you see conflicts or newly added cases and can safely merge changes.
"""
    },
    "shortcuts": {
        "title": "⌨ Keyboard Shortcuts & Hotkeys",
        "category": "Shortcuts",
        "content": """### ⌨ Keyboard Shortcuts

Work even faster with the following hotkeys:

| Action | Default Hotkey |
| :--- | :--- |
| **New Case** | `Ctrl + N` |
| **Save Case** | `Ctrl + S` |
| **Archive Case** | `Ctrl + Shift + A` |
| **Export Case** | `Ctrl + E` |
| **Open Settings** | `Ctrl + P` |
| **Open Snippet Picker** | `Ctrl + M` |
| **Focus Wiki Search** | `Ctrl + W` |
| **Focus Customer Search** | `Ctrl + F` |
| **Cockpit View** | `Ctrl + 1` |
| **Tab View** | `Ctrl + 2` |
| **Split View** | `Ctrl + 3` |
| **Analytics & KPIs** | `Ctrl + 4` |
| **Toggle Theme** | `Ctrl + T` |
| **Help Dialog** | `F1` |
| **Text Snippet Macros** | e.g. `Ctrl + Alt + 1` |

*Note: All keyboard shortcuts and snippet macros can be customized and recorded interactively in Settings (`⚙ Profile & Settings` -> `⌨ Shortcuts & Scoring`).*
"""
    },
    "storage_paths": {
        "title": "📁 Storage Locations & File Paths",
        "category": "Configuration",
        "content": """### 📁 Storage Locations, Data Structure & EXE Mode

The **Support Cockpit** keeps application data separated from program files. This allows safe execution from a single executable file (PyInstaller `.exe`) and prevents tracking real customer data in Git repositories.

#### 1. Data Folder & Custom Paths
- Open **Profile & Settings** (`👤 [Your Name]`) -> **📁 Storage & Paths** tab.
- **Main Data Folder**: Click **📁 Choose Folder** to set your workspace location (e.g. `D:\\SupportData` or a network share).
- **Individual File Paths**: If needed, link individual files (`cases.json`, `customers.json`, `wiki_index.sqlite`) to different locations or reset them to default via **🔄 Reset Individual Paths**.

#### 2. Executable (.exe) Mode Behavior
- When the app is run as a compiled `.exe`, no folders are created in the execution directory (e.g. `C:\\Program Files\\`).
- Instead, the central user configuration is stored in your user profile:
  - Windows: `%APPDATA%\\SupportCockpit\\user_config.json`
  - Linux/Mac: `~/.config/SupportCockpit/user_config.json`
- If configuration is missing, `Documents\\SupportCockpitData` is automatically used as the default data folder.

#### 3. Sample Files & Automatic Initialization
- **Repository Templates (`data_examples/`)**: Sample files from `data_examples/` are copied to your chosen data folder on first startup.
- **Empty Files**: If neither data nor templates exist, the application automatically creates new empty data files for smooth operation.
"""
    },
    "template_editor": {
        "title": "📄 Export Template Editor",
        "category": "Export",
        "content": """### 📄 Create & Customize Export Templates

In the **Export Template Editor**, you can customize existing handover templates or define completely new export formats.

#### Open Template Manager
- Click **📄 Templates** in the top menu bar or **🛠 Manage Templates** inside the Export Dialog (`Ctrl+E`).

#### Configure Template
1. **Name & ID**: Assign a unique ID and a readable display name.
2. **Target Action**: Choose between clipboard text and file export.
3. **Assigned Schemas**: Check the form schemas for which the template should be offered.
4. **Required Mandatory Fields**: Define which case fields must be filled out before exporting is allowed.
5. **Jinja2 Template**: Write the template text in Markdown/HTML. Use **👁 Render Live Preview** to instantly verify the output!
"""
    },
    "handover_followup": {
        "title": "🔔 Case Handovers & Follow-ups",
        "category": "Workflow",
        "content": """### 🔔 Responsibility Handovers & Follow-up Reminders

Always keep track of when a case was handed over to whom and when to follow up with colleagues.

#### 1. Automatic Handover Logging
- As soon as you change the **Assignee (Actor)** of a case (e.g. from *Support* to *Development*), the system automatically creates a precise entry in the **Timeline**:
  - *Timestamp & Author*
  - *Status Change: ASSIGNEE: Support -> Development*
  - *Note: Handover to: Development (previously: Support)*

#### 2. Schedule Follow-up & Reminder Alerts
- When reassigning a case, the **🔔 Schedule Follow-up** dialog opens automatically.
- Or click **🔔 Follow-up** anytime in the case details.
- Select a quick preset (`+ 1 Day`, `+ 2 Days`, `+ 1 Week`) or a custom date with a note.
- Cases with an active follow-up are highlighted with 3 lines in the case list (Follow-up on, date with relative info `(tomorrow)` / `(today)` / `(in X days)`, time).
"""
    },
    "email_calendar_outlook": {
        "title": "✉ Email, Calendar (.ics) & Outlook",
        "category": "Communication",
        "content": """### ✉ Compose Emails, iCalendar Export & Microsoft Outlook Integration

Two separate features are available in the Cockpit:

#### 1. ✉ Compose Email
- Click **✉ Email** to open the email draft for the current case.
- Recipient and subject are pre-filled based on practice data and subject.
- Click **🧩 Text Snippet** to insert pre-built support templates (e.g. TI troubleshooting, billing correction) with one click.
- **Transfer to Outlook**: Opens the email directly in Microsoft Outlook with all fields filled.
- **Open in Standard Mail App**: Launches your default mail client via `mailto:` protocol.

#### 2. 📅 Create Calendar Entry (.ics)
- Click **📅 Calendar** to generate a calendar appointment for follow-ups or callback deadlines.
- **Open directly in Calendar**: Creates a temporary `.ics` file and opens your calendar (Outlook / Thunderbird).
- **Save as .ics file...**: Saves the event file to any location.

#### 3. 📬 Outlook Add-in / Macro (Transfer Emails to Cockpit)
- With the integrated Outlook macro, you can transfer received customer emails directly from Outlook into Support Cockpit to automatically create a new case or append a timeline note.
"""
    },
    "case_print_reporting": {
        "title": "🖨 Case Print View, PDF & Images",
        "category": "Export",
        "content": """### 🖨 Case Print View, PDF Export & Image Attachments

Create comprehensive case dossiers for archiving or team meetings.

#### 1. Open Print Dialog
- Click **🖨 Print** in the Cockpit.
- Select which sections to include (customer data, form fields, timeline entries, images).

#### 2. Images & Screenshots at Page End
- All image files (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`) from the case folder are automatically embedded at the end of the document.
- You can inspect screenshots simply by scrolling in the report and printing them along with the document.

#### 3. Export Options
- **🖨 Open in Browser & Print**: Opens the page in your default browser and automatically launches the browser print/PDF export dialog.
- **💾 Save as HTML/PDF Report...**: Saves the complete standalone HTML dossier to your disk.
"""
    },
    "ai_ollama_management": {
        "title": "🤖 AI Assistant, Ollama Server & Model Control",
        "category": "AI & Ollama",
        "content": """### 🤖 Local AI Support Assistant & Ollama Server Control

The Support Cockpit provides 100% privacy-compliant AI assistance powered by local open-source LLMs (e.g. Ollama with Qwen2.5 / Llama3). All requests remain 100% on your PC!

#### 1. ⚙ Ollama Server Control (Start & Stop from App)
Under **Profile & Settings** (`👤`) -> **🤖 AI & NLP** tab, you can manage the Ollama server directly:
- **`▶ Start Ollama Server`**: Starts the Ollama background process (`ollama serve`) without opening a terminal.
- **`🛑 Stop Server`**: Gracefully terminates the Ollama process and frees up RAM/VRAM immediately.
- **`🌐 Download Links`**: Direct links to `ollama.com`, `qwen2.5`, and `llama3` if Ollama is not yet installed.

#### 2. ⚡ Create PVS Support Model in One Click
- Click **`⚡ Create PVS Support Model from Modelfile`** to generate a specialized model (`pvs-support`) from the bundled Modelfile.
- This model is pre-configured specifically for German healthcare IT support (PVS, TI connectors, GKV billing, KV-SafeNet).

#### 3. 🎚 Global AI Toggle & Auto Unload
- Use the **`🤖 AI Globally Active`** switch to turn AI off anytime.
- Disabling AI automatically unloads the active model from RAM/VRAM.
- All AI generation buttons are safely disabled when the switch is OFF.

#### 4. 🚦 Precise Status Color Coding
- **`🔴 Red`**: Ollama Offline or server unreachable.
- **`⚪ Gray`**: Ollama Online, but AI switch is OFF.
- **`🔵 Blue`**: Ollama Online & AI Active, but standby (no model loaded in RAM).
- **`🟢 Green`**: Ollama Online & AI Active with model ready in RAM.

#### 5. 🎯 Hierarchical Prompt Rules & Directives
1. **Global Base Rules** (User profile defaults).
2. **Practice-Specific Override Rules** (Stored in practice details).
3. **⚡ Prioritized Custom Directive** (Entered in dialog, highest priority).
"""
    },
    "stepper_time_picker": {
        "title": "⏱ Time Selection (07:00-20:00) & Stepper",
        "category": "User Interface",
        "content": """### ⏱ Time Selection & Stepper Arrows

The time picker in calendar and follow-up dialogs is optimized specifically for office working hours:

- **Practice Working Hours**: Hours focus on core office hours from **07:00 AM to 08:00 PM**.
- **Quick Stepper Buttons**: Arrow buttons (`▲` / `▼`) next to dropdown menus:
  - Hours: Adjust step-by-step by `+/- 1 Hour`.
  - Minutes: Adjust step-by-step in 5-minute increments (`+/- 5 Min`).
"""
    },
    "internal_cases": {
        "title": "🏢 Internal Cases & Tasks (Non-Customer)",
        "category": "Workflow",
        "content": """### 🏢 Internal Operations & Sub-Tasks

In addition to customer support cases, you can manage **purely internal tasks** (e.g. server maintenance, system updates, notes, or development tasks).

#### Features:
- **No Customer Required**: When creating a new case (`+ New Case` / `Ctrl+N`), leave practice blank or set to *\"🏢 Internal Operation / No Practice\"*.
- **Automatic Schema Adaptation**: The form automatically switches to *\"🏢 Internal Task / Note\"*.
- **Visual Highlight**: Internal cases get a blue **`🏢 INTERNAL`** badge in the case list.
- **Search Filter**: Use **`[🏢 Internal]`** quick filter or search token `is:internal`.
"""
    },
    "cobra_crm_import": {
        "title": "🐍 Cobra CRM Practice & Customer Import",
        "category": "Customers",
        "content": """### 🐍 Cobra CRM Import Assistant

Import your existing practice database directly from Cobra CRM into Support Cockpit.

#### Workflow:
1. Open Practice Management (**🏥 Practices**).
2. Click **🐍 Cobra CRM Import...**.
3. Select your export file (supports `.csv`, `.txt`, `.json`).
4. **Automatic Column Detection**: Recognizes Cobra fields (customer number, practice name, contact person, email, phone, VIP status) via aliasing.
5. After confirmation, all practices are immediately available for case assignment.
"""
    },
    "snippets_manager": {
        "title": "📝 Text Snippets & Snippet Manager",
        "category": "Communication",
        "content": """### 📝 Manage & Insert Text Snippets

Save time on recurring responses and standard notes with the built-in snippet manager.

#### 1. Manage Text Snippets
- Click **📝 Text Snippets** in the main menu.
- Create new snippets with title, category (e.g. *Billing*, *Hardware*, *TI Support*), tags, and template text.

#### 2. Insert Snippets into Notes or Emails
- In note fields or email dialog (`✉ Email`): Click **🧩 Text Snippet**.
- The `SnippetPickerDialog` opens with search bar and category filter.
- Select the desired snippet — text is inserted at the current cursor position!
"""
    },
    "repeatable_sub_forms": {
        "title": "📂 Dynamic Multi-Card Forms",
        "category": "Forms",
        "content": """### 📂 Dynamic Multi-Card Forms (Repeatable Blocks)

Certain form types (such as *\"Co-payment Claim & Billing Correction\"*) require capturing multiple independent requests within a single case.

#### Usage:
1. Select the form **\"Co-payment Claim & Billing Correction\"**.
2. **Card Container**: Creates individual cards for each request (ESOL file name, requested action, invoice no. & date, prescription no., patient name(s), justification).
3. **➕ Add Another File / Claim Request**: Dynamically adds a new empty claim card.
4. **🗑 Remove Claim #N**: Deletes individual cards as needed.
5. **Email & Export**: Formats all cards automatically as numbered sections (`--- File Claim #1 ---`).
"""
    },
    "analytics_kpi_dashboard": {
        "title": "Analytics & KPI Dashboard",
        "category": "Analytics",
        "content": """### Analytics & KPI Dashboard

Get comprehensive insights into your support performance and key metrics at a glance.

#### Open Dashboard:
- Click **Analytics & Metrics** in the menu bar or press `Ctrl + 4`.

#### 6 Main KPI Cards (Top Row):
- **📋 Total Cases**: Total number of recorded cases.
- **⏳ Open Cases**: Cases in progress or waiting.
- **✓ Resolved (%)**: Number of resolved cases with percentage success rate.
- **⚠ Overdue**: Open cases with exceeded follow-up / due date (`due_date`).
- **⏱ Avg Resolution Time**: Average resolution time from creation to completion in days or hours.
- **⭐ VIP Ratio**: Percentage of cases from premium/VIP practices.

#### 2-Column Dashboard Layout:
- **Left Column**:
  - **🚨 Urgency Distribution (Scoring)**: Traffic light indicator for `🔴 Critical`, `🟡 High`, `🟢 Normal`.
  - **📄 Distribution by Form Schema**: Breakdown by form type.
- **Right Column**:
  - **🏆 Top 5 Practices by Volume**: Ranking with VIP badges (`★ VIP`).
  - **👤 Workload by Assignee**: Open vs. resolved cases per staff member.
  - **👥 Open Cases by Department**: Breakdown by *Support, Development, Tech, Customer*.

#### 📋 Copy Statistics Report:
- Click the top-right button to copy a complete Markdown summary of all metrics directly to your clipboard!
"""
    },
    "advanced_search_filters": {
        "title": "🔍 Advanced Search & Search Tokens",
        "category": "Basics",
        "content": """### 🔍 Advanced Search System & Tokens

The cockpit search bar supports both free-text search and powerful filter tokens.

#### 1. Quick Filter Buttons
- **`[All]`**: Show all cases.
- **`[🔥 Urgent]`**: Show cases with high urgency score.
- **`[🔔 Follow-ups]`**: Show due follow-ups.
- **`[🏢 Internal]`**: Show purely internal tasks.

#### 2. Search Tokens (`Ctrl+F`):
Combinable tokens for precise filtering:
- `is:internal` / `is:customer`: Filter by internal or customer cases.
- `vip:true`: Only VIP practices.
- `reminder:due`: Only due follow-ups.
- `actor:dev` / `actor:support` / `actor:tech`: Filter by responsibility.
- `status:open` / `status:closed`: Filter by status.
- `error:XYZ`: Search by error codes or notes text.
"""
    },
    "attachments_and_screenshots": {
        "title": "📂 File Attachments & Screenshots (Ctrl+V)",
        "category": "Documents",
        "content": """### 📂 File Attachments, Screenshots & Previews

Manage log files, screenshots, and documents directly inside the case.

#### 1. Paste Screenshots via `Ctrl+V`
- Take a screenshot (e.g. using `Win+Shift+S`).
- Press **`Ctrl + V`** inside Cockpit: Image is automatically saved to case folder and embedded in timeline!

#### 2. Live Preview & OS Launch
- Image files (`.png`, `.jpg`, `.webp`) and text files (`.log`, `.json`, `.txt`) can be previewed directly in attachments bar.
- Double-clicking opens the file in your OS default application.
"""
    },
    "zip_backup_restore": {
        "title": "📦 Complete ZIP Backup & Import/Export",
        "category": "Configuration",
        "content": """### 📦 Complete ZIP Backup & Import/Export

Backup your entire workspace including all cases, customer data, schemas, templates, and attachments in a single ZIP file.

#### Procedure:
1. Open **Profile & Settings** (`👤`) -> **📦 Backup & Restoration**.
2. **`💾 Create Full Backup...`**: Saves all JSON files and attachments folder into a ZIP archive.
3. **`📥 Restore Backup...`**: Unpacks and restores a previous state (with automated safety backup of current data).
"""
    },
    "email_webhook_integration": {
        "title": "🔌 Email Import & REST Webhooks (Jira/GitLab)",
        "category": "Integrations",
        "content": """### 🔌 Email Ingestion & REST Webhooks

Connect Support Cockpit to external systems.

#### 1. 📬 Automatic Email Import (IMAP)
- Queries a support mailbox via IMAP and automatically creates new incoming emails as draft cases.

#### 2. 🔗 REST Webhook Integration (GitLab / Jira)
- Configure webhook URLs under Settings to automatically trigger issue payloads to GitLab, Jira, or custom APIs upon case creation or transfer.
"""
    }
}

# 3. Comprehensive Swedish Help Content
sv_help = {
    "basics": {
        "title": "🚀 Grundläggande & Layouter",
        "category": "Grundläggande",
        "content": """### 🚀 Grundläggande om användargränssnittet

**Support-Cockpit** hjälper dig att effektivt spåra, kategorisera och prioritera supportärenden och klinikförfrågningar.

#### De 4 vyerna (Layoutlägen)
I den övre menyraden kan du när som helst växla mellan 4 vyer (`Ctrl+1` till `Ctrl+4`):

1. **Cockpit-vy (Standard, `Ctrl+1`)**:
   - Tredelad huvudlayout med ärendelista, ärendedetaljer/formulär och BookStack-wiki.

2. **Kanban-tavla (`Ctrl+2`)**:
   - Tavla organiserad efter kolumner & ansvar (*Ny*, *Åtgärd krävs*, *Väntar*, *Pågår*, *Klar*).

3. **Tabell & Detaljer (`Ctrl+3`)**:
   - Tabellmatris som visar ärendedetaljer för en kompakt översikt, sortering och filtrering.

4. **Analys & Nyckeltal (`Ctrl+4`)**:
   - Fullständig statistikpanel som visar handläggningstider, förfallna tidsgränser, VIP-andel och rapportexport.

---

#### 🔍 Sök- & filterfunktion
- Använd sökfältet högst upp i ärendelistan för att filtrera ärenden efter **Ärende-ID**, **Kliniknamn**, **Ämne** eller **Taggar**.
- Kortkommando för att fokusera sökningen: `Ctrl+F`
"""
    },
    "ui_customization": {
        "title": "📅 Datumformat, Kalender & Kolumnbredder",
        "category": "Användargränssnitt",
        "content": """### 📅 Datumformatering, Kalenderväljare & Kolumnbredder

#### 1. 📅 Datumformatering
- Alla datum i Support-Cockpit (tidsgränser, återuppringningar, uppföljningar, tidslinje) visas enhetligt i standarddatumformat (`DD.MM.YYYY` eller `DD.MM.YYYY HH:MM`).

#### 2. 🗓 Interaktiv kalenderväljare
- En interaktiv kalenderdialog finns tillgänglig för alla datumangivelser (t.ex. planera uppföljningar, ange tidsgränser för återuppringning).
- Klicka på **📅 Kalender** bredvid inmatningsfältet för att öppna månadskalendern och enkelt välja önskat datum.
- Snabbvalsknappar för *Idag*, *+ 1 dag* och *+ 1 vecka* snabbar upp inmatningen.

#### 3. 📐 Individuella & permanenta kolumnbredder
- Använd knappen **📐 Kolumner** i den övre menyraden för att fritt anpassa bredden på enskilda kolumner i cockpit och Kanban-tavlan.
- Dina valda bredder sparas automatiskt i användarkonfigurationen (`user_config.json`) och finns kvar vid omstart.
"""
    },
    "praxis": {
        "title": "🏥 Klinik- & Kundhantering",
        "category": "Kunder",
        "content": """### 🏥 Klinik- & Kundhantering

Varje supportärende är tilldelat en specifik klinik (kund).

#### 1. Öppna klinikhantering
- Klicka på **🏥 Kliniker** i den övre menyraden.
- Här ser du en fullständig lista över alla registrerade kliniker med kundnummer, kliniknamn, kontaktperson, e-post och telefon.

#### 2. Skapa ny klinik
- Öppna **🏥 Kliniker** -> **+ Skapa ny klinik**.
- Eller direkt när du skapar ett nytt ärende i dialogen **+ Nytt ärende**: Klicka på **+ Ny klinik** bredvid klinikvalet. Den nya kliniken blir omedelbart tillgänglig!

#### 3. Hantera kontaktpersoner
- I klinikdetaljerna kan du lägga till flera kontaktpersoner (t.ex. klinikägare, IT-ansvarig, assistenter).
"""
    },
    "scoring": {
        "title": "📊 Ärendepoäng & Prioritering",
        "category": "Arbetsflöde",
        "content": """### 📊 Automatisk brådskepoängsättning

Support-Cockpit beräknar automatiskt en **Brådskepoäng** (Urgency Score) för varje öppet ärende så att du omedelbart kan identifiera brådskande ärenden.

#### Hur beräknas poängen?
- **Prioritet**: Kritisk (60 poäng), Hög (40 poäng), Medium (20 poäng), Låg (10 poäng).
- **VIP-status**: VIP-kliniker får en bonus på +30 poäng.
- **Väntetid**: Ju längre ett ärende förblir öppet, desto högre stiger poängen (+2 poäng / dag).
- **Inaktivitet**: Ärenden utan uppdatering de senaste 48 timmarna får extra poäng.
- **Status**: Pågår (+10 poäng), Väntar på kund (+0 poäng), Platsbesök krävs (+20 poäng).

#### Automatisk timvis omberäkning
En bakgrundstimer uppdaterar poängen för alla öppna ärenden varje timme.
"""
    },
    "schemas": {
        "title": "📄 Formulärbyggare (Scheman)",
        "category": "Formulär",
        "content": """### 📄 Dynamiska formulärscheman

Olika supporttyper (t.ex. byte av hårdvara, faktureringsfråga, gränssnittsproblem) kräver olika information.

#### Skapa & anpassa egna formulär
1. Klicka på **🛠 Formulärbyggare** i menyraden.
2. Skapa ett nytt schema (t.ex. *\"PVS-gränssnitt\"*) eller redigera ett befintligt.
3. Lägg till egna fält:
   - **Textfält** (t.ex. felmeddelande)
   - **Nummerfält** (t.ex. portnummer)
   - **Ja/Nej-kryssrutor** (t.ex. tjänst omstartad)
   - **Rullgardinsfält** (t.ex. PVS-tillverkare)
4. Ange obligatoriska fält (*).

När du fyller i ett ärende i cockpit anpassas formuläret automatiskt till det valda schemat!
"""
    },
    "export": {
        "title": "📤 Exportmotor & Mallar",
        "category": "Export",
        "content": """### 📤 Överlämnings- & exportmotor

Generera färdiga överlämningsprotokoll, e-postmeddelanden eller dokumentation för kollegor eller ärendesystem med ett klick.

#### Exportera ärende
1. Välj önskat ärende och klicka på **📤 Exportera (Ctrl+E)**.
2. Välj en mall (t.ex. *\"Standardöverlämning\"*, *\"Kundsammanfattning\"*, *\"Utvecklarrapport\"*).
3. Välj utdataformat:
   - **Markdown** (idealiskt för wiki / Jira / GitHub)
   - **HTML / Text** (idealiskt för e-post)
   - **PDF** (för utskrift / arkivering)
4. Använd knappen **📋 Kopiera till urklipp** eller **💾 Spara som fil**.
"""
    },
    "wiki": {
        "title": "📚 BookStack Wiki-integration",
        "category": "Wiki",
        "content": """### 📚 BookStack Wiki-integration

Support-Cockpit är direkt ansluten till din BookStack Wiki för att hålla lösningsartiklar lättillgängliga.

#### Funktioner
- **Automatisk sökning**: Skriv sökord i wiki-sökfältet för att hitta matchande artiklar.
- **Förhandsvisning**: Artikelinnehåll renderas direkt i den högra cockpitpanelen.
- **Öppna i BookStack**: Öppna artiklar med ett klick i din standardwebbläsare.
- **Koppla ärende**: Koppla lösta ärenden till motsvarande wiki-artikel.
- **Konfiguration**: Ange din BookStack URL och API-tokens under **Profil & Inställningar** (`👤`).
"""
    },
    "p2p": {
        "title": "🔄 Peer-to-Peer Sync (Kollegor)",
        "category": "Synk",
        "content": """### 🔄 Peer-to-Peer (P2P) Synkronisering

Samarbeta med kollegor utan en central server! P2P-synk gör det möjligt att jämföra ärendedata direkt mellan lokala arbetsstationer.

#### Arbetsflöde
1. Klicka på **🔄 P2P-synk**.
2. Välj den kollega du vill synkronisera med.
3. Systemet jämför ärendenas versionsstatus.
4. I **Skillnadsdialogen** ser du konflikter eller nyligen tillagda ärenden och kan säkert sammanfoga ändringar.
"""
    },
    "shortcuts": {
        "title": "⌨ Kortkommandon & Hotkeys",
        "category": "Kortkommandon",
        "content": """### ⌨ Kortkommandon

Arbeta ännu snabbare med följande kortkommandon:

| Åtgärd | Standardkortkommando |
| :--- | :--- |
| **Nytt ärende** | `Ctrl + N` |
| **Spara ärende** | `Ctrl + S` |
| **Arkivera ärende** | `Ctrl + Skift + A` |
| **Exportera ärende** | `Ctrl + E` |
| **Öppna inställningar** | `Ctrl + P` |
| **Öppna textmallsväljare** | `Ctrl + M` |
| **Fokusera wiki-sökning** | `Ctrl + W` |
| **Fokusera kundsökning** | `Ctrl + F` |
| **Cockpit-vy** | `Ctrl + 1` |
| **Tabb-vy** | `Ctrl + 2` |
| **Split-vy** | `Ctrl + 3` |
| **Analys & Nyckeltal** | `Ctrl + 4` |
| **Växla tema** | `Ctrl + T` |
| **Hjälp-dialog** | `F1` |
| **Textmallsmakron** | t.ex. `Ctrl + Alt + 1` |

*Obs: Alla kortkommandon kan anpassas i inställningarna (`⚙ Profil & Inställningar` -> `⌨ Kortkommandon`).*
"""
    },
    "storage_paths": {
        "title": "📁 Lagringsplatser & Sökvägar",
        "category": "Konfiguration",
        "content": """### 📁 Lagringsplatser, Datastruktur & EXE-körning

**Support-Cockpit** håller applikationsdata separerade från programfiler. Detta möjliggör säker körning från en enda exekverbar fil (PyInstaller `.exe`).

#### 1. Datamapp & sökvägar
- Öppna **Profil & Inställningar** (`👤 [Ditt namn]`) -> **📁 Lagring & Sökvägar**.
- **Huvuddatamapp**: Klicka på **📁 Välj mapp** för att ange din arbetsyta (t.ex. `D:\\SupportData`).
- **Enskilda filsökvägar**: Koppla enskilda filer (`cases.json`, `customers.json`) till andra platser vid behov.

#### 2. Körning som enkel fil (.exe)
- När appen körs som en kompilerad `.exe` skapas inga mappar i körningskatalogen.
- Istället sparas konfigurationen i din användarprofil:
  - Windows: `%APPDATA%\\SupportCockpit\\user_config.json`
  - Linux/Mac: `~/.config/SupportCockpit/user_config.json`

#### 3. Exempelfiler
- Exempelfiler från `data_examples/` kopieras automatiskt till din datamapp vid första starten.
"""
    },
    "template_editor": {
        "title": "📄 Redigerare för exportmallar",
        "category": "Export",
        "content": """### 📄 Skapa & anpassa exportmallar

I **Redigeraren för exportmallar** kan du anpassa befintliga överlämningsmallar eller definiera helt nya exportformat.

#### Öppna mallhanteraren
- Klicka på **📄 Mallar** i menyraden eller **🛠 Hantera mallar** i exportdialogen (`Ctrl+E`).

#### Konfigurera mall
1. **Namn & ID**: Ange ett unikt ID och ett läsbart visningsnamn.
2. **Målåtgärd**: Välj mellan text till urklipp och filexport.
3. **Tilldelade scheman**: Välj vilka formulärscheman mallen ska erbjudas för.
4. **Obligatoriska fält**: Ange vilka fält som måste fyllas i innan export tillåts.
5. **Jinja2-mall**: Skriv malltexten i Markdown/HTML och förhandsgranska direkt!
"""
    },
    "handover_followup": {
        "title": "🔔 Överlämningar & Uppföljningar",
        "category": "Arbetsflöde",
        "content": """### 🔔 Ansvarsöverlämning & Uppföljningspåminnelser

Håll alltid koll på när ett ärende överlämnades till vem och när det är dags att följa upp.

#### 1. Automatisk överlämningsloggning
- När du ändrar **Ansvarig (Aktör)** för ett ärende (t.ex. från *Support* till *Utveckling*) skapas automatiskt en post i **tidslinjen**.

#### 2. Planera uppföljning
- Klicka på **🔔 Uppföljning** i ärendedetaljerna.
- Välj en snabbinställning (`+ 1 dag`, `+ 2 dagar`, `+ 1 vecka`) eller ett valfritt datum med en anteckning.
- Ärenden med aktiv uppföljning framhävs i ärendelistan.
"""
    },
    "email_calendar_outlook": {
        "title": "✉ E-post, Kalender (.ics) & Outlook",
        "category": "Kommunikation",
        "content": """### ✉ Skriva e-post, Kalenderexport & Microsoft Outlook-integration

Två separata funktioner finns tillgängliga i Cockpit:

#### 1. ✉ Skriva e-post
- Klicka på **✉ E-post** för att öppna e-postutkastet för det aktuella ärendet.
- Mottagare och ämne förifylls utifrån klinikdata.
- Klicka på **🧩 Textmall** för att infoga färdiga supportmallar.
- **Överför till Outlook**: Öppnar e-postmeddelandet direkt i Microsoft Outlook.

#### 2. 📅 Skapa kalenderhändelse (.ics)
- Klicka på **📅 Kalender** för att generera en kalenderbokning för uppföljning eller återuppringningsfrist.
- **Spara som .ics-fil...**: Sparar händelsefilen på valfri plats.
"""
    },
    "case_print_reporting": {
        "title": "🖨 Utskrift, PDF & Bilder",
        "category": "Export",
        "content": """### 🖨 Ärendreutskrift & PDF-export

Skapa fullständiga ärendeöversikter för arkivering eller möten.

#### 1. Öppna utskriftsdialog
- Klicka på **🖨 Skriv ut** i Cockpit.
- Välj vilka avsnitt som ska ingå (kunddata, formulärfält, tidslinje, bilder).

#### 2. Bilder & Skärmdumpar
- Alla bildfiler (`.png`, `.jpg`, `.webp`) bäddas automatiskt in i slutet av dokumentet.

#### 3. Exportalternativ
- **🖨 Öppna i webbläsare & skriv ut**: Öppnar sidan i standardwebbläsaren och startar utskriftsdialogen.
- **💾 Spara som HTML/PDF-rapport...**: Sparar rapporten på din hårddisk.
"""
    },
    "ai_ollama_management": {
        "title": "🤖 AI-assistent, Ollama-server & Modellhantering",
        "category": "AI & Ollama",
        "content": """### 🤖 Lokal AI-supportassistent & Ollama-serverstyring

Support-Cockpit erbjuder 100 % integritetssäker AI-hjälp baserad på lokala öppen källkod-modeller (t.ex. Ollama med Qwen2.5 / Llama3). Alla förfrågningar stannar 100 % på din dator!

#### 1. ⚙ Hantera Ollama-server
Under **Profil & Inställningar** (`👤`) -> **🤖 AI & NLP** kan du starta och stoppa Ollama-servern direkt.

#### 2. ⚡ Skapa PVS-supportmodell med ett klick
- Klicka på **`⚡ Skapa PVS-supportmodell från Modelfile`** för att generera en specialiserad modell (`pvs-support`).

#### 3. 🎚 Global AI-brytare
- Inaktivera AI när som helst med den globala brytaren. Att inaktivera laddar automatiskt ur modellen från RAM.
"""
    },
    "stepper_time_picker": {
        "title": "⏱ Tidsval (07:00-20:00) & Stegarpilar",
        "category": "Användargränssnitt",
        "content": """### ⏱ Interaktiv tidsväljare

Optimering av tidsval för klinikers arbetstider (07:00 till 20:00) med snabba piltangenter (`▲` / `▼`).
"""
    },
    "internal_cases": {
        "title": "🏢 Interna ärenden & uppgifter (Utan kund)",
        "category": "Arbetsflöde",
        "content": """### 🏢 Interna ärenden & underuppgifter

Förutom kundrelaterade supportärenden kan du hantera **rent interna uppgifter** (t.ex. serverunderhåll, systemuppdateringar, anteckningar).

#### Funktioner:
- **Ingen kund krävs**: Välj *\"🏢 Internt ärende / Ingen klinik\"*.
- **Visuell markering**: Interna ärenden får en blå **`🏢 INTERNT`**-bricka i ärendelistan.
"""
    },
    "cobra_crm_import": {
        "title": "🐍 Cobra CRM Klinik- & Kundimport",
        "category": "Kunder",
        "content": """### 🐍 Cobra CRM Importassistent

Importera din kunddatabas direkt från Cobra CRM-exporter (`.csv`, `.txt`, `.json`).

#### Arbetsflöde:
1. Öppna Klinikhantering (**🏥 Kliniker**).
2. Klicka på **🐍 Cobra CRM Import...**.
3. Välj fil och bekräfta fältkopplingen.
"""
    },
    "snippets_manager": {
        "title": "📝 Textmallar & Mallsystem",
        "category": "Kommunikation",
        "content": """### 📝 Hantera & infoga textmallar

Spara tid vid återkommande svar med den inbyggda mallhanteraren.

#### 1. Hantera textmallar
- Klicka på **📝 Textmallar** i huvudmenyn för att skapa nya mallar med rubrik, kategori och taggar.

#### 2. Infoga mallar i anteckningar eller e-post
- Klicka på **🧩 Textmall** i e-postdialogen för att välja och infoga mallen vid markören.
"""
    },
    "repeatable_sub_forms": {
        "title": "📂 Dynamiska fler-kortsformulär",
        "category": "Formulär",
        "content": """### 📂 Dynamiska fler-kortsformulär (Upprepningsbara block)

Vissa formulärtyper tillåter registrering av flera oberoende förfrågningar i ett enda ärende (t.ex. flera fakturor eller filer).
"""
    },
    "analytics_kpi_dashboard": {
        "title": "Analys- & KPI-panel",
        "category": "Analys",
        "content": """### Analys- & KPI-panel

Få omfattande insikter i din supportprestanda och nyckeltal med ett ögonkast.

#### Huvudnyckeltal:
- **📋 Ärenden totalt**: Totalt antal registrerade ärenden.
- **⏳ Öppna ärenden**: Ärenden som pågår eller väntar.
- **✓ Klara (%)**: Antal klara ärenden med procentuell andel.
- **⏱ Genomsnittlig handläggningstid**: Genomsnittlig tid från skapande till färdigställande.
"""
    },
    "advanced_search_filters": {
        "title": "🔍 Avancerat söksystem & söksymboler",
        "category": "Grundläggande",
        "content": """### 🔍 Avancerade sökfilter & söksymboler

Sökfältet stöder kombinerbara söksymboler som `is:internal`, `vip:true`, `reminder:due` och `actor:dev`.
"""
    },
    "attachments_and_screenshots": {
        "title": "📂 Bilagor & Skärmdumpar (Ctrl+V)",
        "category": "Dokument",
        "content": """### 📂 Bilagshantering & skärmdumpar

Klistra in skärmdumpar direkt med **`Ctrl + V`** och förhandsgranska loggfiler och bilder i bilagsraden.
"""
    },
    "zip_backup_restore": {
        "title": "📦 Komplett ZIP-säkerhetskopiering",
        "category": "Konfiguration",
        "content": """### 📦 Säkerhetskopiera & återställ arbetsyta

Säkerhetskopiera alla ärenden, kunder, scheman, mallar och bilagor i en enda komprimerad ZIP-fil under **Profil & Inställningar** (`👤`).
"""
    },
    "email_webhook_integration": {
        "title": "🔌 E-postimport & REST Webhooks (Jira/GitLab)",
        "category": "Integrationer",
        "content": """### 🔌 E-postimport & REST Webhooks

Anslut Support-Cockpit till externa system. Importera e-post via IMAP och utlös REST-webhooks för GitLab eller Jira.
"""
    }
}

en_data["help_content"] = en_help
sv_data["help_content"] = sv_help

save_json(de_path, de_data)
save_json(en_path, en_data)
save_json(sv_path, sv_data)

print("Successfully updated de.json, en.json, and sv.json with full help content and splash screen translations!")
