# Milestone 3 Handoff Report: AST Scanner & Localization Mapping

## 1. Observation

### 1.1 Scope of Investigation
We conducted a comprehensive AST and string literal investigation across all Milestone 3 target files:
- App Shell & Orchestration: `src/ui/app.py`, `src/ui/app_dialogs.py`
- UI Views: `src/ui/views/analytics_view.py`, `src/ui/views/board_view.py`, `src/ui/views/cockpit_layout_builders.py`, `src/ui/views/cockpit_view.py`, `src/ui/views/table_view.py`
- UI Widgets: `src/ui/widgets/attachment_widget.py`, `src/ui/widgets/case_list_widget.py`, `src/ui/widgets/ctk_tooltip.py`, `src/ui/widgets/date_picker.py`, `src/ui/widgets/dynamic_form_field_renderers.py`, `src/ui/widgets/dynamic_form_widget.py`, `src/ui/widgets/searchable_combobox.py`, `src/ui/widgets/timeline_widget.py`, `src/ui/widgets/toast_notification.py`, `src/ui/widgets/wiki_widget.py`
- Locale JSON files: `locales/de.json`, `locales/en.json`, `locales/sv.json`
- AST Test Suite: `tests/test_ast_i18n_scanner.py`, `tests/test_translation_parity_and_quality.py`

### 1.2 Baseline Scan Measurements
Running AST extraction across the 17 M3 files yielded:
- **148 existing `tr(...)` calls** across M3 files (100% already synchronized across `de.json`, `en.json`, `sv.json` from Milestone 1).
- **76 distinct user-visible UI text locations** requiring localization or refactoring:
  - **20 locations** map directly to existing locale keys that were either hardcoded at widget construction or bypassed in configure callbacks.
  - **56 locations** require **NEW translation keys** to be added to `locales/de.json`, `locales/en.json`, and `locales/sv.json`.

---

## 2. Logic Chain

1. **AST Principle Adherence**:
   - `tests/test_ast_i18n_scanner.py` enforces that all widget keyword arguments (`text`, `placeholder_text`, `title`, `message`, etc.), dialog popup calls (`asksaveasfilename`, `askopenfilename`), and tab additions (`CTkTabview.add`) must not use hardcoded user-visible text literals.
   - All text must be resolved via `tr(key, default, **kwargs)` or `LocalizedDict` proxy subscripts.

2. **Categorization & Namespace Architecture**:
   - Keys are structured hierarchically by domain namespace:
     - `app.*`: Application shell, file dialogs, system backup, and notification titles.
     - `analytics.*`: Metrics cards, KPI summaries, breakdown rows, and clipboard toast notifications.
     - `board.*`: Kanban columns, card score badges, and dynamic column header counts.
     - `cockpit.*`: Cockpit view header cards, customer/contact displays, status buttons, and action menu.
     - `table.*`: Treeview column headers, matrix details headers, and tab headers.
     - `attachments.*`: Preview metadata, error labels, file dialog titles.
     - `case_list.*`: Search filters, case count headers, card badges, and hover tooltip template strings.
     - `date_picker.*`: Calendar dialog title, weekday abbreviations, time units, and quick preset buttons.
     - `dynamic_form.*`: Form field placeholders, multiselect options, popup dialog titles, repeatable group card headers.
     - `timeline.*`: History note prefixes, channel tags.
     - `wiki.*`: Search status counts, sync progress notifications.
     - `common.*`: Reusable shared tokens (`general`, `unassigned`, `all_files`, `please_select`).

3. **Reconciliation with Existing Locale Data**:
   - Several UI elements had keys already defined during M1/M2 (e.g. `date_picker.preset_today_1130`, `dynamic_form.select_tags_dialog_title`, `dynamic_form.import_backup_dialog_title`, `table.tab_form`, `cockpit.followup_at`, `analytics.report_copied_msg`).
   - The UI components were still passing raw German strings in code rather than calling `tr(...)`.
   - The implementation must wire these existing keys directly to prevent duplicate keys or inconsistencies.

4. **Dynamic Formatting Parameterization**:
   - Hardcoded f-strings (such as `f"{len(self.cases)} Support-Fälle"`, `f"• {act_str}: {count} Fälle"`, `f"Score {score:.0f}"`, `f"🔔 Wiedervorlage fällig ({due_count})"`) must use keyword-argument formatting in `tr(...)`:
     - e.g. `tr("case_list.count_format", "{count} Support-Fälle", count=len(self.cases))`
     - `tr("analytics.dept_cases_item", "• {dept}: {count} Fälle", dept=act_str, count=count)`
     - `tr("app.followup_due_toast_title", "🔔 Wiedervorlage fällig ({count})", count=due_count)`

---

## 3. Caveats

1. **Scope Boundary**:
   - `src/ui/dialogs/` (all 18 dialog files) is explicitly scoped to **Milestone 4**. Only dialog openers in `src/ui/app_dialogs.py` and widgets embedded in views are in Milestone 3.
2. **Dynamic Language Switch Propagation (Milestone 5)**:
   - While Milestone 3 focuses on string extraction to `tr(...)` and adding missing keys to `locales/*.json`, full dynamic switching across all views at runtime without reload is completed in Milestone 5 via `refresh_ui_labels()`. M3 should provide clean `refresh_ui_labels()` implementations where labels are modified dynamically.
3. **CTkTabview Tab Key Binding**:
   - `CTkTabview.add("tab_name")` uses the string as both an internal dictionary key and display label. When calling `tr(...)`, ensure the tab identifier remains consistent or uses `refresh_ui_labels` on `right_tabview._segmented_button._buttons_dict`.

---

## 4. Conclusion & Complete Localization Mapping

### 4.1 Master Mapping Table for Milestone 3 UI Elements

| File & Line | Component / Context | Current Hardcoded Literal | Proposed Code Call | Translation Key | Existing vs New | German (DE) | English (EN) | Swedish (SV) |
|---|---|---|---|---|---|---|---|---|
| `src/ui/app.py:688` | `filedialog.asksaveasfilename(title=...)` | `"Komplett-Datensicherung als ZIP speichern"` | `tr("app.zip_backup_title", "Komplett-Datensicherung als ZIP speichern")` | `app.zip_backup_title` | **NEW** | `Komplett-Datensicherung als ZIP speichern` | `Save complete data backup as ZIP` | `Spara fullständig säkerhetskopia som ZIP` |
| `src/ui/app.py:690` | `filetypes=[("ZIP-Archiv", ...)]` | `"ZIP-Archiv"` | `tr("app.zip_filetypes", "ZIP-Archiv")` | `app.zip_filetypes` | **NEW** | `ZIP-Archiv` | `ZIP Archive` | `ZIP-arkiv` |
| `src/ui/app.py:725` | `ToastNotification(title=...)` | `f"🔔 Wiedervorlage fällig ({due_count})"` | `tr("app.followup_due_toast_title", "🔔 Wiedervorlage fällig ({count})", count=due_count)` | `app.followup_due_toast_title` | **NEW** | `🔔 Wiedervorlage fällig ({count})` | `🔔 Follow-up due ({count})` | `🔔 Uppföljning förfallen ({count})` |
| `src/ui/app_dialogs.py:53` | `TimelineEntry(note=...)` | `f"Wiedervorlage gesetzt auf: {dt_iso}. {note_text}"` | `tr("app.timeline_followup_set", "Wiedervorlage gesetzt auf: {date}. {note}", date=dt_iso, note=note_text)` | `app.timeline_followup_set` | **NEW** | `Wiedervorlage gesetzt auf: {date}. {note}` | `Follow-up set to: {date}. {note}` | `Uppföljning satt till: {date}. {note}` |
| `src/ui/app_dialogs.py:68` | `TimelineEntry(note=...)` | `"Fall auf erledigt gesetzt."` | `tr("app.timeline_case_completed", "Fall auf erledigt gesetzt.")` | `app.timeline_case_completed` | **NEW** | `Fall auf erledigt gesetzt.` | `Case marked as completed.` | `Ärendet markerat som klart.` |
| `src/ui/app_dialogs.py:69` | `TimelineEntry(status_change=...)` | `"STATUS: Erledigt"` | `tr("app.timeline_status_completed", "STATUS: Erledigt")` | `app.timeline_status_completed` | **NEW** | `STATUS: Erledigt` | `STATUS: Completed` | `STATUS: Klart` |
| `src/ui/app_dialogs.py:71` | `TimelineEntry(note=...)` | `"Fall wieder geöffnet."` | `tr("app.timeline_case_reopened", "Fall wieder geöffnet.")` | `app.timeline_case_reopened` | **NEW** | `Fall wieder geöffnet.` | `Case reopened.` | `Ärendet återöppnat.` |
| `src/ui/app_dialogs.py:72` | `TimelineEntry(status_change=...)` | `"STATUS: Offen"` | `tr("app.timeline_status_open", "STATUS: Offen")` | `app.timeline_status_open` | **NEW** | `STATUS: Offen` | `STATUS: Open` | `STATUS: Öppen` |
| `src/ui/app_dialogs.py:101` | `TimelineEntry(note=...)` | `f"Zuständigkeit übergeben an: {get_actor_display(...)}..."` | `tr("app.timeline_handover_note", "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}", ...)` | `app.timeline_handover_note` | **NEW** | `Zuständigkeit übergeben an: {actor}{person} via {channel}{note}` | `Responsibility handed over to: {actor}{person} via {channel}{note}` | `Ansvar överlämnat till: {actor}{person} via {channel}{note}` |
| `src/ui/app_dialogs.py:102` | `TimelineEntry(status_change=...)` | `f"ZUSTÄNDIGKEIT: {prev} -> {next}"` | `tr("app.timeline_handover_status", "ZUSTÄNDIGKEIT: {prev} -> {next}", prev=..., next=...)` | `app.timeline_handover_status` | **NEW** | `ZUSTÄNDIGKEIT: {prev} -> {next}` | `RESPONSIBILITY: {prev} -> {next}` | `ANSVAR: {prev} -> {next}` |
| `src/ui/views/analytics_view.py:93` | `avg_res_str` formatting | `f"{avg_days:.1f} Tage"` | `tr("analytics.days_format", "{days:.1f} Tage", days=avg_days)` | `analytics.days_format` | **NEW** | `{days:.1f} Tage` | `{days:.1f} days` | `{days:.1f} dagar` |
| `src/ui/views/analytics_view.py:96` | `avg_res_str` formatting | `f"{avg_hrs:.1f} Std"` | `tr("analytics.hours_format", "{hours:.1f} Std", hours=avg_hrs)` | `analytics.hours_format` | **NEW** | `{hours:.1f} Std` | `{hours:.1f} hrs` | `{hours:.1f} tim` |
| `src/ui/views/analytics_view.py:98` | `avg_res_str` fallback | `"n/a"` | `tr("analytics.na", "n/a")` | `analytics.na` | **NEW** | `n/a` | `n/a` | `ej tillgängligt` |
| `src/ui/views/analytics_view.py:141` | `CTkLabel(text=...)` | `f"🔴 Rot (Kritisch): {red_count} ({pct:.0f}%)"` | `tr("analytics.urgency_red", "🔴 Rot (Kritisch): {count} ({pct:.0f}%)", count=red_count, pct=...)` | `analytics.urgency_red` | **NEW** | `🔴 Rot (Kritisch): {count} ({pct:.0f}%)` | `🔴 Red (Critical): {count} ({pct:.0f}%)` | `🔴 Röd (Kritisk): {count} ({pct:.0f}%)` |
| `src/ui/views/analytics_view.py:142` | `CTkLabel(text=...)` | `f"🟡 Gelb (Mittel): {yellow_count} ({pct:.0f}%)"` | `tr("analytics.urgency_yellow", "🟡 Gelb (Mittel): {count} ({pct:.0f}%)", count=yellow_count, pct=...)` | `analytics.urgency_yellow` | **NEW** | `🟡 Gelb (Mittel): {count} ({pct:.0f}%)` | `🟡 Yellow (Medium): {count} ({pct:.0f}%)` | `🟡 Gul (Medel): {count} ({pct:.0f}%)` |
| `src/ui/views/analytics_view.py:143` | `CTkLabel(text=...)` | `f"🟢 Grün (Normal): {green_count} ({pct:.0f}%)"` | `tr("analytics.urgency_green", "🟢 Grün (Normal): {count} ({pct:.0f}%)", count=green_count, pct=...)` | `analytics.urgency_green` | **NEW** | `🟢 Grün (Normal): {count} ({pct:.0f}%)` | `🟢 Green (Normal): {count} ({pct:.0f}%)` | `🟢 Grön (Normal): {count} ({pct:.0f}%)` |
| `src/ui/views/analytics_view.py:154` | fallback schema name | `"Allgemein"` | `tr("common.general", "Allgemein")` | `common.general` | **NEW** | `Allgemein` | `General` | `Allmänt` |
| `src/ui/views/analytics_view.py:161` | `CTkLabel(text=...)` | `f"• {sname}: {scount} Fälle ({pct:.0f}%)"` | `tr("analytics.schema_cases_item", "• {name}: {count} Fälle ({pct:.0f}%)", name=sname, count=scount, pct=pct)` | `analytics.schema_cases_item` | **NEW** | `• {name}: {count} Fälle ({pct:.0f}%)` | `• {name}: {count} cases ({pct:.0f}%)` | `• {name}: {count} ärenden ({pct:.0f}%)` |
| `src/ui/views/analytics_view.py:180` | `CTkLabel(text=...)` | `f"{idx}. {p_name}{vip_str} — {count} Vorgänge"` | `tr("analytics.practice_ranking_item", "{idx}. {name}{vip} — {count} Vorgänge", idx=idx, name=p_name, vip=vip_str, count=count)` | `analytics.practice_ranking_item` | **NEW** | `{idx}. {name}{vip} — {count} Vorgänge` | `{idx}. {name}{vip} — {count} cases` | `{idx}. {name}{vip} — {count} ärenden` |
| `src/ui/views/analytics_view.py:190` | unassigned fallback | `"Nicht zugewiesen"` | `tr("common.unassigned", "Nicht zugewiesen")` | `common.unassigned` | **NEW** | `Nicht zugewiesen` | `Unassigned` | `Inte tilldelad` |
| `src/ui/views/analytics_view.py:199` | `CTkLabel(text=...)` | `f"• {assignee}: {st['open']} offen, {st['done']} erledigt"` | `tr("analytics.assignee_workload_item", "• {assignee}: {open} offen, {done} erledigt", assignee=assignee, open=st['open'], done=st['done'])` | `analytics.assignee_workload_item` | **NEW** | `• {assignee}: {open} offen, {done} erledigt` | `• {assignee}: {open} open, {done} completed` | `• {assignee}: {open} öppna, {done} klara` |
| `src/ui/views/analytics_view.py:213` | `CTkLabel(text=...)` | `f"• {act_str}: {count} Fälle"` | `tr("analytics.dept_cases_item", "• {dept}: {count} Fälle", dept=act_str, count=count)` | `analytics.dept_cases_item` | **NEW** | `• {dept}: {count} Fälle` | `• {dept}: {count} cases` | `• {dept}: {count} ärenden` |
| `src/ui/views/analytics_view.py:272` | `ToastNotification(message=...)` | `"Statistik-Bericht wurde in die Zwischenablage kopiert."` | `tr("analytics.report_copied_msg", "Statistik-Bericht wurde in die Zwischenablage kopiert.")` | `analytics.report_copied_msg` | **EXISTING** | `Statistik-Bericht wurde in die Zwischenablage kopiert.` | `Statistics report copied to clipboard.` | `Statistikrapporten kopierades till urklipp.` |
| `src/ui/views/board_view.py:46` | `CTkLabel(text=...)` | `f"Score {score:.0f}"` | `tr("board.score_label", "Score {score}", score=f"{score:.0f}")` | `board.score_label` | **NEW** | `Score {score}` | `Score {score}` | `Poäng {score}` |
| `src/ui/views/board_view.py:314` | column header count | `f"📥 Support ({len(col_cases['support'])})"` | `tr("board.col_support", "📥 Support ({count})", count=len(col_cases['support']))` | `board.col_support` | **EXISTING** | `📥 Support ({count})` | `📥 Support ({count})` | `📥 Support ({count})` |
| `src/ui/views/board_view.py:315` | column header count | `f"💻 Entwickler ({len(col_cases['dev'])})"` | `tr("board.col_dev", "💻 Entwickler ({count})", count=len(col_cases['dev']))` | `board.col_dev` | **EXISTING** | `💻 Entwickler ({count})` | `💻 Developer ({count})` | `💻 Utvecklare ({count})` |
| `src/ui/views/board_view.py:316` | column header count | `f"🔔 Wiedervorlage ({len(col_cases['followup'])})"` | `tr("board.col_followup", "🔔 Wiedervorlage ({count})", count=len(col_cases['followup']))` | `board.col_followup` | **EXISTING** | `🔔 Wiedervorlage ({count})` | `🔔 Follow-up ({count})` | `🔔 Uppföljning ({count})` |
| `src/ui/views/board_view.py:317` | column header count | `f"✓ Erledigt ({len(col_cases['completed'])})"` | `tr("board.col_done", "✓ Erledigt ({count})", count=len(col_cases['completed']))` | `board.col_done` | **EXISTING** | `✓ Erledigt ({count})` | `✓ Completed ({count})` | `✓ Klart ({count})` |
| `src/ui/views/cockpit_layout_builders.py:158` | `CTkLabel(text=...)` | `"🔔 Nachfragen am:"` | `tr("cockpit.followup_at", "🔔 Nachfragen am:")` | `cockpit.followup_at` | **EXISTING** | `🔔 Nachfragen am:` | `🔔 Follow up on:` | `🔔 Följ upp den:` |
| `src/ui/views/cockpit_view.py:242` | status completed tag | `"  [✓ ERLEDIGT]"` | `tr("cockpit.status_completed_tag", "  [✓ ERLEDIGT]")` | `cockpit.status_completed_tag` | **NEW** | `  [✓ ERLEDIGT]` | `  [✓ COMPLETED]` | `  [✓ KLART]` |
| `src/ui/views/cockpit_view.py:259` | `kunde_label.configure(text=...)` | `f"🏢 Kunde: INTERNE AUFGABE / VORGANG ({case.customer.customer_id}){vip_str}"` | `tr("cockpit.customer_internal", "🏢 Kunde: INTERNE AUFGABE / VORGANG ({id}){vip}", id=case.customer.customer_id, vip=vip_str)` | `cockpit.customer_internal` | **NEW** | `🏢 Kunde: INTERNE AUFGABE / VORGANG ({id}){vip}` | `🏢 Customer: INTERNAL TASK / CASE ({id}){vip}` | `🏢 Kund: INTERNT ÄRENDE / UPPGIFT ({id}){vip}` |
| `src/ui/views/cockpit_view.py:261` | `kunde_label.configure(text=...)` | `f"🏥 Kunde: {case.customer.practice_name} ({case.customer.customer_id}){vip_str}"` | `tr("cockpit.customer_practice", "🏥 Kunde: {name} ({id}){vip}", name=case.customer.practice_name, id=case.customer.customer_id, vip=vip_str)` | `cockpit.customer_practice` | **NEW** | `🏥 Kunde: {name} ({id}){vip}` | `🏥 Customer: {name} ({id}){vip}` | `🏥 Kund: {name} ({id}){vip}` |
| `src/ui/views/cockpit_view.py:265` | `ansprechpartner_label.configure(text=...)` | `f"👤 Ansprechpartner: {case.customer.contact_person}{addr_str}"` | `tr("cockpit.contact_person", "👤 Ansprechpartner: {contact}{address}", contact=case.customer.contact_person, address=addr_str)` | `cockpit.contact_person` | **NEW** | `👤 Ansprechpartner: {contact}{address}` | `👤 Contact Person: {contact}{address}` | `👤 Kontaktperson: {contact}{address}` |
| `src/ui/views/cockpit_view.py:270` | `complete_btn.configure(text=...)` | `"✓ Wieder öffnen"` | `tr("cockpit.reopen", "✓ Wieder öffnen")` | `cockpit.reopen` | **NEW** | `✓ Wieder öffnen` | `✓ Reopen` | `✓ Återöppna` |
| `src/ui/views/cockpit_view.py:329` | `ToastNotification(message=...)` | `f"Praxis-E-Mail '{email_clean}' wurde in die Zwischenablage kopiert."` | `tr("cockpit.email_copied_message", "Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.", email=email_clean)` | `cockpit.email_copied_message` | **NEW** | `Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.` | `Practice email '{email}' has been copied to clipboard.` | `Mottagningens e-post '{email}' har kopierats till urklipp.` |
| `src/ui/views/cockpit_view.py:337` | `ToastNotification(message=...)` | `"Für diese Praxis ist keine E-Mail-Adresse hinterlegt."` | `tr("cockpit.no_email_msg", "Für diese Praxis ist keine E-Mail-Adresse hinterlegt.")` | `cockpit.no_email_msg` | **EXISTING** | `Für diese Praxis ist keine E-Mail-Adresse hinterlegt.` | `No email address is registered for this practice.` | `Ingen e-postadress är registrerad för denna mottagning.` |
| `src/ui/views/table_view.py:157` | `detail_tabview.add(...)` | `"📝 Formular & Ausfüllen"` | `tr("table.tab_form", "📝 Formular & Ausfüllen")` | `table.tab_form` | **EXISTING** | `📝 Formular & Ausfüllen` | `📝 Form & Fill-in` | `📝 Formulär & ifyllning` |
| `src/ui/views/table_view.py:158` | `detail_tabview.add(...)` | `"🕒 Zeitleiste"` | `tr("table.tab_timeline", "🕒 Zeitleiste")` | `table.tab_timeline` | **EXISTING** | `🕒 Zeitleiste` | `🕒 Timeline` | `🕒 Tidslinje` |
| `src/ui/views/table_view.py:159` | `detail_tabview.add(...)` | `"📎 Anhänge"` | `tr("table.tab_attachments", "📎 Anhänge")` | `table.tab_attachments` | **EXISTING** | `📎 Anhänge` | `📎 Attachments` | `📎 Bilagor` |
| `src/ui/views/table_view.py:302` | `detail_title_label.configure(text=...)` | `f"📋 Falldetails: {case.case_id} - {case.customer.practice_name} ({case.classification.title})"` | `tr("table.case_details_header", "📋 Falldetails: {id} - {practice} ({title})", id=case.case_id, practice=case.customer.practice_name, title=case.classification.title)` | `table.case_details_header` | **NEW** | `📋 Falldetails: {id} - {practice} ({title})` | `📋 Case Details: {id} - {practice} ({title})` | `📋 Ärendedetaljer: {id} - {practice} ({title})` |
| `src/ui/widgets/attachment_widget.py:136` | `CTkLabel(text=...)` | `f"🖼 Bild Vorschau: {filepath.name}\nAuflösung: {pil_img.width} x {pil_img.height} px \| Format: {pil_img.format}"` | `tr("attachments.image_preview_info", "🖼 Bild Vorschau: {name}\nAuflösung: {width} x {height} px \| Format: {format}", name=filepath.name, width=pil_img.width, height=pil_img.height, format=pil_img.format)` | `attachments.image_preview_info` | **NEW** | `🖼 Bild Vorschau: {name}\nAuflösung: {width} x {height} px \| Format: {format}` | `🖼 Image Preview: {name}\nResolution: {width} x {height} px \| Format: {format}` | `🖼 Bildförhandsvisning: {name}\nUpplösning: {width} x {height} px \| Format: {format}` |
| `src/ui/widgets/attachment_widget.py:139` | `CTkLabel(text=...)` | `f"Bild-Vorschau nicht verfügbar: {err}"` | `tr("attachments.image_preview_error", "Bild-Vorschau nicht verfügbar: {err}", err=err)` | `attachments.image_preview_error` | **NEW** | `Bild-Vorschau nicht verfügbar: {err}` | `Image preview not available: {err}` | `Bildförhandsvisning ej tillgänglig: {err}` |
| `src/ui/widgets/attachment_widget.py:149` | `CTkLabel(text=...)` | `f"Text-Vorschau Fehler: {err}"` | `tr("attachments.text_preview_error", "Text-Vorschau Fehler: {err}", err=err)` | `attachments.text_preview_error` | **NEW** | `Text-Vorschau Fehler: {err}` | `Text preview error: {err}` | `Textförhandsvisningsfel: {err}` |
| `src/ui/widgets/attachment_widget.py:151` | `CTkLabel(text=...)` | `f"📄 Vorschau für '{filepath.name}' (Doppelklick zum Öffnen im OS)"` | `tr("attachments.generic_preview_info", "📄 Vorschau für '{name}' (Doppelklick zum Öffnen im OS)", name=filepath.name)` | `attachments.generic_preview_info` | **NEW** | `📄 Vorschau für '{name}' (Doppelklick zum Öffnen im OS)` | `📄 Preview for '{name}' (Double-click to open in OS)` | `📄 Förhandsgranskning för '{name}' (Dubbelklicka för att öppna i OS)` |
| `src/ui/widgets/attachment_widget.py:177` | `filedialog.askopenfilename()` | `"Datei zum Anhängen auswählen"` | `filedialog.askopenfilename(title=tr("attachments.select_file_dialog_title", "Datei zum Anhängen auswählen"))` | `attachments.select_file_dialog_title` | **NEW** | `Datei zum Anhängen auswählen` | `Select file to attach` | `Välj fil att bifoga` |
| `src/ui/widgets/case_list_widget.py:131` | `count_label.configure(text=...)` | `f"{len(self.cases)} Support-Fälle"` | `tr("case_list.count_format", "{count} Support-Fälle", count=len(self.cases))` | `case_list.count_format` | **NEW** | `{count} Support-Fälle` | `{count} Support Cases` | `{count} Supportärenden` |
| `src/ui/widgets/case_list_widget.py:177` | `score_lbl.configure(text=...)` | `f"Pkt.: {case.classification.calculated_score:.0f}"` | `tr("case_list.score_pts", "Pkt.: {score}", score=f"{case.classification.calculated_score:.0f}")` | `case_list.score_pts` | **NEW** | `Pkt.: {score}` | `Pts: {score}` | `Pkt: {score}` |
| `src/ui/widgets/case_list_widget.py:208` | `practice_str` | `"🏢 INTERNE AUFGABE / VORGANG"` | `tr("case_list.internal_task", "🏢 INTERNE AUFGABE / VORGANG")` | `case_list.internal_task` | **NEW** | `🏢 INTERNE AUFGABE / VORGANG` | `🏢 INTERNAL TASK / CASE` | `🏢 INTERNT ÄRENDE / UPPGIFT` |
| `src/ui/widgets/case_list_widget.py:232` | `sub_str` | `f"{case.classification.title} \| Zuständig: {get_actor_display(...)}"` | `tr("case_list.actor_format", "{title} \| Zuständig: {actor}", title=case.classification.title, actor=get_actor_display(case.workflow_status.current_actor))` | `case_list.actor_format` | **NEW** | `{title} \| Zuständig: {actor}` | `{title} \| Assigned: {actor}` | `{title} \| Ansvarig: {actor}` |
| `src/ui/widgets/case_list_widget.py:297` | `CTkLabel(text=...)` | `"🔔 Nachfragen am:"` | `tr("cockpit.followup_at", "🔔 Nachfragen am:")` | `cockpit.followup_at` | **EXISTING** | `🔔 Nachfragen am:` | `🔔 Follow up on:` | `🔔 Följ upp den:` |
| `src/ui/widgets/case_list_widget.py:371` | `build_tooltip` header | `f"📌 Fall: {c.case_id} (Priorität: {c.classification.calculated_score:.0f} Pkt.)"` | `tr("case_list.tooltip_case_header", "📌 Fall: {id} (Priorität: {score} Pkt.)", id=c.case_id, score=f"{c.classification.calculated_score:.0f}")` | `case_list.tooltip_case_header` | **NEW** | `📌 Fall: {id} (Priorität: {score} Pkt.)` | `📌 Case: {id} (Priority: {score} pts)` | `📌 Ärende: {id} (Prioritet: {score} pkt)` |
| `src/ui/widgets/case_list_widget.py:374` | `build_tooltip` internal | `f"🏢 Kunde: INTERNE AUFGABE ({c.customer.customer_id})"` | `tr("case_list.tooltip_customer_internal", "🏢 Kunde: INTERNE AUFGABE ({id})", id=c.customer.customer_id)` | `case_list.tooltip_customer_internal` | **NEW** | `🏢 Kunde: INTERNE AUFGABE ({id})` | `🏢 Customer: INTERNAL TASK ({id})` | `🏢 Kund: INTERNT ÄRENDE ({id})` |
| `src/ui/widgets/case_list_widget.py:377` | `build_tooltip` practice | `f"🏥 Kunde: {c.customer.practice_name} ({c.customer.customer_id}){vip_t}"` | `tr("case_list.tooltip_customer_practice", "🏥 Kunde: {name} ({id}){vip}", name=c.customer.practice_name, id=c.customer.customer_id, vip=vip_t)` | `case_list.tooltip_customer_practice` | **NEW** | `🏥 Kunde: {name} ({id}){vip}` | `🏥 Customer: {name} ({id}){vip}` | `🏥 Kund: {name} ({id}){vip}` |
| `src/ui/widgets/case_list_widget.py:378` | `build_tooltip` contact | `f"👤 Ansprechpartner: {c.customer.contact_person}"` | `tr("case_list.tooltip_contact", "👤 Ansprechpartner: {contact}", contact=c.customer.contact_person)` | `case_list.tooltip_contact` | **NEW** | `👤 Ansprechpartner: {contact}` | `👤 Contact Person: {contact}` | `👤 Kontaktperson: {contact}` |
| `src/ui/widgets/case_list_widget.py:380` | `build_tooltip` topic | `f"📋 Thema: {c.classification.title}"` | `tr("case_list.tooltip_topic", "📋 Thema: {title}", title=c.classification.title)` | `case_list.tooltip_topic` | **NEW** | `📋 Thema: {title}` | `📋 Topic: {title}` | `📋 Ämne: {title}` |
| `src/ui/widgets/case_list_widget.py:381` | `build_tooltip` actor | `f"👤 Zuständig: {get_actor_display(...)}"` | `tr("case_list.tooltip_assigned", "👤 Zuständig: {actor}", actor=get_actor_display(c.workflow_status.current_actor))` | `case_list.tooltip_assigned` | **NEW** | `👤 Zuständig: {actor}` | `👤 Assigned: {actor}` | `👤 Ansvarig: {actor}` |
| `src/ui/widgets/case_list_widget.py:388` | `build_tooltip` followup | `f"🔔 Wiedervorlage: {fw_d} um {fw_tm}{note_t}"` | `tr("case_list.tooltip_followup", "🔔 Wiedervorlage: {date} um {time}{note}", date=fw_d, time=fw_tm, note=note_t)` | `case_list.tooltip_followup` | **NEW** | `🔔 Wiedervorlage: {date} um {time}{note}` | `🔔 Follow-up: {date} at {time}{note}` | `🔔 Uppföljning: {date} kl {time}{note}` |
| `src/ui/widgets/case_list_widget.py:391` | `build_tooltip` tags | `f"🏷 Tags: {', '.join(c.classification.tags)}"` | `tr("case_list.tooltip_tags", "🏷 Tags: {tags}", tags=', '.join(c.classification.tags))` | `case_list.tooltip_tags` | **NEW** | `🏷 Tags: {tags}` | `🏷 Tags: {tags}` | `🏷 Taggar: {tags}` |
| `src/ui/widgets/date_picker.py:23` | `self.title(...)` | `"📅 Datum auswählen"` | `self.title(tr("date_picker.dialog_title", "📅 Datum auswählen"))` | `date_picker.dialog_title` | **EXISTING** | `📅 Datum auswählen` | `📅 Select Date` | `📅 Välj datum` |
| `src/ui/widgets/date_picker.py:225` | `CTkButton(text=...)` | `"Heute 11:30"` | `tr("date_picker.preset_today_1130", "Heute 11:30")` | `date_picker.preset_today_1130` | **EXISTING** | `Heute 11:30` | `Today 11:30` | `Idag 11:30` |
| `src/ui/widgets/date_picker.py:226` | `CTkButton(text=...)` | `"Heute 13:30"` | `tr("date_picker.preset_today_1330", "Heute 13:30")` | `date_picker.preset_today_1330` | **EXISTING** | `Heute 13:30` | `Today 13:30` | `Idag 13:30` |
| `src/ui/widgets/date_picker.py:227` | `CTkButton(text=...)` | `"Heute 16:30"` | `tr("date_picker.preset_today_1630", "Heute 16:30")` | `date_picker.preset_today_1630` | **EXISTING** | `Heute 16:30` | `Today 16:30` | `Idag 16:30` |
| `src/ui/widgets/date_picker.py:228` | `CTkButton(text=...)` | `"Morgen 08:00"` | `tr("date_picker.preset_tomorrow_0800", "Morgen 08:00")` | `date_picker.preset_tomorrow_0800` | **EXISTING** | `Morgen 08:00` | `Tomorrow 08:00` | `Imorgon 08:00` |
| `src/ui/widgets/date_picker.py:229` | `CTkButton(text=...)` | `"+ 1 Tag"` | `tr("date_picker.preset_plus_1day", "+ 1 Tag")` | `date_picker.preset_plus_1day` | **EXISTING** | `+ 1 Tag` | `+ 1 Day` | `+ 1 dag` |
| `src/ui/widgets/date_picker.py:230` | `CTkButton(text=...)` | `"+ 1 Woche"` | `tr("date_picker.preset_plus_1week", "+ 1 Woche")` | `date_picker.preset_plus_1week` | **EXISTING** | `+ 1 Woche` | `+ 1 Week` | `+ 1 vecka` |
| `src/ui/widgets/dynamic_form_field_renderers.py:84` | `format_mod_btn_text` | `"🧩 Keinen Programmbereich ausgewählt ▾"` | `tr("dynamic_form.no_mod_selected", "🧩 Keinen Programmbereich ausgewählt ▾")` | `dynamic_form.no_mod_selected` | **NEW** | `🧩 Keinen Programmbereich ausgewählt ▾` | `🧩 No module selected ▾` | `🧩 Ingen modul vald ▾` |
| `src/ui/widgets/dynamic_form_field_renderers.py:90` | `format_mod_btn_text` | `f" (+{len(sel_list)-2} weitere) ▾"` | `tr("dynamic_form.more_mods_suffix", " (+{count} weitere)", count=len(sel_list)-2)` | `dynamic_form.more_mods_suffix` | **NEW** | ` (+{count} weitere)` | ` (+{count} more)` | ` (+{count} fler)` |
| `src/ui/widgets/dynamic_form_field_renderers.py:266` | `filedialog.askopenfilename(title=...)` | `f"Datei auswählen für '{f_item.label}'"` | `tr("dynamic_form.select_file_for", "Datei auswählen für '{label}'", label=f_item.label)` | `dynamic_form.select_file_for` | **NEW** | `Datei auswählen für '{label}'` | `Select file for '{label}'` | `Välj fil för '{label}'` |
| `src/ui/widgets/dynamic_form_widget.py:67` | `self.title(...)` | `"🧩 Programmbereiche auswählen"` | `self.title(tr("dynamic_form.select_tags_dialog_title", "🧩 Programmbereiche auswählen"))` | `dynamic_form.select_tags_dialog_title` | **EXISTING** | `🧩 Programmbereiche auswählen` | `🧩 Select Program Modules` | `🧩 Välj programmoduler` |
| `src/ui/widgets/dynamic_form_widget.py:437` | `CTkButton(text=...)` | `f"🗑 Anfrage #{idx + 1} entfernen"` | `tr("dynamic_form.remove_card", "🗑 Anfrage #{idx} entfernen", idx=idx+1)` | `dynamic_form.remove_card` | **NEW** | `🗑 Anfrage #{idx} entfernen` | `🗑 Remove request #{idx}` | `🗑 Ta bort förfrågan #{idx}` |
| `src/ui/widgets/dynamic_form_widget.py:462` | `CTkButton(text=...)` | `f"➕ Weitere {group_title} anfordern"` | `tr("dynamic_form.add_card", "➕ Weitere {title} anfordern", title=group_title)` | `dynamic_form.add_card` | **NEW** | `➕ Weitere {title} anfordern` | `➕ Request another {title}` | `➕ Begär ytterligare {title}` |
| `src/ui/widgets/dynamic_form_widget.py:533` | `filedialog.askopenfilename(title=...)` | `"Datenbank-Backup (.backup) importieren"` | `filedialog.askopenfilename(title=tr("dynamic_form.import_backup_dialog_title", "Datenbank-Backup (.backup) importieren"))` | `dynamic_form.import_backup_dialog_title` | **EXISTING** | `Datenbank-Backup (.backup) importieren` | `Import Database Backup (.backup)` | `Importera databassäkerhetskopia (.backup)` |
| `src/ui/widgets/dynamic_form_widget.py:534` | `filetypes=[("Backup-Dateien (*.backup)", ...)]` | `"Backup-Dateien (*.backup)"` | `tr("dynamic_form.backup_filetypes", "Backup-Dateien (*.backup)")` | `dynamic_form.backup_filetypes` | **NEW** | `Backup-Dateien (*.backup)` | `Backup Files (*.backup)` | `Säkerhetskopior (*.backup)` |
| `src/ui/widgets/searchable_combobox.py:15` | `placeholder_text` | `"– Bitte auswählen –"` | `tr("common.please_select", "– Bitte auswählen –")` | `common.please_select` | **NEW** | `– Bitte auswählen –` | `– Please select –` | `– Vänligen välj –` |
| `src/ui/widgets/timeline_widget.py:119` | `CTkLabel(text=...)` | `f"Status: {entry.status_change}"` | `tr("timeline.status_prefix", "Status: {status}", status=entry.status_change)` | `timeline.status_prefix` | **NEW** | `Status: {status}` | `Status: {status}` | `Status: {status}` |
| `src/ui/widgets/wiki_widget.py:65` | `status_label.configure(text=...)` | `f"{len(results)} {tr('wiki.articles_found', ...)}"` | `tr("wiki.articles_found_count", "{count} Wiki-Artikel gefunden", count=len(results))` | `wiki.articles_found_count` | **NEW** | `{count} Wiki-Artikel gefunden` | `{count} wiki articles found` | `{count} wiki-artiklar hittades` |

---

## 5. Verification Method

### 5.1 Automated Test Verification Commands
Run the complete automated test suite to confirm existing tests pass without regressions:
```bash
.venv\Scripts\python.exe -m pytest tests/test_ast_i18n_scanner.py tests/test_translation_parity_and_quality.py tests/test_dynamic_language_switch.py tests/test_e2e_multilingual_workflows.py
```

### 5.2 Standalone AST Scan Verification
Verify that after M3 implementation, running AST scanner on `src/ui/app.py`, `src/ui/views/`, and `src/ui/widgets/` yields **0 violations**:
```bash
.venv\Scripts\python.exe -c "
from pathlib import Path
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'tests')
from test_ast_i18n_scanner import scan_python_file

targets = [Path('src/ui/app.py'), Path('src/ui/app_dialogs.py')] + list(Path('src/ui/views').glob('*.py')) + list(Path('src/ui/widgets').glob('*.py'))
all_v = []
for p in targets:
    v = scan_python_file(p)
    if v:
        print(f'{p}: {len(v)} violations')
        all_v.extend(v)
assert len(all_v) == 0, f'Expected 0 violations, found {len(all_v)}'
print('AST Verification PASSED with 0 violations.')
"
```

### 5.3 Locale Parity Verification
Confirm that 100% of newly added keys exist across `locales/de.json`, `locales/en.json`, and `locales/sv.json` without German placeholders in EN or SV:
```bash
.venv\Scripts\python.exe -c "
import json
de = json.load(open('locales/de.json', encoding='utf-8'))
en = json.load(open('locales/en.json', encoding='utf-8'))
sv = json.load(open('locales/sv.json', encoding='utf-8'))

def get_keys(d, prefix=''):
    keys = set()
    for k, v in d.items():
        fk = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            keys.update(get_keys(v, fk))
        else:
            keys.add(fk)
    return keys

de_keys = get_keys(de)
en_keys = get_keys(en)
sv_keys = get_keys(sv)

assert de_keys == en_keys, f'DE vs EN mismatch: {de_keys ^ en_keys}'
assert de_keys == sv_keys, f'DE vs SV mismatch: {de_keys ^ sv_keys}'
print(f'Parity Verified across {len(de_keys)} keys in DE, EN, SV.')
"
```

### 5.4 Invalidation Conditions
- If any UI widget constructor receives a hardcoded non-exempt string literal without wrapping in `tr(...)` or `LocalizedDict`.
- If any key added to `locales/de.json` is missing from `locales/en.json` or `locales/sv.json`.
- If English or Swedish strings contain untranslated German text.
