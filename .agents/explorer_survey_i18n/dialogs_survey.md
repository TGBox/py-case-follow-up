# Dialogs Survey

| Dialog File | Main Class | Has `refresh_ui_labels` | `self.title(...)` expression |
| :--- | :--- | :---: | :--- |
| `ai_assistant_dialog.py` | `AiAssistantDialog` | ❌ | L81: `f"{DIALOG_TITLES['ai_assistant']} — Fall [{case.case_id}]"` |
| `calendar_export_dialog.py` | `CalendarExportDialog` | ❌ | L26: `f"{DIALOG_TITLES['calendar_export']} - Fall {case.case_id}"` |
| `case_print_dialog.py` | `CasePrintDialog` | ❌ | L22: `f'🖨 Fall-Akte Druck- & HTML Export: {case.case_id}'` |
| `cobra_import_dialog.py` | `CobraImportDialog` | ❌ | L19: `DIALOG_TITLES['cobra_import']` |
| `colleague_management_dialog.py` | `ColleagueManagementDialog` | ❌ | L24: `DIALOG_TITLES['colleague_mgmt']` |
| `convert_schema_dialog.py` | `ConvertSchemaDialog` | ❌ | L28: `DIALOG_TITLES['convert_schema']` |
| `customer_form_builders.py` | `CustomerFormBuilderMixin` | ❌ | - |
| `customer_management_dialog.py` | `CustomerManagementDialog` | ❌ | L16: `DIALOG_TITLES['customer_mgmt']` |
| `email_calendar_dialog.py` | `EmailCalendarDialog` | ❌ | L28: `f"{DIALOG_TITLES['email_calendar']} - Fall {case.case_id}"` |
| `email_draft_dialog.py` | `EmailDraftDialog` | ❌ | L103: `dialog_title` |
| `email_import_dialog.py` | `EmailImportDialog` | ❌ | L26: `DIALOG_TITLES['email_import']` |
| `export_dialog.py` | `ExportDialog` | ❌ | L24: `f"{DIALOG_TITLES['export']} — {case.case_id}"` |
| `followup_dialog.py` | `FollowupDialog` | ❌ | L22: `'🔔 Wiedervorlage & Nachfrage-Erinnerung'` |
| `followup_flyout_dialog.py` | `FollowupFlyoutDialog` | ❌ | L19: `DIALOG_TITLES['followup_flyout']` |
| `handover_dialog.py` | `HandoverDialog` | ❌ | L34: `f"{DIALOG_TITLES['handover']} (Fall {case.case_id})"` |
| `help_dialog.py` | `HelpDialog` | ❌ | L556: `tr('dialog_titles.help', '📖 Handbuch & Anwendungsdokumentation')` |
| `new_case_dialog.py` | `QuickAddCustomerDialog, NewCaseDialog` | ❌ | L18: `tr('dialog_titles.quick_customer', '🏥 Neue Praxis schnell anlegen')`<br>L94: `tr('dialog_titles.new_case', 'Neuen Support-Fall anlegen')` |
| `p2p_diff_dialog.py` | `P2PDiffDialog` | ❌ | L19: `DIALOG_TITLES['p2p_diff']` |
| `profile_settings_ai_tab.py` | `AiSettingsTabMixin` | ❌ | - |
| `profile_settings_dialog.py` | `HotkeyRecorderDialog, ProfileSettingsDialog` | ✅ | L85: `HOTKEY_RECORDER_TITLE`<br>L148: `tr('profile.title', DIALOG_TITLES['profile_settings'])`<br>L342: `tr('dialog_titles.profile_settings', '⚙ Profil & Anwendungseinstellungen')` |
| `schema_builder_dialog.py` | `NewSchemaDialog, SchemaBuilderDialog` | ❌ | L13: `'🆕 Neues Formular (Schema) erstellen'`<br>L82: `'In-App Formular-Baukasten (Schemata verwalten)'` |
| `snippet_management_dialog.py` | `SnippetManagementDialog` | ❌ | L18: `DIALOG_TITLES['snippet_mgmt']` |
| `snippet_picker_dialog.py` | `SnippetPickerDialog` | ❌ | L23: `'🧩 Textbaustein auswählen & einfügen'` |
| `tag_management_dialog.py` | `TagManagementDialog` | ❌ | L24: `DIALOG_TITLES['tag_mgmt']` |
| `template_manager_dialog.py` | `EditTemplateDialog, TemplateManagerDialog` | ❌ | L29: `'✏ Vorlage bearbeiten' if not is_new else '➕ Neue Export-Vorlage'`<br>L216: `'📄 Export-Vorlagen verwalten'` |
| `zip_import_dialog.py` | `ZipImportPathDialog` | ❌ | L28: `DIALOG_TITLES['zip_import']` |