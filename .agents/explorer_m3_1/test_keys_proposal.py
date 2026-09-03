import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

new_keys = {
    "app": {
        "window_title": ("Support-Cockpit & Ticket Management", "Support Cockpit & Ticket Management", "Support Cockpit & Ärendehantering")
    },
    "file_types": {
        "zip_archive": ("ZIP-Archiv", "ZIP Archive", "ZIP-arkiv")
    },
    "dialog_titles": {
        "zip_export": ("Komplett-Datensicherung als ZIP speichern", "Save full data backup as ZIP", "Spara fullständig säkerhetskopia som ZIP")
    },
    "toast": {
        "followup_due_title": ("🔔 Wiedervorlage fällig ({count})", "🔔 Follow-up due ({count})", "🔔 Uppföljning förfallen ({count})")
    },
    "timeline": {
        "followup_set_note": ("Wiedervorlage gesetzt auf: {date}. {note}", "Follow-up set to: {date}. {note}", "Uppföljning satt till: {date}. {note}"),
        "handover_note": ("Zuständigkeit übergeben an: {actor}{person} via {channel}{note}", "Responsibility transferred to: {actor}{person} via {channel}{note}", "Ansvar överfört till: {actor}{person} via {channel}{note}"),
        "handover_status": ("ZUSTÄNDIGKEIT: {prev} -> {curr}", "RESPONSIBILITY: {prev} -> {curr}", "ANSVAR: {prev} -> {curr}"),
        "case_completed": ("Fall auf erledigt gesetzt.", "Case marked as completed.", "Ärende markerat som slutfört."),
        "status_completed": ("STATUS: Erledigt", "STATUS: Completed", "STATUS: Slutförd"),
        "case_reopened": ("Fall wieder geöffnet.", "Case reopened.", "Ärende återöppnat."),
        "status_open": ("STATUS: Offen", "STATUS: Open", "STATUS: Öppen")
    },
    "cockpit": {
        "customer": ("Kunde", "Customer", "Kund"),
        "contact_person": ("Ansprechpartner", "Contact Person", "Kontaktperson"),
        "internal_task_title": ("INTERNE AUFGABE / VORGANG", "INTERNAL TASK / CASE", "INTERNT ÄRENDE / UPPGIFT"),
        "status_completed_tag": ("✓ ERLEDIGT", "✓ COMPLETED", "✓ SLUTFÖRD"),
        "reopen": ("✓ Wieder öffnen", "✓ Reopen", "✓ Återöppna"),
        "email_copied_msg": ("Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.", "Practice email '{email}' copied to clipboard.", "Mottagningens e-post '{email}' kopierades till urklipp.")
    },
    "board": {
        "score": ("Score", "Score", "Poäng"),
        "col_support_header": ("📥 Support / In Bearbeitung", "📥 Support / In Progress", "📥 Support / Pågående"),
        "col_dev_header": ("💻 Entwickler / Dev-Team", "💻 Developer / Dev Team", "💻 Utvecklare / Dev-team"),
        "col_followup_header": ("🔔 Wiedervorlage / Warten", "🔔 Follow-up / Waiting", "🔔 Uppföljning / Väntar"),
        "col_completed_header": ("✓ Erledigte Fälle", "✓ Completed Cases", "✓ Slutförda ärenden"),
        "expand_btn": ("▶", "▶", "▶"),
        "title_support": ("Support", "Support", "Support"),
        "title_dev": ("Entwickler", "Developer", "Utvecklare"),
        "title_followup": ("Wiedervorlage", "Follow-up", "Uppföljning"),
        "title_completed": ("Erledigt", "Completed", "Slutfört")
    },
    "table": {
        "tab_form": ("📝 Formular & Ausfüllen", "📝 Form & Data", "📝 Formulär & Fyll i"),
        "tab_timeline": ("🕒 Zeitleiste", "🕒 Timeline", "🕒 Tidslinje"),
        "tab_attachments": ("📎 Anhänge", "📎 Attachments", "📎 Bilagor")
    },
    "analytics": {
        "schema_general": ("Allgemein", "General", "Allmänt"),
        "cases_suffix": ("Fälle", "cases", "ärenden"),
        "cases_suffix_alt": ("Vorgänge", "cases", "ärenden"),
        "unassigned": ("Nicht zugewiesen", "Unassigned", "Ej tilldelad"),
        "open_suffix": ("offen", "open", "öppna"),
        "done_suffix": ("erledigt", "completed", "slutförda"),
        "report_header": ("# Support Cockpit — Statistik & Kennzahlen Bericht", "# Support Cockpit — Statistics & KPIs Report", "# Support Cockpit — Statistik & KPI-rapport"),
        "report_total_cases": ("**Fälle Gesamt:** {count}", "**Total Cases:** {count}", "**Totalt antal ärenden:** {count}"),
        "report_open_cases": ("**Offene Fälle:** {count}", "**Open Cases:** {count}", "**Öppna ärenden:** {count}"),
        "report_completed_cases": ("**Erledigte Fälle:** {count} ({pct:.1f}%)", "**Completed Cases:** {count} ({pct:.1f}%)", "**Slutförda ärenden:** {count} ({pct:.1f}%)"),
        "report_overdue_cases": ("**Überfällige Wiedervorlagen:** {count}", "**Overdue Follow-ups:** {count}", "**Förfallna uppföljningar:** {count}"),
        "report_vip_rate": ("**VIP-Kundenquote:** {pct:.1f}%\n", "**VIP Customer Rate:** {pct:.1f}%\n", "**VIP-kundandel:** {pct:.1f}%\n"),
        "report_urgency_title": ("### Dringlichkeits-Verteilung (Scoring):", "### Urgency Distribution (Scoring):", "### Brådskandefördelning (Scoring):"),
        "report_urgency_red": ("- Rot (Kritisch): {count}", "- Red (Critical): {count}", "- Röd (Kritisk): {count}"),
        "report_urgency_yellow": ("- Gelb (Mittel): {count}", "- Yellow (Medium): {count}", "- Gul (Medel): {count}"),
        "report_urgency_green": ("- Grün (Normal): {count}", "- Green (Normal): {count}", "- Grön (Normal): {count}"),
        "report_dept_title": ("### Offene Fälle nach Abteilung:", "### Open Cases by Department:", "### Öppna ärenden per avdelning:"),
        "report_dept_item": ("- {actor}: {count} Fälle", "- {actor}: {count} cases", "- {actor}: {count} ärenden")
    }
}

total = sum(len(v) for v in new_keys.values())
print(f"Total proposed new/mapped keys: {total}")
for sec, keys in new_keys.items():
    print(f"  [{sec}] ({len(keys)} keys)")
    for k, (de, en, sv) in keys.items():
        print(f"    {k}: DE='{de}' | EN='{en}' | SV='{sv}'")
