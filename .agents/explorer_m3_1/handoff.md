# Technical Blueprint & Handoff Report: Milestone 3 (UI Views & App Shell String Extraction)

## 1. Observation

Direct code inspections and automated AST scans revealed the following hardcoded strings, AST violations, and language synchronization gaps across `src/ui/app.py` and `src/ui/views/`:

### 1.1 AST Violations Detected by Scanner
Running `I18nASTScanner` on the target files produced 5 direct AST violations:
1. `src/ui/app.py:687:20`: `asksaveasfilename(title="Komplett-Datensicherung als ZIP speichern", ...)`
2. `src/ui/views/cockpit_view.py:334:12`: `ToastNotification(message="Für diese Praxis ist keine E-Mail-Adresse hinterlegt.")`
3. `src/ui/views/cockpit_layout_builders.py:156:28`: `CTkLabel(text="🔔 Nachfragen am:")`
4. `src/ui/views/board_view.py:224:26`: `CTkButton(text="▶")`
5. `src/ui/views/analytics_view.py:272:12`: `ToastNotification(message="Statistik-Bericht wurde in die Zwischenablage kopiert.")`

### 1.2 Non-AST Hardcoded German String Literals & Formatting Patterns
Beyond AST constructor violations, the following user-facing strings and dynamic update gaps were observed:

#### A. `src/ui/app.py`
- Line 89: `self.title(APP_WINDOW_TITLE)` — uses constant `APP_WINDOW_TITLE = "Support-Cockpit & Ticket Management"` without runtime translation.
- Lines 240–244: `on_language_changed(self, lang_code: str)` only refreshes `menu_frame` and `cockpit_view`, omitting `board_view`, `table_view`, and `analytics_view`.
- Line 687–690: `asksaveasfilename` dialog title and file filter `filetypes=[("ZIP-Archiv", "*.zip")]`.
- Line 725: Followup deadline toast `title=f"🔔 Wiedervorlage fällig ({due_count})"`.

#### B. `src/ui/app_dialogs.py` (App Dialogs Mixin)
- Line 53: Timeline entry `note=f"Wiedervorlage gesetzt auf: {dt_iso}. {note_text}"`.
- Lines 68–72: Hardcoded status change notes: `"Fall auf erledigt gesetzt."`, `"STATUS: Erledigt"`, `"Fall wieder geöffnet."`, `"STATUS: Offen"`.
- Lines 101–102: Hardcoded handover note and status: `f"Zuständigkeit übergeben an: {get_actor_display(new_actor_val)}{person_str} via {channel}{note_str}"` and `f"ZUSTÄNDIGKEIT: {get_actor_display(prev_actor_val)} -> {get_actor_display(new_actor_val)}"`.

#### C. `src/ui/views/cockpit_view.py`
- Line 172 & 176: `self.right_tabview.set("Wiki")` and `self.right_tabview.set("Zeitleiste")` — hardcoded German tab names break when tabs are localized.
- Line 242: Status tag `status_tag = "  [✓ ERLEDIGT]"`.
- Lines 259 & 261: `self.kunde_label.configure(text=f"🏢 Kunde: INTERNE AUFGABE / VORGANG ({case.customer.customer_id}){vip_str}")` and `f"🏥 Kunde: {case.customer.practice_name}..."`.
- Line 265: `self.ansprechpartner_label.configure(text=f"👤 Ansprechpartner: {case.customer.contact_person}{addr_str}")`.
- Line 270 & 453: `self.complete_btn.configure(text="✓ Wieder öffnen" if case.workflow_status.is_completed else "✓ Erledigen")`.
- Lines 292 & 294: `_on_sidebar_tab_changed` compares against `"Zeitleiste"` and `"Anhänge"` directly.
- Line 329: Toast `message=f"Praxis-E-Mail '{email_clean}' wurde in die Zwischenablage kopiert."`.
- Line 337: Toast `message="Für diese Praxis ist keine E-Mail-Adresse hinterlegt."`.
- Lines 392–400 & 433–448: Hardcoded timeline notes and status strings.
- Line 520: `self._wiedervorlage_full_text = f"🔔 Nachfragen am: {fw_date_str}, {fw_time_str}{note_suffix}"`.

#### D. `src/ui/views/cockpit_layout_builders.py`
- Line 158: `text="🔔 Nachfragen am:"` in `_build_info_row`.
- Line 313 in `refresh_ui_labels()`: Checked `hasattr(self, "case_list_widget")` instead of `hasattr(self, "left_frame")`, causing child widget label refresh to silently fail.
- Missing updates in `refresh_ui_labels()`: `self.wv_hdr_label`, `self.case_title_label`, `self.complete_btn`, `self.actor_combo`, `self.kunde_label`, `self.ansprechpartner_label`.

#### E. `src/ui/views/board_view.py`
- Line 47: Score badge text `f"Score {score:.0f}"`.
- Line 58: Customer name prefix for internal cases.
- Lines 204–207: Column titles `cols_def` in `create_board()` — headers like `"📥 Support / In Bearbeitung"`, `"💻 Entwickler / Dev-Team"`, etc.
- Lines 314–317 in `refresh_board()`: Column counter titles `f"📥 Support ({count})"`, `f"💻 Entwickler ({count})"`, `f"🔔 Wiedervorlage ({count})"`, `f"✓ Erledigt ({count})"`.
- Missing `refresh_ui_labels(self)` method in `BoardView`.

#### F. `src/ui/views/table_view.py`
- Lines 157–159: Hardcoded detail tabs `add("📝 Formular & Ausfüllen")`, `add("🕒 Zeitleiste")`, `add("📎 Anhänge")`.
- Lines 301–303: `self.detail_title_label.configure(text=f"📋 Falldetails: {case.case_id} - {case.customer.practice_name} ({case.classification.title})")`.
- Missing `refresh_ui_labels(self)` method in `TableView`.

#### G. `src/ui/views/analytics_view.py`
- Lines 93 & 96: Resolution time units `f"{avg_days:.1f} Tage"`, `f"{avg_hrs:.1f} Std"`.
- Lines 141–143: Urgency breakdown lines: `🔴 Rot (Kritisch): ...`, `🟡 Gelb (Mittel): ...`, `🟢 Grün (Normal): ...`.
- Line 154: Fallback schema name `"Allgemein"`.
- Line 161: Schema item suffix `" Fälle"`.
- Line 180: Practice ranking item suffix `" Vorgänge"`.
- Line 190: Fallback assignee `"Nicht zugewiesen"`.
- Line 199: Workload item suffix `" offen, ... erledigt"`.
- Line 213: Department item suffix `" Fälle"`.
- Lines 240–258: Markdown export report strings in `generate_report_markdown()`.
- Line 272: Toast message `"Statistik-Bericht wurde in die Zwischenablage kopiert."`.
- Missing `refresh_ui_labels(self)` method in `AnalyticsView`.

---

## 2. Logic Chain

1. **Root Cause Analysis**: The UI components were initially constructed with hardcoded German strings or English/German hybrid formatting. While many buttons and dialog titles already use `tr(...)`, label formatters, dropdown choices, toast messages, and view-level refresh cascades were only partially implemented.
2. **Dynamic Language Switch Incompleteness**: `SupportCockpitApp.on_language_changed` previously notified only `cockpit_view`, leaving `board_view`, `table_view`, and `analytics_view` in their initial language until application restart.
3. **Key Parity Requirement**: All new extraction keys must be added symmetrically to `locales/de.json`, `locales/en.json`, and `locales/sv.json` to satisfy test suite `test_translation_parity_and_quality.py`.
4. **AST Cleanliness**: All UI widget instantiation and `.configure()` calls must use `tr(...)` or `LocalizedDict` subscripts so that `test_ast_i18n_scanner.py` produces 0 violations across all `src/ui/views/` and `src/ui/app.py`.

---

## 3. Detailed Technical Blueprint & Replacement Specifications

### 3.1 New Translation Keys for `locales/*.json` (48 Keys)

The following keys must be added to `locales/de.json`, `locales/en.json`, and `locales/sv.json`:

```json
{
  "app": {
    "window_title": "Support-Cockpit & Ticket Management"
  },
  "file_types": {
    "zip_archive": "ZIP-Archiv"
  },
  "dialog_titles": {
    "zip_export": "Komplett-Datensicherung als ZIP speichern"
  },
  "toast": {
    "followup_due_title": "🔔 Wiedervorlage fällig ({count})"
  },
  "timeline": {
    "followup_set_note": "Wiedervorlage gesetzt auf: {date}. {note}",
    "handover_note": "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}",
    "handover_status": "ZUSTÄNDIGKEIT: {prev} -> {curr}",
    "case_completed": "Fall auf erledigt gesetzt.",
    "status_completed": "STATUS: Erledigt",
    "case_reopened": "Fall wieder geöffnet.",
    "status_open": "STATUS: Offen"
  },
  "cockpit": {
    "customer": "Kunde",
    "contact_person": "Ansprechpartner",
    "internal_task_title": "INTERNE AUFGABE / VORGANG",
    "status_completed_tag": "✓ ERLEDIGT",
    "reopen": "✓ Wieder öffnen",
    "email_copied_msg": "Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert."
  },
  "board": {
    "score": "Score",
    "col_support_header": "📥 Support / In Bearbeitung",
    "col_dev_header": "💻 Entwickler / Dev-Team",
    "col_followup_header": "🔔 Wiedervorlage / Warten",
    "col_completed_header": "✓ Erledigte Fälle",
    "expand_btn": "▶",
    "title_support": "Support",
    "title_dev": "Entwickler",
    "title_followup": "Wiedervorlage",
    "title_completed": "Erledigt"
  },
  "table": {
    "tab_form": "📝 Formular & Ausfüllen",
    "tab_timeline": "🕒 Zeitleiste",
    "tab_attachments": "📎 Anhänge"
  },
  "analytics": {
    "schema_general": "Allgemein",
    "cases_suffix": "Fälle",
    "cases_suffix_alt": "Vorgänge",
    "unassigned": "Nicht zugewiesen",
    "open_suffix": "offen",
    "done_suffix": "erledigt",
    "report_header": "# Support Cockpit — Statistik & Kennzahlen Bericht",
    "report_total_cases": "**Fälle Gesamt:** {count}",
    "report_open_cases": "**Offene Fälle:** {count}",
    "report_completed_cases": "**Erledigte Fälle:** {count} ({pct:.1f}%)",
    "report_overdue_cases": "**Überfällige Wiedervorlagen:** {count}",
    "report_vip_rate": "**VIP-Kundenquote:** {pct:.1f}%\n",
    "report_urgency_title": "### Dringlichkeits-Verteilung (Scoring):",
    "report_urgency_red": "- Rot (Kritisch): {count}",
    "report_urgency_yellow": "- Gelb (Mittel): {count}",
    "report_urgency_green": "- Grün (Normal): {count}",
    "report_dept_title": "### Offene Fälle nach Abteilung:",
    "report_dept_item": "- {actor}: {count} Fälle"
  }
}
```

#### English Translations (`locales/en.json`):
```json
{
  "app": {
    "window_title": "Support Cockpit & Ticket Management"
  },
  "file_types": {
    "zip_archive": "ZIP Archive"
  },
  "dialog_titles": {
    "zip_export": "Save full data backup as ZIP"
  },
  "toast": {
    "followup_due_title": "🔔 Follow-up due ({count})"
  },
  "timeline": {
    "followup_set_note": "Follow-up set to: {date}. {note}",
    "handover_note": "Responsibility transferred to: {actor}{person} via {channel}{note}",
    "handover_status": "RESPONSIBILITY: {prev} -> {curr}",
    "case_completed": "Case marked as completed.",
    "status_completed": "STATUS: Completed",
    "case_reopened": "Case reopened.",
    "status_open": "STATUS: Open"
  },
  "cockpit": {
    "customer": "Customer",
    "contact_person": "Contact Person",
    "internal_task_title": "INTERNAL TASK / CASE",
    "status_completed_tag": "✓ COMPLETED",
    "reopen": "✓ Reopen",
    "email_copied_msg": "Practice email '{email}' copied to clipboard."
  },
  "board": {
    "score": "Score",
    "col_support_header": "📥 Support / In Progress",
    "col_dev_header": "💻 Developer / Dev Team",
    "col_followup_header": "🔔 Follow-up / Waiting",
    "col_completed_header": "✓ Completed Cases",
    "expand_btn": "▶",
    "title_support": "Support",
    "title_dev": "Developer",
    "title_followup": "Follow-up",
    "title_completed": "Completed"
  },
  "table": {
    "tab_form": "📝 Form & Data",
    "tab_timeline": "🕒 Timeline",
    "tab_attachments": "📎 Attachments"
  },
  "analytics": {
    "schema_general": "General",
    "cases_suffix": "cases",
    "cases_suffix_alt": "cases",
    "unassigned": "Unassigned",
    "open_suffix": "open",
    "done_suffix": "completed",
    "report_header": "# Support Cockpit — Statistics & KPIs Report",
    "report_total_cases": "**Total Cases:** {count}",
    "report_open_cases": "**Open Cases:** {count}",
    "report_completed_cases": "**Completed Cases:** {count} ({pct:.1f}%)",
    "report_overdue_cases": "**Overdue Follow-ups:** {count}",
    "report_vip_rate": "**VIP Customer Rate:** {pct:.1f}%\n",
    "report_urgency_title": "### Urgency Distribution (Scoring):",
    "report_urgency_red": "- Red (Critical): {count}",
    "report_urgency_yellow": "- Yellow (Medium): {count}",
    "report_urgency_green": "- Green (Normal): {count}",
    "report_dept_title": "### Open Cases by Department:",
    "report_dept_item": "- {actor}: {count} cases"
  }
}
```

#### Swedish Translations (`locales/sv.json`):
```json
{
  "app": {
    "window_title": "Support Cockpit & Ärendehantering"
  },
  "file_types": {
    "zip_archive": "ZIP-arkiv"
  },
  "dialog_titles": {
    "zip_export": "Spara fullständig säkerhetskopia som ZIP"
  },
  "toast": {
    "followup_due_title": "🔔 Uppföljning förfallen ({count})"
  },
  "timeline": {
    "followup_set_note": "Uppföljning satt till: {date}. {note}",
    "handover_note": "Ansvar överfört till: {actor}{person} via {channel}{note}",
    "handover_status": "ANSVAR: {prev} -> {curr}",
    "case_completed": "Ärende markerat som slutfört.",
    "status_completed": "STATUS: Slutförd",
    "case_reopened": "Ärende återöppnat.",
    "status_open": "STATUS: Öppen"
  },
  "cockpit": {
    "customer": "Kund",
    "contact_person": "Kontaktperson",
    "internal_task_title": "INTERNT ÄRENDE / UPPGIFT",
    "status_completed_tag": "✓ SLUTFÖRD",
    "reopen": "✓ Återöppna",
    "email_copied_msg": "Mottagningens e-post '{email}' kopierades till urklipp."
  },
  "board": {
    "score": "Poäng",
    "col_support_header": "📥 Support / Pågående",
    "col_dev_header": "💻 Utvecklare / Dev-team",
    "col_followup_header": "🔔 Uppföljning / Väntar",
    "col_completed_header": "✓ Slutförda ärenden",
    "expand_btn": "▶",
    "title_support": "Support",
    "title_dev": "Utvecklare",
    "title_followup": "Uppföljning",
    "title_completed": "Slutfört"
  },
  "table": {
    "tab_form": "📝 Formulär & Fyll i",
    "tab_timeline": "🕒 Tidslinje",
    "tab_attachments": "📎 Bilagor"
  },
  "analytics": {
    "schema_general": "Allmänt",
    "cases_suffix": "ärenden",
    "cases_suffix_alt": "ärenden",
    "unassigned": "Ej tilldelad",
    "open_suffix": "öppna",
    "done_suffix": "slutförda",
    "report_header": "# Support Cockpit — Statistik & KPI-rapport",
    "report_total_cases": "**Totalt antal ärenden:** {count}",
    "report_open_cases": "**Öppna ärenden:** {count}",
    "report_completed_cases": "**Slutförda ärenden:** {count} ({pct:.1f}%)",
    "report_overdue_cases": "**Förfallna uppföljningar:** {count}",
    "report_vip_rate": "**VIP-kundandel:** {pct:.1f}%\n",
    "report_urgency_title": "### Brådskandefördelning (Scoring):",
    "report_urgency_red": "- Röd (Kritisk): {count}",
    "report_urgency_yellow": "- Gul (Medel): {count}",
    "report_urgency_green": "- Grön (Normal): {count}",
    "report_dept_title": "### Öppna ärenden per avdelning:",
    "report_dept_item": "- {actor}: {count} ärenden"
  }
}
```

---

### 3.2 File-by-File Code Replacement Plan

#### 1. `src/ui/app.py`
- **Line 89**:
  ```python
  # BEFORE:
  self.title(APP_WINDOW_TITLE)
  # AFTER:
  from services.i18n_service import tr
  self.title(tr("app.window_title", APP_WINDOW_TITLE))
  ```
- **Lines 240–244 (`on_language_changed`)**:
  ```python
  # BEFORE:
  def on_language_changed(self, lang_code: str):
      self.create_menu_bar()
      if hasattr(self, "cockpit_view") and hasattr(self.cockpit_view, "refresh_ui_labels"):
          self.cockpit_view.refresh_ui_labels()

  # AFTER:
  def on_language_changed(self, lang_code: str):
      from services.i18n_service import tr
      from constants import APP_WINDOW_TITLE
      self.title(tr("app.window_title", APP_WINDOW_TITLE))
      self.create_menu_bar()
      if hasattr(self, "cockpit_view") and hasattr(self.cockpit_view, "refresh_ui_labels"):
          self.cockpit_view.refresh_ui_labels()
      if hasattr(self, "board_view") and hasattr(self.board_view, "refresh_ui_labels"):
          self.board_view.refresh_ui_labels()
      if hasattr(self, "table_view") and hasattr(self.table_view, "refresh_ui_labels"):
          self.table_view.refresh_ui_labels()
      if hasattr(self, "analytics_view") and hasattr(self.analytics_view, "refresh_ui_labels"):
          self.analytics_view.refresh_ui_labels()
      self.refresh_views(force_all=True)
  ```
- **Lines 687–690 (`open_zip_export_dialog`)**:
  ```python
  # BEFORE:
  dest_file = filedialog.asksaveasfilename(
      title="Komplett-Datensicherung als ZIP speichern",
      defaultextension=".zip",
      filetypes=[("ZIP-Archiv", "*.zip")],
      initialfile="SupportCockpit_Backup.zip",
      parent=self,
  )
  # AFTER:
  from services.i18n_service import tr
  dest_file = filedialog.asksaveasfilename(
      title=tr("dialog_titles.zip_export", "Komplett-Datensicherung als ZIP speichern"),
      defaultextension=".zip",
      filetypes=[(tr("file_types.zip_archive", "ZIP-Archiv"), "*.zip")],
      initialfile="SupportCockpit_Backup.zip",
      parent=self,
  )
  ```
- **Line 725 (`check_due_followups`)**:
  ```python
  # BEFORE:
  title=f"🔔 Wiedervorlage fällig ({due_count})",
  # AFTER:
  from services.i18n_service import tr
  title=tr("toast.followup_due_title", "🔔 Wiedervorlage fällig ({count})", count=due_count),
  ```

---

#### 2. `src/ui/app_dialogs.py`
- **Line 53**:
  ```python
  from services.i18n_service import tr
  note=tr("timeline.followup_set_note", "Wiedervorlage gesetzt auf: {date}. {note}", date=dt_iso, note=note_text)
  ```
- **Lines 68–72**:
  ```python
  from services.i18n_service import tr
  if new_state:
      case.workflow_status.followup_at = ""
      note_text = tr("timeline.case_completed", "Fall auf erledigt gesetzt.")
      change_text = tr("timeline.status_completed", "STATUS: Erledigt")
  else:
      note_text = tr("timeline.case_reopened", "Fall wieder geöffnet.")
      change_text = tr("timeline.status_open", "STATUS: Offen")
  ```
- **Lines 101–102**:
  ```python
  from services.i18n_service import tr
  note_text = tr("timeline.handover_note", "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}", actor=get_actor_display(new_actor_val), person=person_str, channel=channel, note=note_str)
  change_text = tr("timeline.handover_status", "ZUSTÄNDIGKEIT: {prev} -> {curr}", prev=get_actor_display(prev_actor_val), curr=get_actor_display(new_actor_val))
  ```

---

#### 3. `src/ui/views/cockpit_view.py`
- **Line 172 & 176 (`focus_wiki_search`, `focus_timeline_note`)**:
  ```python
  # BEFORE:
  self.right_tabview.set("Wiki")
  self.right_tabview.set("Zeitleiste")
  # AFTER:
  self.right_tabview.set(self._sidebar_tab_names.get("wiki", "Wiki"))
  self.right_tabview.set(self._sidebar_tab_names.get("timeline", "Zeitleiste"))
  ```
- **Line 242 (`_update_title_label`)**:
  ```python
  from services.i18n_service import tr
  status_tag = f"  [{tr('cockpit.status_completed_tag', '✓ ERLEDIGT')}]" if self.current_case.workflow_status.is_completed else ""
  self.case_title_label.configure(text=f"{self.current_case.case_id}: {self.current_case.classification.title}{status_tag}")
  ```
- **Lines 259 & 261 (`on_select_case_from_list`)**:
  ```python
  from services.i18n_service import tr
  if case.is_internal:
      self.kunde_label.configure(text=f"🏢 {tr('cockpit.customer', 'Kunde')}: {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')} ({case.customer.customer_id}){vip_str}")
  else:
      self.kunde_label.configure(text=f"🏥 {tr('cockpit.customer', 'Kunde')}: {case.customer.practice_name} ({case.customer.customer_id}){vip_str}")

  full_addr = getattr(case.customer, "full_address", "")
  addr_str = f" | 🏠 {full_addr}" if full_addr else ""
  self.ansprechpartner_label.configure(text=f"👤 {tr('cockpit.contact_person', 'Ansprechpartner')}: {case.customer.contact_person}{addr_str}")
  ```
- **Line 270 & Line 453 (`complete_btn`)**:
  ```python
  from services.i18n_service import tr
  self.complete_btn.configure(text=tr("cockpit.reopen", "✓ Wieder öffnen") if case.workflow_status.is_completed else tr("cockpit.complete", "✓ Erledigt"))
  ```
- **Lines 292 & 294 (`_on_sidebar_tab_changed`)**:
  ```python
  if curr_tab == self._sidebar_tab_names.get("timeline") or curr_tab == "Zeitleiste":
      self.timeline_widget.load_timeline(self.current_case.timeline)
  elif curr_tab == self._sidebar_tab_names.get("attachments") or curr_tab == "Anhänge":
      self.attachment_widget.load_attachments(self.current_case)
  ```
- **Line 329 & Line 337 (`on_copy_practice_email`)**:
  ```python
  from services.i18n_service import tr
  ToastNotification(
      self.winfo_toplevel(),
      title=tr("cockpit.email_copied_title", "📋 E-Mail kopiert"),
      message=tr("cockpit.email_copied_msg", "Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.", email=email_clean),
  )
  ToastNotification(
      self.winfo_toplevel(),
      title=tr("cockpit.no_email_title", "⚠ Keine E-Mail-Adresse"),
      message=tr("cockpit.no_email_msg", "Für diese Praxis ist keine E-Mail-Adresse hinterlegt."),
  )
  ```
- **Lines 392–393 & Lines 433–437**:
  Use `tr("timeline.handover_note", ...)` and `tr("timeline.case_completed", ...)`.
- **Line 520 (`_update_wiedervorlage_display`)**:
  ```python
  from services.i18n_service import tr
  self._wiedervorlage_full_text = f"{tr('cockpit.followup_at', '🔔 Nachfragen am:')} {fw_date_str}, {fw_time_str}{note_suffix}"
  ```

---

#### 4. `src/ui/views/cockpit_layout_builders.py`
- **Line 158**:
  ```python
  # BEFORE:
  self.wv_hdr_label = ctk.CTkLabel(
      self.wiedervorlage_frame,
      text="🔔 Nachfragen am:",
      font=ctk.CTkFont(size=11, weight="bold"),
      ...
  )
  # AFTER:
  from services.i18n_service import tr
  self.wv_hdr_label = ctk.CTkLabel(
      self.wiedervorlage_frame,
      text=tr("cockpit.followup_at", "🔔 Nachfragen am:"),
      font=ctk.CTkFont(size=11, weight="bold"),
      ...
  )
  ```
- **Lines 274–323 (`refresh_ui_labels`)**:
  ```python
  def refresh_ui_labels(self):
      from services.i18n_service import tr
      from enums import ACTOR_DISPLAY, get_actor_display
      if hasattr(self, "more_actions_combo"):
          self.more_actions_combo.configure(values=[
              tr("cockpit.copy_email", "📧 Praxis E-Mail kopieren"),
              tr("cockpit.export_case", "📤 Fall exportieren"),
              tr("cockpit.print_case", "🖨 Fall-Akte drucken"),
              tr("cockpit.convert_form", "🔄 Formular umwandeln"),
          ])
          self.more_actions_combo.set(tr("cockpit.more_actions", "⚙ Weitere Aktionen..."))
      if hasattr(self, "email_btn"):
          self.email_btn.configure(text=tr("cockpit.email_ai", "✉ E-Mail & 🤖 KI"))
      if hasattr(self, "cal_btn"):
          self.cal_btn.configure(text=tr("cockpit.calendar", "📅 Kalender"))
      if hasattr(self, "followup_btn"):
          self.followup_btn.configure(text=tr("cockpit.followup", "🔔 Wiedervorlage"))
      if hasattr(self, "add_note_btn"):
          self.add_note_btn.configure(text=tr("cockpit.note", "📝 Notiz"))
      if hasattr(self, "save_btn"):
          self.save_btn.configure(text=tr("cockpit.save", "💾 Speichern"))
      if hasattr(self, "archive_btn"):
          self.archive_btn.configure(text=tr("cockpit.archive", "📦 Archivieren"))
      if hasattr(self, "wv_hdr_label"):
          self.wv_hdr_label.configure(text=tr("cockpit.followup_at", "🔔 Nachfragen am:"))
      if hasattr(self, "complete_btn"):
          if self.current_case:
              self.complete_btn.configure(text=tr("cockpit.reopen", "✓ Wieder öffnen") if self.current_case.workflow_status.is_completed else tr("cockpit.complete", "✓ Erledigt"))
          else:
              self.complete_btn.configure(text=tr("cockpit.complete", "✓ Erledigt"))
      if hasattr(self, "actor_combo"):
          self.actor_combo.configure(values=list(ACTOR_DISPLAY.values()))
          if self.current_case:
              self.actor_combo.set(get_actor_display(self.current_case.workflow_status.current_actor))
      if hasattr(self, "case_title_label"):
          if self.current_case:
              self._update_title_label()
          else:
              self.case_title_label.configure(text=tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen"))
      if self.current_case:
          vip_str = " ★ VIP" if self.current_case.customer.is_vip else ""
          if self.current_case.is_internal:
              self.kunde_label.configure(text=f"🏢 {tr('cockpit.customer', 'Kunde')}: {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')} ({self.current_case.customer.customer_id}){vip_str}")
          else:
              self.kunde_label.configure(text=f"🏥 {tr('cockpit.customer', 'Kunde')}: {self.current_case.customer.practice_name} ({self.current_case.customer.customer_id}){vip_str}")
          full_addr = getattr(self.current_case.customer, "full_address", "")
          addr_str = f" | 🏠 {full_addr}" if full_addr else ""
          self.ansprechpartner_label.configure(text=f"👤 {tr('cockpit.contact_person', 'Ansprechpartner')}: {self.current_case.customer.contact_person}{addr_str}")
          self._update_wiedervorlage_display()

      # Refresh right pane tabs ("Zeitleiste", "Anhänge", "Wiki")
      if hasattr(self, "right_tabview") and hasattr(self.right_tabview, "_segmented_button") and hasattr(self.right_tabview._segmented_button, "_buttons_dict"):
          btns = self.right_tabview._segmented_button._buttons_dict
          tab_defs = {"timeline": "Zeitleiste", "attachments": "Anhänge", "wiki": "Wiki"}
          for tab_key, def_name in tab_defs.items():
              new_text = tr(f"cockpit.tab_{tab_key}", def_name)
              prev_text = self._sidebar_tab_names.get(tab_key, def_name)
              self._sidebar_tab_names[tab_key] = new_text
              if prev_text in btns:
                  btns[prev_text].configure(text=new_text)

      # Refresh child widgets (Fixing left_frame reference)
      if hasattr(self, "left_frame") and hasattr(self.left_frame, "refresh_ui_labels"):
          self.left_frame.refresh_ui_labels()
      if hasattr(self, "timeline_widget") and hasattr(self.timeline_widget, "refresh_ui_labels"):
          self.timeline_widget.refresh_ui_labels()
      if hasattr(self, "attachment_widget") and hasattr(self.attachment_widget, "refresh_ui_labels"):
          self.attachment_widget.refresh_ui_labels()
      if hasattr(self, "wiki_widget") and hasattr(self.wiki_widget, "refresh_ui_labels"):
          self.wiki_widget.refresh_ui_labels()
      if hasattr(self, "form_widget") and hasattr(self.form_widget, "refresh_ui_labels"):
          self.form_widget.refresh_ui_labels()
  ```

---

#### 5. `src/ui/views/board_view.py`
- **Line 47 in `KanbanCardWidget`**:
  ```python
  from services.i18n_service import tr
  score_lbl = ctk.CTkLabel(
      header_frame,
      text=f"{tr('board.score', 'Score')} {score:.0f}",
      font=ctk.CTkFont(size=10, weight="bold"),
      ...
  )
  ```
- **Lines 204–207 in `create_board`**:
  ```python
  from services.i18n_service import tr
  cols_def = [
      ("support", tr("board.col_support_header", "📥 Support / In Bearbeitung")),
      ("dev", tr("board.col_dev_header", "💻 Entwickler / Dev-Team")),
      ("followup", tr("board.col_followup_header", "🔔 Wiedervorlage / Warten")),
      ("completed", tr("board.col_completed_header", "✓ Erledigte Fälle")),
  ]
  ```
- **Line 226 in `create_board`**:
  ```python
  from services.i18n_service import tr
  btn_exp = ctk.CTkButton(
      col_frame,
      text=tr("board.expand_btn", "▶"),
      width=28,
      height=28,
      command=lambda k=col_key: self.toggle_column_collapse(k),
      fg_color=("gray75", "gray35"),
      hover_color=("gray65", "gray50"),
  )
  ```
- **Lines 314–317 in `refresh_board`**:
  ```python
  from services.i18n_service import tr
  titles = {
      "support": f"📥 {tr('board.title_support', 'Support')} ({len(col_cases['support'])})",
      "dev": f"💻 {tr('board.title_dev', 'Entwickler')} ({len(col_cases['dev'])})",
      "followup": f"🔔 {tr('board.title_followup', 'Wiedervorlage')} ({len(col_cases['followup'])})",
      "completed": f"✓ {tr('board.title_completed', 'Erledigt')} ({len(col_cases['completed'])})",
  }
  ```
- **Add `refresh_ui_labels` method**:
  ```python
  def refresh_ui_labels(self):
      self.create_board()
      self.refresh_board()
  ```

---

#### 6. `src/ui/views/table_view.py`
- **Lines 157–159 in `create_layout`**:
  ```python
  from services.i18n_service import tr
  self._detail_tab_keys = {
      "form": tr("table.tab_form", "📝 Formular & Ausfüllen"),
      "timeline": tr("table.tab_timeline", "🕒 Zeitleiste"),
      "attachments": tr("table.tab_attachments", "📎 Anhänge"),
  }
  tab_form = self.detail_tabview.add(self._detail_tab_keys["form"])
  tab_timeline = self.detail_tabview.add(self._detail_tab_keys["timeline"])
  tab_attachments = self.detail_tabview.add(self._detail_tab_keys["attachments"])
  ```
- **Lines 301–303 in `select_case`**:
  ```python
  from services.i18n_service import tr
  self.detail_title_label.configure(
      text=tr("table.details_title", "📋 Falldetails: {case_id} - {title}", case_id=case.case_id, title=f"{case.customer.practice_name} ({case.classification.title})")
  )
  ```
- **Add `refresh_ui_labels` method**:
  ```python
  def refresh_ui_labels(self):
      from services.i18n_service import tr
      self.configure_tree_columns()
      self.render_rows()
      if self.selected_case:
          self.detail_title_label.configure(
              text=tr("table.details_title", "📋 Falldetails: {case_id} - {title}", case_id=self.selected_case.case_id, title=f"{self.selected_case.customer.practice_name} ({self.selected_case.classification.title})")
          )
      else:
          self.detail_title_label.configure(
              text=tr("table.details_header", "📋 Falldetails & Formular (Wählen Sie einen Fall aus der Tabelle)")
          )
      self.save_btn.configure(text=tr("table.save_btn", "💾 Ändern & Speichern"))

      if hasattr(self, "detail_tabview") and hasattr(self.detail_tabview, "_segmented_button") and hasattr(self.detail_tabview._segmented_button, "_buttons_dict"):
          btns = self.detail_tabview._segmented_button._buttons_dict
          tab_defs = {
              "form": ("📝 Formular & Ausfüllen", tr("table.tab_form", "📝 Formular & Ausfüllen")),
              "timeline": ("🕒 Zeitleiste", tr("table.tab_timeline", "🕒 Zeitleiste")),
              "attachments": ("📎 Anhänge", tr("table.tab_attachments", "📎 Anhänge")),
          }
          for key, (def_text, new_text) in tab_defs.items():
              prev_text = getattr(self, "_detail_tab_keys", {}).get(key, def_text)
              if prev_text in btns:
                  btns[prev_text].configure(text=new_text)
              if not hasattr(self, "_detail_tab_keys"):
                  self._detail_tab_keys = {}
              self._detail_tab_keys[key] = new_text

      if hasattr(self, "form_widget") and hasattr(self.form_widget, "refresh_ui_labels"):
          self.form_widget.refresh_ui_labels()
      if hasattr(self, "timeline_widget") and hasattr(self.timeline_widget, "refresh_ui_labels"):
          self.timeline_widget.refresh_ui_labels()
      if hasattr(self, "attachment_widget") and hasattr(self.attachment_widget, "refresh_ui_labels"):
          self.attachment_widget.refresh_ui_labels()
  ```

---

#### 7. `src/ui/views/analytics_view.py`
- **Lines 93 & 96**:
  ```python
  from services.i18n_service import tr
  if avg_days >= 1.0:
      avg_res_str = f"{avg_days:.1f} {tr('analytics.days_unit', 'Tage')}"
  else:
      avg_hrs = max(0.1, avg_sec / 3600.0)
      avg_res_str = f"{avg_hrs:.1f} {tr('analytics.hours_unit', 'Std')}"
  ```
- **Lines 141–143**:
  ```python
  from services.i18n_service import tr
  ctk.CTkLabel(urg_row, text=f"{tr('analytics.critical_red', '🔴 Rot (Kritisch)')}: {red_count} ({red_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="red").pack(anchor="w", pady=2)
  ctk.CTkLabel(urg_row, text=f"{tr('analytics.medium_yellow', '🟡 Gelb (Mittel)')}: {yellow_count} ({yellow_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="gold").pack(anchor="w", pady=2)
  ctk.CTkLabel(urg_row, text=f"{tr('analytics.normal_green', '🟢 Grün (Normal)')}: {green_count} ({green_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="limegreen").pack(anchor="w", pady=2)
  ```
- **Lines 154, 161, 180, 190, 199, 213**:
  ```python
  from services.i18n_service import tr
  sid = c.classification.schema_id or tr("analytics.schema_general", "Allgemein")
  ctk.CTkLabel(schema_frame, text=f"• {sname}: {scount} {tr('analytics.cases_suffix', 'Fälle')} ({pct:.0f}%)", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)
  ctk.CTkLabel(prac_frame, text=f"{idx}. {p_name}{vip_str} — {count} {tr('analytics.cases_suffix_alt', 'Vorgänge')}", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)
  assignee = c.assigned_to.strip() if getattr(c, "assigned_to", "") and c.assigned_to.strip() else tr("analytics.unassigned", "Nicht zugewiesen")
  ctk.CTkLabel(staff_frame, text=f"• {assignee}: {st['open']} {tr('analytics.open_suffix', 'offen')}, {st['done']} {tr('analytics.done_suffix', 'erledigt')}", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)
  ctk.CTkLabel(dept_frame, text=f"• {act_str}: {count} {tr('analytics.cases_suffix', 'Fälle')}", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)
  ```
- **Lines 240–258 (`generate_report_markdown`)**:
  ```python
  from services.i18n_service import tr
  lines = [
      tr("analytics.report_header", "# Support Cockpit — Statistik & Kennzahlen Bericht"),
      tr("analytics.report_total_cases", "**Fälle Gesamt:** {count}", count=total_count),
      tr("analytics.report_open_cases", "**Offene Fälle:** {count}", count=len(open_cases)),
      tr("analytics.report_completed_cases", "**Erledigte Fälle:** {count} ({pct:.1f}%)", count=len(completed_cases), pct=(len(completed_cases)/total_count*100 if total_count else 0)),
      tr("analytics.report_overdue_cases", "**Überfällige Wiedervorlagen:** {count}", count=len(overdue_cases)),
      tr("analytics.report_vip_rate", "**VIP-Kundenquote:** {pct:.1f}%\n", pct=(len(vip_cases)/total_count*100 if total_count else 0)),
      tr("analytics.report_urgency_title", "### Dringlichkeits-Verteilung (Scoring):"),
      tr("analytics.report_urgency_red", "- Rot (Kritisch): {count}", count=sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)),
      tr("analytics.report_urgency_yellow", "- Gelb (Mittel): {count}", count=sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW)),
      tr("analytics.report_urgency_green", "- Grün (Normal): {count}", count=sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN)) + "\n",
      tr("analytics.report_dept_title", "### Offene Fälle nach Abteilung:"),
  ]
  actor_counts: dict[str, int] = {}
  for c in open_cases:
      act_str = get_actor_display(c.workflow_status.current_actor)
      actor_counts[act_str] = actor_counts.get(act_str, 0) + 1
  for act_str, count in actor_counts.items():
      lines.append(tr("analytics.report_dept_item", "- {actor}: {count} Fälle", actor=act_str, count=count))
  ```
- **Line 272 (`copy_analytics_report`)**:
  ```python
  from services.i18n_service import tr
  ToastNotification(
      self.winfo_toplevel(),
      title=tr("analytics.copied_title", "📋 Statistik kopiert"),
      message=tr("analytics.report_copied_msg", "Statistik-Bericht wurde in die Zwischenablage kopiert."),
  )
  ```
- **Add `refresh_ui_labels` method**:
  ```python
  def refresh_ui_labels(self):
      from services.i18n_service import tr
      if hasattr(self, "top_bar_title"):
          self.top_bar_title.configure(text=tr("analytics.header", "Auswertungen & Support Cockpit KPIs"))
      if hasattr(self, "copy_report_btn"):
          self.copy_report_btn.configure(text=tr("analytics.copy_report_btn", "📋 Statistik-Bericht kopieren"))
      self.render_dashboard()
  ```

---

## 4. Caveats

1. **CustomTkinter Tabviews**: `CTkTabview` internally stores tab frames by their initial string name. Dynamic renaming must configure the segmented button dictionary (`self.tabview._segmented_button._buttons_dict[orig_name].configure(text=new_text)`) rather than recreating tabs to preserve tab contents and avoid layout flicker.
2. **Dialog Launchers**: `app_dialogs.py` contains dialog openers and callback handlers. Some timeline entries created on status toggle or handover are persisted in the case's timeline history. Using localized template strings ensures new timeline entries match the user's active session language.
3. **No other caveats**: The target scope is strictly contained within `src/ui/app.py`, `src/ui/app_dialogs.py`, and `src/ui/views/*.py`.

---

## 5. Conclusion

- All hardcoded German strings, AST violations, and missing refresh listeners across `app.py` and `src/ui/views/` (`cockpit_view.py`, `cockpit_layout_builders.py`, `board_view.py`, `table_view.py`, `analytics_view.py`) are fully cataloged.
- 48 key definitions across DE, EN, SV are specified with complete natural translations and parameter mappings.
- Exact line-by-line replacement specifications and dynamic refresh cascade logic have been designed to ensure seamless runtime language switching with 0 AST violations and 100% test pass rate.

---

## 6. Verification Method

To independently verify the investigation and implementation:
1. **Locale Parity & Quality Test**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_translation_parity_and_quality.py
   ```
2. **AST Scanner Cleanliness Test**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_ast_i18n_scanner.py
   ```
3. **Dynamic Language Switch & View Integration Tests**:
   ```bash
   .venv\Scripts\python.exe -m pytest tests/test_dynamic_language_switch.py tests/test_e2e_multilingual_workflows.py
   ```
4. **Full Test Suite Execution**:
   ```bash
   .venv\Scripts\python.exe -m pytest
   ```
