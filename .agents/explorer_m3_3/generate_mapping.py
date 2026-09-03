import json
from pathlib import Path

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

locales = {}
for lang in ("de", "en", "sv"):
    p = project_root / "locales" / f"{lang}.json"
    with open(p, "r", encoding="utf-8") as f:
        locales[lang] = json.load(f)

def get_nested(d, key):
    parts = key.split(".")
    curr = d
    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        else:
            return None
    return curr

# Proposed missing keys catalog for M3 UI Views & Widgets
M3_KEYS_PROPOSAL = [
    # app.py / app_dialogs.py
    {
        "key": "app.zip_backup_title",
        "category": "app",
        "de": "Komplett-Datensicherung als ZIP speichern",
        "en": "Save full data backup as ZIP",
        "sv": "Spara fullständig säkerhetskopia som ZIP",
        "source": "src/ui/app.py:688 (asksaveasfilename title)"
    },
    {
        "key": "app.zip_filetypes",
        "category": "app",
        "de": "ZIP-Archiv",
        "en": "ZIP Archive",
        "sv": "ZIP-arkiv",
        "source": "src/ui/app.py:690"
    },
    {
        "key": "app.followup_due_toast_title",
        "category": "app",
        "de": "🔔 Wiedervorlage fällig ({count})",
        "en": "🔔 Follow-up due ({count})",
        "sv": "🔔 Uppföljning förfallen ({count})",
        "source": "src/ui/app.py:725"
    },
    {
        "key": "app.timeline_followup_set",
        "category": "app_dialogs",
        "de": "Wiedervorlage gesetzt auf: {date}. {note}",
        "en": "Follow-up set to: {date}. {note}",
        "sv": "Uppföljning satt till: {date}. {note}",
        "source": "src/ui/app_dialogs.py:53"
    },
    {
        "key": "app.timeline_case_completed",
        "category": "app_dialogs",
        "de": "Fall auf erledigt gesetzt.",
        "en": "Case marked as completed.",
        "sv": "Ärendet markerat som klart.",
        "source": "src/ui/app_dialogs.py:68"
    },
    {
        "key": "app.timeline_status_completed",
        "category": "app_dialogs",
        "de": "STATUS: Erledigt",
        "en": "STATUS: Completed",
        "sv": "STATUS: Klart",
        "source": "src/ui/app_dialogs.py:69"
    },
    {
        "key": "app.timeline_case_reopened",
        "category": "app_dialogs",
        "de": "Fall wieder geöffnet.",
        "en": "Case reopened.",
        "sv": "Ärendet återöppnat.",
        "source": "src/ui/app_dialogs.py:71"
    },
    {
        "key": "app.timeline_status_open",
        "category": "app_dialogs",
        "de": "STATUS: Offen",
        "en": "STATUS: Open",
        "sv": "STATUS: Öppen",
        "source": "src/ui/app_dialogs.py:72"
    },
    {
        "key": "app.timeline_handover_note",
        "category": "app_dialogs",
        "de": "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}",
        "en": "Responsibility handed over to: {actor}{person} via {channel}{note}",
        "sv": "Ansvar överlämnat till: {actor}{person} via {channel}{note}",
        "source": "src/ui/app_dialogs.py:101"
    },
    {
        "key": "app.timeline_handover_status",
        "category": "app_dialogs",
        "de": "ZUSTÄNDIGKEIT: {prev} -> {next}",
        "en": "RESPONSIBILITY: {prev} -> {next}",
        "sv": "ANSVAR: {prev} -> {next}",
        "source": "src/ui/app_dialogs.py:102"
    },

    # analytics_view.py
    {
        "key": "analytics.days_format",
        "category": "analytics",
        "de": "{days:.1f} Tage",
        "en": "{days:.1f} days",
        "sv": "{days:.1f} dagar",
        "source": "src/ui/views/analytics_view.py:93"
    },
    {
        "key": "analytics.hours_format",
        "category": "analytics",
        "de": "{hours:.1f} Std",
        "en": "{hours:.1f} hrs",
        "sv": "{hours:.1f} tim",
        "source": "src/ui/views/analytics_view.py:96"
    },
    {
        "key": "analytics.na",
        "category": "analytics",
        "de": "n/a",
        "en": "n/a",
        "sv": "ej tillgängligt",
        "source": "src/ui/views/analytics_view.py:98"
    },
    {
        "key": "analytics.urgency_red",
        "category": "analytics",
        "de": "🔴 Rot (Kritisch): {count} ({pct:.0f}%)",
        "en": "🔴 Red (Critical): {count} ({pct:.0f}%)",
        "sv": "🔴 Röd (Kritisk): {count} ({pct:.0f}%)",
        "source": "src/ui/views/analytics_view.py:141"
    },
    {
        "key": "analytics.urgency_yellow",
        "category": "analytics",
        "de": "🟡 Gelb (Mittel): {count} ({pct:.0f}%)",
        "en": "🟡 Yellow (Medium): {count} ({pct:.0f}%)",
        "sv": "🟡 Gul (Medel): {count} ({pct:.0f}%)",
        "source": "src/ui/views/analytics_view.py:142"
    },
    {
        "key": "analytics.urgency_green",
        "category": "analytics",
        "de": "🟢 Grün (Normal): {count} ({pct:.0f}%)",
        "en": "🟢 Green (Normal): {count} ({pct:.0f}%)",
        "sv": "🟢 Grön (Normal): {count} ({pct:.0f}%)",
        "source": "src/ui/views/analytics_view.py:143"
    },
    {
        "key": "analytics.schema_cases_item",
        "category": "analytics",
        "de": "• {name}: {count} Fälle ({pct:.0f}%)",
        "en": "• {name}: {count} cases ({pct:.0f}%)",
        "sv": "• {name}: {count} ärenden ({pct:.0f}%)",
        "source": "src/ui/views/analytics_view.py:161"
    },
    {
        "key": "analytics.practice_ranking_item",
        "category": "analytics",
        "de": "{idx}. {name}{vip} — {count} Vorgänge",
        "en": "{idx}. {name}{vip} — {count} cases",
        "sv": "{idx}. {name}{vip} — {count} ärenden",
        "source": "src/ui/views/analytics_view.py:180"
    },
    {
        "key": "analytics.assignee_workload_item",
        "category": "analytics",
        "de": "• {assignee}: {open} offen, {done} erledigt",
        "en": "• {assignee}: {open} open, {done} completed",
        "sv": "• {assignee}: {open} öppna, {done} klara",
        "source": "src/ui/views/analytics_view.py:199"
    },
    {
        "key": "analytics.dept_cases_item",
        "category": "analytics",
        "de": "• {dept}: {count} Fälle",
        "en": "• {dept}: {count} cases",
        "sv": "• {dept}: {count} ärenden",
        "source": "src/ui/views/analytics_view.py:213"
    },
    {
        "key": "analytics.copied_message",
        "category": "analytics",
        "de": "Statistik-Bericht wurde in die Zwischenablage kopiert.",
        "en": "Statistical report has been copied to clipboard.",
        "sv": "Statistikrapporten har kopierats till urklipp.",
        "source": "src/ui/views/analytics_view.py:272"
    },

    # board_view.py
    {
        "key": "board.score_label",
        "category": "board",
        "de": "Score {score}",
        "en": "Score {score}",
        "sv": "Poäng {score}",
        "source": "src/ui/views/board_view.py:46"
    },
    {
        "key": "board.header_support_count",
        "category": "board",
        "de": "📥 Support ({count})",
        "en": "📥 Support ({count})",
        "sv": "📥 Support ({count})",
        "source": "src/ui/views/board_view.py:314"
    },
    {
        "key": "board.header_dev_count",
        "category": "board",
        "de": "💻 Entwickler ({count})",
        "en": "💻 Developer ({count})",
        "sv": "💻 Utvecklare ({count})",
        "source": "src/ui/views/board_view.py:315"
    },
    {
        "key": "board.header_followup_count",
        "category": "board",
        "de": "🔔 Wiedervorlage ({count})",
        "en": "🔔 Follow-up ({count})",
        "sv": "🔔 Uppföljning ({count})",
        "source": "src/ui/views/board_view.py:316"
    },
    {
        "key": "board.header_completed_count",
        "category": "board",
        "de": "✓ Erledigt ({count})",
        "en": "✓ Completed ({count})",
        "sv": "✓ Klart ({count})",
        "source": "src/ui/views/board_view.py:317"
    },

    # cockpit_layout_builders.py & cockpit_view.py
    {
        "key": "cockpit.followup_at_hdr",
        "category": "cockpit",
        "de": "🔔 Nachfragen am:",
        "en": "🔔 Follow-up on:",
        "sv": "🔔 Följ upp den:",
        "source": "src/ui/views/cockpit_layout_builders.py:158, cockpit_view.py:533"
    },
    {
        "key": "cockpit.status_completed_tag",
        "category": "cockpit",
        "de": "  [✓ ERLEDIGT]",
        "en": "  [✓ COMPLETED]",
        "sv": "  [✓ KLART]",
        "source": "src/ui/views/cockpit_view.py:242"
    },
    {
        "key": "cockpit.customer_internal",
        "category": "cockpit",
        "de": "🏢 Kunde: INTERNE AUFGABE / VORGANG ({id}){vip}",
        "en": "🏢 Customer: INTERNAL TASK / CASE ({id}){vip}",
        "sv": "🏢 Kund: INTERNT ÄRENDE / UPPGIFT ({id}){vip}",
        "source": "src/ui/views/cockpit_view.py:259"
    },
    {
        "key": "cockpit.customer_practice",
        "category": "cockpit",
        "de": "🏥 Kunde: {name} ({id}){vip}",
        "en": "🏥 Customer: {name} ({id}){vip}",
        "sv": "🏥 Kund: {name} ({id}){vip}",
        "source": "src/ui/views/cockpit_view.py:261"
    },
    {
        "key": "cockpit.contact_person",
        "category": "cockpit",
        "de": "👤 Ansprechpartner: {contact}{address}",
        "en": "👤 Contact Person: {contact}{address}",
        "sv": "👤 Kontaktperson: {contact}{address}",
        "source": "src/ui/views/cockpit_view.py:265"
    },
    {
        "key": "cockpit.reopen",
        "category": "cockpit",
        "de": "✓ Wieder öffnen",
        "en": "✓ Reopen",
        "sv": "✓ Återöppna",
        "source": "src/ui/views/cockpit_view.py:270, 453"
    },
    {
        "key": "cockpit.email_copied_message",
        "category": "cockpit",
        "de": "Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.",
        "en": "Practice email '{email}' has been copied to clipboard.",
        "sv": "Mottagningens e-post '{email}' har kopierats till urklipp.",
        "source": "src/ui/views/cockpit_view.py:329"
    },
    {
        "key": "cockpit.no_email_message",
        "category": "cockpit",
        "de": "Für diese Praxis ist keine E-Mail-Adresse hinterlegt.",
        "en": "No email address registered for this practice.",
        "sv": "Ingen e-postadress är registrerad för denna mottagning.",
        "source": "src/ui/views/cockpit_view.py:337"
    },

    # table_view.py
    {
        "key": "table.case_details_header",
        "category": "table",
        "de": "📋 Falldetails: {id} - {practice} ({title})",
        "en": "📋 Case Details: {id} - {practice} ({title})",
        "sv": "📋 Ärendedetaljer: {id} - {practice} ({title})",
        "source": "src/ui/views/table_view.py:302"
    },

    # attachment_widget.py
    {
        "key": "attachments.image_preview_info",
        "category": "attachments",
        "de": "🖼 Bild Vorschau: {name}\nAuflösung: {width} x {height} px | Format: {format}",
        "en": "🖼 Image Preview: {name}\nResolution: {width} x {height} px | Format: {format}",
        "sv": "🖼 Bildförhandsvisning: {name}\nUpplösning: {width} x {height} px | Format: {format}",
        "source": "src/ui/widgets/attachment_widget.py:136"
    },
    {
        "key": "attachments.image_preview_error",
        "category": "attachments",
        "de": "Bild-Vorschau nicht verfügbar: {err}",
        "en": "Image preview not available: {err}",
        "sv": "Bildförhandsvisning ej tillgänglig: {err}",
        "source": "src/ui/widgets/attachment_widget.py:139"
    },
    {
        "key": "attachments.text_preview_error",
        "category": "attachments",
        "de": "Text-Vorschau Fehler: {err}",
        "en": "Text preview error: {err}",
        "sv": "Textförhandsvisningsfel: {err}",
        "source": "src/ui/widgets/attachment_widget.py:149"
    },
    {
        "key": "attachments.generic_preview_info",
        "category": "attachments",
        "de": "📄 Vorschau für '{name}' (Doppelklick zum Öffnen im OS)",
        "en": "📄 Preview for '{name}' (Double-click to open in OS)",
        "sv": "📄 Förhandsgranskning för '{name}' (Dubbelklicka för att öppna i OS)",
        "source": "src/ui/widgets/attachment_widget.py:151"
    },
    {
        "key": "attachments.select_file_dialog_title",
        "category": "attachments",
        "de": "Datei zum Anhängen auswählen",
        "en": "Select file to attach",
        "sv": "Välj fil att bifoga",
        "source": "src/ui/widgets/attachment_widget.py:177"
    },

    # case_list_widget.py
    {
        "key": "case_list.count_format",
        "category": "case_list",
        "de": "{count} Support-Fälle",
        "en": "{count} Support Cases",
        "sv": "{count} Supportärenden",
        "source": "src/ui/widgets/case_list_widget.py:131"
    },
    {
        "key": "case_list.score_pts",
        "category": "case_list",
        "de": "Pkt.: {score}",
        "en": "Pts: {score}",
        "sv": "Pkt: {score}",
        "source": "src/ui/widgets/case_list_widget.py:177"
    },
    {
        "key": "case_list.internal_task",
        "category": "case_list",
        "de": "🏢 INTERNE AUFGABE / VORGANG",
        "en": "🏢 INTERNAL TASK / CASE",
        "sv": "🏢 INTERNT ÄRENDE / UPPGIFT",
        "source": "src/ui/widgets/case_list_widget.py:208"
    },
    {
        "key": "case_list.actor_format",
        "category": "case_list",
        "de": "{title} | Zuständig: {actor}",
        "en": "{title} | Assigned: {actor}",
        "sv": "{title} | Ansvarig: {actor}",
        "source": "src/ui/widgets/case_list_widget.py:232"
    },
    {
        "key": "case_list.tooltip_case_header",
        "category": "case_list",
        "de": "📌 Fall: {id} (Priorität: {score} Pkt.)",
        "en": "📌 Case: {id} (Priority: {score} pts)",
        "sv": "📌 Ärende: {id} (Prioritet: {score} pkt)",
        "source": "src/ui/widgets/case_list_widget.py:371"
    },
    {
        "key": "case_list.tooltip_customer_internal",
        "category": "case_list",
        "de": "🏢 Kunde: INTERNE AUFGABE ({id})",
        "en": "🏢 Customer: INTERNAL TASK ({id})",
        "sv": "🏢 Kund: INTERNT ÄRENDE ({id})",
        "source": "src/ui/widgets/case_list_widget.py:374"
    },
    {
        "key": "case_list.tooltip_customer_practice",
        "category": "case_list",
        "de": "🏥 Kunde: {name} ({id}){vip}",
        "en": "🏥 Customer: {name} ({id}){vip}",
        "sv": "🏥 Kund: {name} ({id}){vip}",
        "source": "src/ui/widgets/case_list_widget.py:377"
    },
    {
        "key": "case_list.tooltip_contact",
        "category": "case_list",
        "de": "👤 Ansprechpartner: {contact}",
        "en": "👤 Contact Person: {contact}",
        "sv": "👤 Kontaktperson: {contact}",
        "source": "src/ui/widgets/case_list_widget.py:378"
    },
    {
        "key": "case_list.tooltip_topic",
        "category": "case_list",
        "de": "📋 Thema: {title}",
        "en": "📋 Topic: {title}",
        "sv": "📋 Ämne: {title}",
        "source": "src/ui/widgets/case_list_widget.py:380"
    },
    {
        "key": "case_list.tooltip_assigned",
        "category": "case_list",
        "de": "👤 Zuständig: {actor}",
        "en": "👤 Assigned: {actor}",
        "sv": "👤 Ansvarig: {actor}",
        "source": "src/ui/widgets/case_list_widget.py:381"
    },
    {
        "key": "case_list.tooltip_followup",
        "category": "case_list",
        "de": "🔔 Wiedervorlage: {date} um {time}{note}",
        "en": "🔔 Follow-up: {date} at {time}{note}",
        "sv": "🔔 Uppföljning: {date} kl {time}{note}",
        "source": "src/ui/widgets/case_list_widget.py:388"
    },
    {
        "key": "case_list.tooltip_tags",
        "category": "case_list",
        "de": "🏷 Tags: {tags}",
        "en": "🏷 Tags: {tags}",
        "sv": "🏷 Taggar: {tags}",
        "source": "src/ui/widgets/case_list_widget.py:391"
    },

    # date_picker.py
    {
        "key": "date_picker.dialog_title",
        "category": "date_picker",
        "de": "📅 Datum auswählen",
        "en": "📅 Select Date",
        "sv": "📅 Välj datum",
        "source": "src/ui/widgets/date_picker.py:23"
    },
    {
        "key": "date_picker.preset_today_1130",
        "category": "date_picker",
        "de": "Heute 11:30",
        "en": "Today 11:30",
        "sv": "Idag 11:30",
        "source": "src/ui/widgets/date_picker.py:225"
    },
    {
        "key": "date_picker.preset_today_1330",
        "category": "date_picker",
        "de": "Heute 13:30",
        "en": "Today 13:30",
        "sv": "Idag 13:30",
        "source": "src/ui/widgets/date_picker.py:226"
    },
    {
        "key": "date_picker.preset_today_1630",
        "category": "date_picker",
        "de": "Heute 16:30",
        "en": "Today 16:30",
        "sv": "Idag 16:30",
        "source": "src/ui/widgets/date_picker.py:227"
    },
    {
        "key": "date_picker.preset_tomorrow_8am",
        "category": "date_picker",
        "de": "Morgen 08:00",
        "en": "Tomorrow 08:00",
        "sv": "Imorgon 08:00",
        "source": "src/ui/widgets/date_picker.py:228"
    },
    {
        "key": "date_picker.preset_plus_1_day",
        "category": "date_picker",
        "de": "+ 1 Tag",
        "en": "+ 1 Day",
        "sv": "+ 1 dag",
        "source": "src/ui/widgets/date_picker.py:229"
    },
    {
        "key": "date_picker.preset_plus_1_week",
        "category": "date_picker",
        "de": "+ 1 Woche",
        "en": "+ 1 Week",
        "sv": "+ 1 vecka",
        "source": "src/ui/widgets/date_picker.py:230"
    },

    # dynamic_form_field_renderers.py & dynamic_form_widget.py
    {
        "key": "dynamic_form.no_mod_selected",
        "category": "dynamic_form",
        "de": "🧩 Keinen Programmbereich ausgewählt ▾",
        "en": "🧩 No module selected ▾",
        "sv": "🧩 Ingen modul vald ▾",
        "source": "src/ui/widgets/dynamic_form_field_renderers.py:84"
    },
    {
        "key": "dynamic_form.more_mods_suffix",
        "category": "dynamic_form",
        "de": " (+{count} weitere)",
        "en": " (+{count} more)",
        "sv": " (+{count} fler)",
        "source": "src/ui/widgets/dynamic_form_field_renderers.py:90"
    },
    {
        "key": "dynamic_form.select_file_for",
        "category": "dynamic_form",
        "de": "Datei auswählen für '{label}'",
        "en": "Select file for '{label}'",
        "sv": "Välj fil för '{label}'",
        "source": "src/ui/widgets/dynamic_form_field_renderers.py:266"
    },
    {
        "key": "dynamic_form.remove_card",
        "category": "dynamic_form",
        "de": "🗑 Anfrage #{idx} entfernen",
        "en": "🗑 Remove request #{idx}",
        "sv": "🗑 Ta bort förfrågan #{idx}",
        "source": "src/ui/widgets/dynamic_form_widget.py:437"
    },
    {
        "key": "dynamic_form.add_card",
        "category": "dynamic_form",
        "de": "➕ Weitere {title} anfordern",
        "en": "➕ Request another {title}",
        "sv": "➕ Begär ytterligare {title}",
        "source": "src/ui/widgets/dynamic_form_widget.py:462"
    },
    {
        "key": "dynamic_form.import_db_backup_title",
        "category": "dynamic_form",
        "de": "Datenbank-Backup (.backup) importieren",
        "en": "Import database backup (.backup)",
        "sv": "Importera databas-backup (.backup)",
        "source": "src/ui/widgets/dynamic_form_widget.py:533"
    },
    {
        "key": "dynamic_form.backup_filetypes",
        "category": "dynamic_form",
        "de": "Backup-Dateien (*.backup)",
        "en": "Backup Files (*.backup)",
        "sv": "Säkerhetskopior (*.backup)",
        "source": "src/ui/widgets/dynamic_form_widget.py:534"
    },

    # common / shared
    {
        "key": "common.general",
        "category": "common",
        "de": "Allgemein",
        "en": "General",
        "sv": "Allmänt",
        "source": "src/ui/views/analytics_view.py:154"
    },
    {
        "key": "common.unassigned",
        "category": "common",
        "de": "Nicht zugewiesen",
        "en": "Unassigned",
        "sv": "Inte tilldelad",
        "source": "src/ui/views/analytics_view.py:190"
    },
    {
        "key": "common.all_files",
        "category": "common",
        "de": "Alle Dateien",
        "en": "All Files",
        "sv": "Alla filer",
        "source": "src/ui/widgets/dynamic_form_widget.py:534"
    },
    {
        "key": "common.please_select",
        "category": "common",
        "de": "– Bitte auswählen –",
        "en": "– Please select –",
        "sv": "– Vänligen välj –",
        "source": "src/ui/widgets/searchable_combobox.py:15"
    }
]

# Check against existing locales
existing_keys = {lang: set() for lang in locales}
def collect_keys(d, prefix=""):
    keys = set()
    for k, v in d.items():
        fk = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(collect_keys(v, fk))
        else:
            keys.add(fk)
    return keys

for lang in locales:
    existing_keys[lang] = collect_keys(locales[lang])

mapping_audit = []
for item in M3_KEYS_PROPOSAL:
    k = item["key"]
    in_de = k in existing_keys["de"]
    in_en = k in existing_keys["en"]
    in_sv = k in existing_keys["sv"]
    mapping_audit.append({
        **item,
        "exists_in_de": in_de,
        "exists_in_en": in_en,
        "exists_in_sv": in_sv,
        "needs_addition": not (in_de and in_en and in_sv)
    })

needs_add = [m for m in mapping_audit if m["needs_addition"]]
print(f"Total proposed M3 keys: {len(mapping_audit)}")
print(f"Keys needing addition across de/en/sv: {len(needs_add)}")

with open(project_root / ".agents" / "explorer_m3_3" / "m3_keys_mapping.json", "w", encoding="utf-8") as f:
    json.dump({
        "total_proposed": len(mapping_audit),
        "needs_addition_count": len(needs_add),
        "keys": mapping_audit
    }, f, indent=2, ensure_ascii=False)
