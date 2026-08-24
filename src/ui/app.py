import logging
import threading
from typing import Any, Callable
import customtkinter as ctk
from pathlib import Path

from config import AppConfig
from enums import LayoutMode, get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY
from models.case import Case
from models.customer import Customer
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from models.profile import UserProfile, Colleague

from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from services.export_service import ExportService
from services.p2p_sync_service import P2PSyncService
from services.search_service import SearchService
from services.schema_service import SchemaService
from services.customer_service import CustomerService

from ui.views.cockpit_view import CockpitView
from ui.views.board_view import BoardView
from ui.views.table_view import TableView

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

logger = logging.getLogger("SupportCockpit")


class SupportCockpitApp(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.app_config = config

        # Initialize Services
        self.storage_service = StorageService(self.app_config)
        self.profile = self.storage_service.load_profile()
        self.customer_service = CustomerService(self.storage_service)
        self.scoring_service = ScoringService(self.profile.scoring_matrix)
        self.attachment_service = AttachmentService(self.app_config)
        self.wiki_service = WikiSyncService(self.app_config, self.profile.wiki_settings)
        self.export_service = ExportService(self.storage_service)
        self.p2p_service = P2PSyncService(self.storage_service)
        from services.calendar_email_service import CalendarEmailService
        self.calendar_email_service = CalendarEmailService(self.app_config.workspace_dir)
        from services.deep_search_service import DeepSearchService
        self.deep_search_service = DeepSearchService(self.app_config.workspace_dir)
        from services.snippet_service import SnippetService
        self.snippet_service = SnippetService(self.app_config.workspace_dir)

        # Configure Window
        self.title("Support Follow-Up & Ticket-Cockpit v1.0.0")
        self.geometry("1440x880")
        self.minsize(1024, 700)
        from utils.ui_utils import center_window
        center_window(self, 1440, 880)

        # Set Theme
        theme_mode = self.profile.ui_settings.theme
        ctk.set_appearance_mode(theme_mode)

        # Load Working Data
        self.cases: list[Case] = []
        self.customers: list[Customer] = []
        self.schemas: list[QuestionSchema] = []
        self.templates: list[ExportTemplate] = []
        self.colleagues: list[Colleague] = []
        self.active_case: Case | None = None
        self.search_query: str = ""

        self.load_all_data()

        # Build UI Structure
        self.create_menu_bar()

        self.container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.container_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.cockpit_view = CockpitView(
            self.container_frame,
            author_name=self.profile.user.name,
            scoring_service=self.scoring_service,
            attachment_service=self.attachment_service,
            wiki_service=self.wiki_service,
            on_case_updated=self.on_case_updated,
            on_case_selected=self.on_case_selected,
            on_search_changed=self.on_search_changed,
            on_open_export_dialog=self.open_export_dialog,
            on_archive_case=self.on_archive_case,
            app_config=self.app_config,
            profile=self.profile,
            storage_service=self.storage_service,
            on_manage_module_tags=self.open_module_tag_management_dialog,
            on_open_email_calendar=self.open_email_calendar_dialog,
            on_open_snippet_picker=self.open_snippet_picker_dialog,
        )
        self.board_view = BoardView(
            self.container_frame,
            on_select_case=self.on_case_selected,
            on_switch_to_cockpit=self.switch_to_cockpit_view_for_case,
            on_open_followup=self.open_followup_dialog_for_case,
            on_toggle_complete=self.on_toggle_complete_for_case,
            on_change_actor=self.open_handover_dialog_for_case,
            app_config=self.app_config,
        )
        self.table_view = TableView(
            self.container_frame,
            author_name=self.profile.user.name,
            scoring_service=self.scoring_service,
            attachment_service=self.attachment_service,
            on_case_updated=self.on_case_updated,
            on_case_selected=self.on_case_selected,
            app_config=self.app_config,
        )
        from ui.views.analytics_view import AnalyticsView
        self.analytics_view = AnalyticsView(self.container_frame)

        self.active_view = None
        self.switch_layout(get_layout_display(self.profile.ui_settings.default_layout))

        # Register Shortcuts & Lifecycle
        self.register_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Startup Wiki Sync if enabled
        if self.profile.wiki_settings.sync_on_startup:
            self.after(1000, lambda: self.wiki_service.sync_from_bookstack())

        # Scoring Timer (every hour) & Followup Timer
        self.schedule_hourly_scoring()
        self.after(2000, self.check_due_followups)

    def load_all_data(self):
        self.cases = self.storage_service.load_cases()
        self.customers = self.storage_service.load_customers()
        self.schemas = self.storage_service.load_schemas()
        self.templates = self.storage_service.load_templates()
        self.colleagues = self.storage_service.load_colleagues()

        # Update scoring on open cases
        for c in self.cases:
            if not c.workflow_status.is_completed:
                self.scoring_service.update_case_scoring(c)

    def create_menu_bar(self):
        menu_frame = ctk.CTkFrame(self, height=48, corner_radius=8)
        menu_frame.pack(fill="x", side="top", padx=10, pady=(10, 6))

        # App Title
        ctk.CTkLabel(menu_frame, text=" 🩺 Support-Cockpit ", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=4)

        # Layout Switcher
        ctk.CTkLabel(menu_frame, text="Layout:").pack(side="left", padx=(12, 5), pady=4)
        layout_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=list(LAYOUT_DISPLAY.values()),
            command=self.switch_layout,
            width=120,
        )
        layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        layout_combo.pack(side="left", padx=5, pady=4)

        # Action Buttons
        new_btn = ctk.CTkButton(menu_frame, text="+ Neuer Fall (Strg+N)", command=self.open_new_case_dialog, width=150, fg_color="forestgreen")
        new_btn.pack(side="left", padx=3, pady=4)

        # Grouped Dropdown 1: Stammdaten
        self.stammdaten_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=["⚙ Stammdaten ▾", "🏥 Praxen", "👥 Mitarbeiter", "🏷 Tags", "🧩 Programmbereiche", "📝 Textbausteine"],
            command=self._on_stammdaten_selected,
            width=165,
        )
        self.stammdaten_combo.set("⚙ Stammdaten ▾")
        self.stammdaten_combo.pack(side="left", padx=3, pady=4)

        # Grouped Dropdown 2: Vorlagen & Formulare
        self.vorlagen_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=["📄 Vorlagen & Formulare ▾", "🛠 Formulare", "📄 Vorlagen"],
            command=self._on_vorlagen_selected,
            width=175,
        )
        self.vorlagen_combo.set("📄 Vorlagen & Formulare ▾")
        self.vorlagen_combo.pack(side="left", padx=3, pady=4)

        # Grouped Dropdown 3: Datenaustausch
        self.datenaustausch_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=["🔄 Datenaustausch ▾", "📤 Export (Strg+E)", "📦 ZIP-Backup", "🔄 P2P-Sync", "📖 Hilfe (F1)"],
            command=self._on_datenaustausch_selected,
            width=155,
        )
        self.datenaustausch_combo.set("🔄 Datenaustausch ▾")
        self.datenaustausch_combo.pack(side="left", padx=3, pady=4)

        # Right side: User, Bell Badge & Theme Toggle
        theme_btn = ctk.CTkButton(menu_frame, text="🌗 Theme", command=self.toggle_theme, width=80, fg_color=("gray70", "gray30"))
        theme_btn.pack(side="right", padx=6, pady=4)

        self.bell_btn = ctk.CTkButton(
            menu_frame,
            text="🔔 0",
            command=self.open_followup_flyout,
            width=65,
            fg_color="gray30",
            hover_color="darkred",
        )
        self.bell_btn.pack(side="right", padx=4, pady=4)

        self.demo_toggle_btn = ctk.CTkButton(
            menu_frame,
            text="🧪 Beispieldaten: AN",
            command=self.toggle_demo_data,
            width=135,
            fg_color="darkblue",
        )
        self.demo_toggle_btn.pack(side="right", padx=4, pady=4)

        self.user_btn = ctk.CTkButton(
            menu_frame,
            text=f"👤 {self.profile.user.name}",
            font=ctk.CTkFont(weight="bold"),
            command=self.open_profile_settings_dialog,
            width=130,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.user_btn.pack(side="right", padx=6, pady=4)

    def _on_stammdaten_selected(self, choice: str):
        self.stammdaten_combo.set("⚙ Stammdaten ▾")
        if choice == "🏥 Praxen":
            self.open_customer_management_dialog()
        elif choice == "👥 Mitarbeiter":
            self.open_colleague_management_dialog()
        elif choice.startswith("🏷"):
            self.open_tag_management_dialog(initial_tab="tags")
        elif choice.startswith("🧩"):
            self.open_module_tag_management_dialog()
        elif choice.startswith("📝"):
            self.open_snippet_management_dialog()

    def _on_vorlagen_selected(self, choice: str):
        self.vorlagen_combo.set("📄 Vorlagen & Formulare ▾")
        if choice.startswith("🛠"):
            self.open_schema_builder_dialog()
        elif choice == "📄 Vorlagen":
            self.open_template_manager_dialog()

    def _on_datenaustausch_selected(self, choice: str):
        self.datenaustausch_combo.set("🔄 Datenaustausch ▾")
        if choice.startswith("📤 Export"):
            self.open_export_dialog(self.active_case)
        elif choice == "📦 ZIP-Backup":
            self.open_zip_export_dialog()
        elif choice == "🔄 P2P-Sync":
            self.open_p2p_dialog()
        elif choice.startswith("📖 Hilfe"):
            self.open_help_dialog()

    def get_filtered_cases(self) -> list[Case]:
        user_cases = [c for c in self.cases if not getattr(c, "is_demo_data", False)]
        has_user_cases = len(user_cases) > 0

        if self.profile.ui_settings.show_demo_data is not None:
            show_demo = self.profile.ui_settings.show_demo_data
        else:
            show_demo = not has_user_cases

        if show_demo:
            return self.cases
        else:
            return user_cases

    def toggle_demo_data(self):
        user_cases = [c for c in self.cases if not getattr(c, "is_demo_data", False)]
        has_user_cases = len(user_cases) > 0
        if self.profile.ui_settings.show_demo_data is not None:
            curr_show = self.profile.ui_settings.show_demo_data
        else:
            curr_show = not has_user_cases

        new_show = not curr_show
        self.profile.ui_settings.show_demo_data = new_show
        self.storage_service.save_profile(self.profile)
        self.refresh_views()

    def switch_layout(self, layout_name: str):
        if self.active_view:
            self.active_view.pack_forget()

        # Handle both display name and internal enum value
        val = get_layout_val_from_display(layout_name)

        if val == LayoutMode.BOARD.value:
            self.board_view.pack(fill="both", expand=True)
            self.active_view = self.board_view
        elif val == LayoutMode.TABLE.value:
            self.table_view.pack(fill="both", expand=True)
            self.active_view = self.table_view
        else:
            self.cockpit_view.pack(fill="both", expand=True)
            self.active_view = self.cockpit_view

        self.profile.ui_settings.default_layout = val
        self.refresh_views()

    def refresh_views(self):
        active_cases = self.get_filtered_cases()
        deep_results = {}
        is_deep_active = (
            hasattr(self.cockpit_view, "left_frame")
            and getattr(self.cockpit_view.left_frame, "is_deep_search_active", False)
        )

        if is_deep_active and self.search_query:
            deep_results = self.deep_search_service.perform_deep_search(active_cases, self.search_query)
            matching_ids = set(deep_results.keys())
            std_filtered = SearchService.filter_cases(active_cases, self.search_query)
            filtered_cases = [c for c in active_cases if c.case_id in matching_ids or c in std_filtered]
        else:
            filtered_cases = SearchService.filter_cases(active_cases, self.search_query) if self.search_query else active_cases

        self.cockpit_view.set_schemas(self.schemas)
        self.cockpit_view.set_cases(filtered_cases, deep_results=deep_results)
        self.board_view.set_cases(filtered_cases)
        self.table_view.set_schemas(self.schemas)
        self.table_view.set_cases(filtered_cases)
        self.analytics_view.set_cases(filtered_cases)

        user_cases = [c for c in self.cases if not getattr(c, "is_demo_data", False)]
        has_user_cases = len(user_cases) > 0
        if self.profile.ui_settings.show_demo_data is not None:
            show_demo = self.profile.ui_settings.show_demo_data
        else:
            show_demo = not has_user_cases

        if hasattr(self, "demo_toggle_btn"):
            if show_demo:
                self.demo_toggle_btn.configure(text="🧪 Beispieldaten: AN", fg_color="darkblue")
            else:
                self.demo_toggle_btn.configure(text="🧪 Beispieldaten: AUS", fg_color="gray40")

    def switch_to_cockpit_view_for_case(self, case: Case):
        self.active_case = case
        if self.active_view != self.cockpit_view:
            self.switch_layout(get_layout_display(LayoutMode.COCKPIT.value))
        self.cockpit_view.on_select_case_from_list(case)

    def open_followup_dialog_for_case(self, case: Case):
        from ui.dialogs.followup_dialog import FollowupDialog

        def on_followup_set(dt_iso: str, note_text: str):
            case.workflow_status.followup_at = dt_iso
            if note_text:
                from models.case import TimelineEntry
                from utils.datetime_utils import now_iso
                from enums import Channel
                entry = TimelineEntry(
                    timestamp=now_iso(),
                    author=self.profile.user.name,
                    channel=Channel.INTERNAL_NOTE.value,
                    note=f"Wiedervorlage gesetzt auf: {dt_iso}. {note_text}",
                )
                case.timeline.append(entry)
            self.on_case_updated(case)

        FollowupDialog(self, case=case, on_followup_set=on_followup_set)

    def on_toggle_complete_for_case(self, case: Case):
        case.workflow_status.is_completed = not case.workflow_status.is_completed
        if case.workflow_status.is_completed:
            case.workflow_status.followup_at = ""
        self.on_case_updated(case)

    def open_handover_dialog_for_case(self, case: Case):
        from ui.dialogs.handover_dialog import HandoverDialog
        from enums import get_actor_display, Channel
        from models.case import TimelineEntry
        from utils.datetime_utils import now_iso

        def on_confirmed(new_actor_val: str, channel: str, person: str, note: str):
            prev_actor_val = case.workflow_status.current_actor
            case.workflow_status.current_actor = new_actor_val
            case.workflow_status.actor_since = now_iso()

            person_str = f" ({person})" if person else ""
            note_str = f" | Details: {note}" if note else ""
            note_text = f"Zuständigkeit übergeben an: {get_actor_display(new_actor_val)}{person_str} via {channel}{note_str}"
            change_text = f"ZUSTÄNDIGKEIT: {get_actor_display(prev_actor_val)} -> {get_actor_display(new_actor_val)}"

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
        self.active_case = case
        if self.active_view != self.cockpit_view or self.cockpit_view.current_case != case:
            self.switch_to_cockpit_view_for_case(case)

    def on_case_updated(self, case: Case):
        self.scoring_service.update_case_scoring(case)
        self.storage_service.save_cases(self.cases)
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

    def open_profile_settings_dialog(self):
        ProfileSettingsDialog(
            self,
            profile=self.profile,
            storage_service=self.storage_service,
            on_profile_updated=self.on_profile_updated,
        )

    def on_profile_updated(self):
        self.load_all_data()
        self.profile = self.storage_service.load_profile()
        self.user_btn.configure(text=f"👤 {self.profile.user.name}")
        self.cockpit_view.author_name = self.profile.user.name
        ctk.set_appearance_mode(self.profile.ui_settings.theme)
        self.scoring_service = ScoringService(self.profile.scoring_matrix)
        self.refresh_views()

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

    def open_snippet_picker_dialog(self, callback: Any):
        from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
        SnippetPickerDialog(self, snippet_service=self.snippet_service, on_snippet_selected=callback)

    def open_snippet_management_dialog(self):
        from ui.dialogs.snippet_management_dialog import SnippetManagementDialog
        SnippetManagementDialog(self, snippet_service=self.snippet_service)

    def toggle_theme(self):
        curr = ctk.get_appearance_mode()
        new_theme = "Light" if curr == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self.profile.ui_settings.theme = new_theme
        self.refresh_views()

    def register_shortcuts(self):
        shortcuts = self.profile.shortcuts
        import tkinter as tk
        tk.Misc.bind_all(self, shortcuts.new_case, self.open_new_case_dialog)
        tk.Misc.bind_all(self, shortcuts.export_dialog, lambda e: self.open_export_dialog(self.active_case))
        tk.Misc.bind_all(self, shortcuts.wiki_search, lambda e: self.cockpit_view.focus_wiki_search())
        tk.Misc.bind_all(self, shortcuts.save_case, lambda e: self.cockpit_view.on_click_save())
        tk.Misc.bind_all(self, "<F1>", lambda e: self.open_help_dialog())

    def schedule_hourly_scoring(self):
        def update_timer():
            logger.info("Hourly scoring background update triggered.")
            for c in self.cases:
                if not c.workflow_status.is_completed:
                    self.scoring_service.update_case_scoring(c)
            self.storage_service.save_cases(self.cases)
            self.after(0, self.refresh_views)
            # Reschedule in 3600 seconds
            timer = threading.Timer(3600, update_timer)
            timer.daemon = True
            timer.start()

        timer = threading.Timer(3600, update_timer)
        timer.daemon = True
        timer.start()

    def open_zip_export_dialog(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService

        dest_file = filedialog.asksaveasfilename(
            title="Komplett-Datensicherung als ZIP speichern",
            defaultextension=".zip",
            filetypes=[("ZIP-Archiv", "*.zip")],
            initialfile="SupportCockpit_Backup.zip",
            parent=self,
        )
        if dest_file:
            res = ZipBackupService.export_backup_zip(self.storage_service, Path(dest_file))
            mb_size = res["total_bytes"] / (1024 * 1024)
            print(f"✅ ZIP-Backup exportiert: {res['file_count']} Dateien ({mb_size:.2f} MB)")

    def check_due_followups(self):
        from utils.datetime_utils import parse_german_date, parse_iso, get_local_now
        from ui.widgets.toast_notification import ToastNotification
        now = get_local_now()
        due_cases = []

        for c in self.get_filtered_cases():
            if c.workflow_status.followup_at and not c.workflow_status.is_completed:
                try:
                    f_str = c.workflow_status.followup_at
                    if "." in f_str:
                        iso_str = parse_german_date(f_str)
                        dt = parse_iso(iso_str)
                    else:
                        dt = parse_iso(f_str)
                    if dt <= now:
                        due_cases.append(c)
                except Exception:
                    pass

        due_count = len(due_cases)
        if due_count > 0:
            self.bell_btn.configure(text=f"🔔 {due_count}", fg_color="darkred")
            if not getattr(self, "_last_notified_due_count", 0) or due_count > self._last_notified_due_count:
                top_case = due_cases[0]
                ToastNotification(
                    self,
                    title=f"🔔 Wiedervorlage fällig ({due_count})",
                    message=f"[{top_case.case_id}] {top_case.classification.title}",
                    on_open=lambda c=top_case: self.switch_to_cockpit_view_for_case(c),
                )
            self._last_notified_due_count = due_count
        else:
            self.bell_btn.configure(text="🔔 0", fg_color="gray30")
            self._last_notified_due_count = 0

        self.after(60000, self.check_due_followups)

    def open_followup_flyout(self):
        from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
        from utils.datetime_utils import parse_german_date, parse_iso, get_local_now
        now = get_local_now()
        due_cases = []

        for c in self.get_filtered_cases():
            if c.workflow_status.followup_at and not c.workflow_status.is_completed:
                try:
                    f_str = c.workflow_status.followup_at
                    if "." in f_str:
                        iso_str = parse_german_date(f_str)
                        dt = parse_iso(iso_str)
                    else:
                        dt = parse_iso(f_str)
                    if dt <= now:
                        due_cases.append(c)
                except Exception:
                    pass

        def on_refresh():
            self.storage_service.save_cases(self.cases)
            self.refresh_views()
            self.check_due_followups()

        FollowupFlyoutDialog(self, due_cases, on_case_selected=self.on_case_selected, on_refresh=on_refresh)

    def on_closing(self):
        logger.info("Saving application settings and profile before exit...")
        self.storage_service.save_profile(self.profile)
        self.destroy()
