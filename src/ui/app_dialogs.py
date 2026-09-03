"""Dialog-Orchestrierung fuer SupportCockpitApp: alle "open_*_dialog"-Methoden,
ihre Abschluss-Callbacks ("on_*_updated/completed") sowie die eng damit verzahnten
Fallauswahl-Events (on_search_changed, on_case_selected, on_case_updated, on_archive_case).

Ausgelagert aus app.py (Refactoring): dieser zusammenhaengende Block machte gut
28% der Datei aus. DialogLaunchersMixin wird per Mixin-Vererbung in
SupportCockpitApp eingemischt, sodass `self` weiterhin dieselbe App-Instanz ist
und alle hier aufgerufenen self.-Attribute (self.storage_service, self.cases,
self.cockpit_view, usw.) unveraendert funktionieren. Reines Verschieben von
Code, keine Verhaltensaenderung.
"""
from typing import TYPE_CHECKING, Any, Callable
import customtkinter as ctk
from models.case import Case
from models.customer import Customer
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from services.schema_service import SchemaService
from services.scoring_service import ScoringService

from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.dialogs.export_dialog import ExportDialog
from ui.dialogs.schema_builder_dialog import SchemaBuilderDialog
from ui.dialogs.template_manager_dialog import TemplateManagerDialog
from ui.dialogs.p2p_diff_dialog import P2PDiffDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.customer_management_dialog import CustomerManagementDialog
from ui.dialogs.colleague_management_dialog import ColleagueManagementDialog
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from ui.dialogs.tag_management_dialog import TagManagementDialog


class DialogLaunchersMixin:
    """Oeffnet alle Dialoge aus dem Hauptfenster heraus und verarbeitet deren
    Abschluss-Callbacks, plus die eng verwandten Fallauswahl-Events. Nur zusammen
    mit SupportCockpitApp (bzw. einer Klasse mit denselben self.storage_service /
    self.cases / self.cockpit_view / ... Attributen) nutzbar.
    """

    if TYPE_CHECKING:
        active_view: Any
        cockpit_view: Any
        board_view: Any
        table_view: Any
        analytics_view: Any
        active_case: Any
        cases: list[Any]
        schemas: list[Any]
        profile: Any
        user_btn: Any
        scoring_service: Any
        storage_service: Any
        customer_service: Any
        export_service: Any
        p2p_service: Any
        calendar_email_service: Any
        snippet_service: Any
        deep_search_service: Any
        search_query: str
        refresh_views: Callable[..., Any]
        bring_to_foreground: Callable[[], None]
        switch_to_cockpit_view_for_case: Callable[[Any], None]
        on_language_changed: Callable[[str], None]
        load_all_data: Callable[[], None]
        on_case_updated: Callable[[Any], None]
        on_customers_updated: Callable[[], None]
        on_tags_updated: Callable[[], None]

    def open_followup_dialog_for_case(self, case: Case):
        from ui.dialogs.followup_dialog import FollowupDialog

        def on_followup_set(dt_iso: str, note_text: str):
            case.workflow_status.followup_at = dt_iso
            if note_text:
                from models.case import TimelineEntry
                from utils.datetime_utils import now_iso
                from enums import Channel
                from services.i18n_service import tr
                entry = TimelineEntry(
                    timestamp=now_iso(),
                    author=self.profile.user.name,
                    channel=Channel.INTERNAL_NOTE.value,
                    note=tr("timeline.followup_set_note", "Wiedervorlage gesetzt auf: {date}. {note}", date=dt_iso, note=note_text),
                )
                case.timeline.append(entry)
            self.on_case_updated(case)
            if self.active_case and self.active_case.case_id == case.case_id:
                if self.active_view == self.cockpit_view and hasattr(self.cockpit_view, "_update_wiedervorlage_display"):
                    self.cockpit_view._update_wiedervorlage_display()

        FollowupDialog(self, case=case, on_followup_set=on_followup_set)

    def on_toggle_complete_for_case(self, case: Case):
        from services.i18n_service import tr
        new_state = not case.workflow_status.is_completed
        case.workflow_status.is_completed = new_state
        if new_state:
            case.workflow_status.followup_at = ""
            note_text = tr("timeline.case_completed", "Fall auf erledigt gesetzt.")
            change_text = tr("timeline.status_completed", "STATUS: Erledigt")
        else:
            note_text = tr("timeline.case_reopened", "Fall wieder geöffnet.")
            change_text = tr("timeline.status_open", "STATUS: Offen")

        from models.case import TimelineEntry
        from utils.datetime_utils import now_iso
        from enums import Channel

        entry = TimelineEntry(
            timestamp=now_iso(),
            author=self.profile.user.name,
            channel=Channel.INTERNAL_NOTE.value,
            note=note_text,
            status_change=change_text,
        )
        case.timeline.append(entry)
        self.on_case_updated(case)

    def open_handover_dialog_for_case(self, case: Case):
        from ui.dialogs.handover_dialog import HandoverDialog
        from enums import get_actor_display, Channel
        from models.case import TimelineEntry
        from utils.datetime_utils import now_iso
        from services.i18n_service import tr

        def on_confirmed(new_actor_val: str, channel: str, person: str, note: str):
            prev_actor_val = case.workflow_status.current_actor
            case.workflow_status.current_actor = new_actor_val
            case.workflow_status.actor_since = now_iso()

            person_str = f" ({person})" if person else ""
            note_str = f" | Details: {note}" if note else ""
            note_text = tr("timeline.handover_note", "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}", actor=get_actor_display(new_actor_val), person=person_str, channel=channel, note=note_str)
            change_text = tr("timeline.handover_status", "ZUSTÄNDIGKEIT: {prev} -> {curr}", prev=get_actor_display(prev_actor_val), curr=get_actor_display(new_actor_val))

            entry = TimelineEntry(
                timestamp=now_iso(),
                author=self.profile.user.name,
                channel=Channel.INTERNAL_NOTE.value,
                note=note_text,
                status_change=change_text,
            )
            case.timeline.append(entry)
            self.on_case_updated(case)

        HandoverDialog(
            self,
            case=case,
            colleagues=self.colleagues,
            on_handover_confirmed=on_confirmed,
        )

    def on_search_changed(self, query: str):
        self.search_query = query
        self.refresh_views()

    def on_case_selected(self, case: Case):
        self.bring_to_foreground()
        self.active_case = case
        if self.active_view != self.cockpit_view or self.cockpit_view.current_case != case:
            self.switch_to_cockpit_view_for_case(case)

    def on_case_updated(self, case: Case):
        self.scoring_service.update_case_scoring(case)
        self.storage_service.update_single_case(case)
        self.refresh_views()

    def on_archive_case(self, case: Case):
        success = self.storage_service.archive_single_case(case.case_id)
        if success:
            self.cases = [c for c in self.cases if c.case_id != case.case_id]
            self.active_case = None
            self.refresh_views()

    # --- Dialog Openers ---
    def open_help_dialog(self):
        HelpDialog(self)

    def open_customer_management_dialog(self):
        CustomerManagementDialog(
            self,
            customer_service=self.customer_service,
            on_customers_updated=self.on_customers_updated,
        )

    def on_customers_updated(self):
        self.customers = self.storage_service.load_customers()

    def open_cobra_import_dialog(self):
        from ui.dialogs.cobra_import_dialog import CobraImportDialog
        CobraImportDialog(
            self,
            existing_customers=self.customers,
            on_import_completed=self.on_cobra_import_completed,
        )

    def on_cobra_import_completed(self, merged_customers: list[Customer]):
        for c in merged_customers:
            self.customer_service.save_customer(c)
        self.on_customers_updated()

    def open_profile_settings_dialog(self):
        ProfileSettingsDialog(
            self,
            profile=self.profile,
            storage_service=self.storage_service,
            on_profile_updated=self.on_profile_updated,
        )

    def on_profile_updated(self):
        from services.i18n_service import get_i18n
        self.load_all_data()
        self.profile = self.storage_service.load_profile()
        if hasattr(self, "user_btn") and self.user_btn and self.user_btn.winfo_exists():
            self.user_btn.configure(text=f"👤 {self.profile.user.name}")
        self.cockpit_view.author_name = self.profile.user.name
        ctk.set_appearance_mode(self.profile.ui_settings.theme)
        self.scoring_service = ScoringService(self.profile.scoring_matrix)
        lang_code = getattr(self.profile.ui_settings, "language", "de")
        get_i18n().current_language = lang_code
        self.on_language_changed(lang_code)

    def open_tag_management_dialog(self, initial_tab: str = "tags"):
        TagManagementDialog(
            self,
            profile=self.profile,
            storage_service=self.storage_service,
            on_tags_updated=self.on_tags_updated,
            initial_tab=initial_tab,
        )

    def open_module_tag_management_dialog(self):
        self.open_tag_management_dialog(initial_tab="modules")

    def on_tags_updated(self):
        self.profile = self.storage_service.load_profile()

    def on_tag_added(self, new_tag: str):
        if new_tag not in self.profile.available_tags:
            self.profile.available_tags.append(new_tag)
            self.storage_service.save_profile(self.profile)

    def open_new_case_dialog(self, event=None):
        NewCaseDialog(
            self,
            customers=self.customers,
            schemas=self.schemas,
            created_by=self.profile.user.name,
            on_case_created=self.on_case_created,
            on_customer_added=self.on_quick_customer_added,
            available_tags=self.profile.available_tags,
            on_tag_added=self.on_tag_added,
        )

    def on_quick_customer_added(self, new_customer: Customer):
        self.customer_service.save_customer(new_customer)
        self.customers = self.storage_service.load_customers()

    def on_case_created(self, new_case: Case):
        self.scoring_service.update_case_scoring(new_case)
        self.cases.append(new_case)
        self.storage_service.save_cases(self.cases)
        self.refresh_views()
        self.cockpit_view.on_select_case_from_list(new_case)

    def open_export_dialog(self, case: Case | None = None, event=None):
        target_case = case or self.active_case
        if not target_case:
            return
        ExportDialog(
            self,
            case=target_case,
            templates=self.templates,
            schemas=self.schemas,
            export_service=self.export_service,
            on_case_updated=self.on_case_updated,
        )

    def open_case_print_dialog(self, case: Case | None = None):
        target_case = case or self.active_case
        if not target_case:
            return
        from ui.dialogs.case_print_dialog import CasePrintDialog
        CasePrintDialog(self, target_case)

    def open_schema_builder_dialog(self):
        SchemaBuilderDialog(
            self,
            schemas=self.schemas,
            schema_service=SchemaService(self.storage_service),
            on_schemas_updated=self.on_schemas_updated,
        )

    def on_schemas_updated(self, updated_schemas: list[QuestionSchema]):
        self.schemas = updated_schemas
        self.refresh_views()

    def open_template_manager_dialog(self):
        TemplateManagerDialog(
            self,
            templates=self.templates,
            schemas=self.schemas,
            storage_service=self.storage_service,
            export_service=self.export_service,
            on_templates_updated=self.on_templates_updated,
        )

    def on_templates_updated(self, updated_templates: list[ExportTemplate]):
        self.templates = updated_templates
        self.refresh_views()

    def open_colleague_management_dialog(self):
        ColleagueManagementDialog(
            self,
            storage_service=self.storage_service,
            on_colleagues_updated=self.on_colleagues_updated,
        )

    def on_colleagues_updated(self):
        self.colleagues = self.storage_service.load_colleagues()

    def open_p2p_dialog(self):
        P2PDiffDialog(
            self,
            colleagues=self.colleagues,
            p2p_service=self.p2p_service,
            on_sync_completed=self.on_p2p_sync_completed,
        )

    def on_p2p_sync_completed(self):
        self.load_all_data()
        self.refresh_views()

    def open_email_calendar_dialog(self, case: Case):
        from ui.dialogs.email_calendar_dialog import EmailCalendarDialog
        EmailCalendarDialog(
            self,
            case=case,
            calendar_email_service=self.calendar_email_service,
            user_name=self.profile.user.name,
            snippet_service=self.snippet_service,
        )

    def open_email_draft_dialog(self, case: Case | None = None):
        from ui.dialogs.email_draft_dialog import EmailDraftDialog
        customers = self.storage_service.load_customers() if self.storage_service else []
        EmailDraftDialog(
            self,
            case=case,
            calendar_email_service=self.calendar_email_service,
            user_name=self.profile.user.name,
            snippet_service=self.snippet_service,
            customers=customers,
            storage_service=self.storage_service,
            profile=self.profile,
        )

    def open_email_import_dialog(self):
        from ui.dialogs.email_import_dialog import EmailImportDialog
        EmailImportDialog(
            self,
            cases=self.cases,
            on_case_created=self.on_case_created,
            on_case_updated=self.on_case_updated,
            author_name=self.profile.user.name,
        )

    def open_calendar_export_dialog(self, case: Case):
        from ui.dialogs.calendar_export_dialog import CalendarExportDialog
        CalendarExportDialog(
            self,
            case=case,
            calendar_email_service=self.calendar_email_service,
        )

    def open_snippet_picker_dialog(self, callback: Any):
        from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
        SnippetPickerDialog(self, snippet_service=self.snippet_service, on_snippet_selected=callback)

    def open_snippet_management_dialog(self):
        from ui.dialogs.snippet_management_dialog import SnippetManagementDialog
        SnippetManagementDialog(self, snippet_service=self.snippet_service)
