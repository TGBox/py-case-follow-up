import logging
import threading
import customtkinter as ctk
from pathlib import Path

from config import AppConfig
from enums import LayoutMode
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
from ui.views.tab_view import TabView
from ui.views.split_view import SplitView

from ui.dialogs.new_case_dialog import NewCaseDialog
from ui.dialogs.export_dialog import ExportDialog
from ui.dialogs.schema_builder_dialog import SchemaBuilderDialog
from ui.dialogs.p2p_diff_dialog import P2PDiffDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.customer_management_dialog import CustomerManagementDialog
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

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

        # Configure Window
        self.title("Support Follow-Up & Ticket-Cockpit v1.0.0")
        self.geometry("1440x880")
        self.minsize(1024, 700)

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
        )
        self.tab_view = TabView(self.container_frame, on_select_case=self.on_case_selected)
        self.split_view = SplitView(self.container_frame, on_case_selected=self.on_case_selected, on_search_changed=self.on_search_changed)

        self.active_view = None
        self.switch_layout(self.profile.ui_settings.default_layout)

        # Register Shortcuts & Lifecycle
        self.register_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Startup Wiki Sync if enabled
        if self.profile.wiki_settings.sync_on_startup:
            self.after(1000, lambda: self.wiki_service.sync_from_bookstack())

        # Scoring Timer (every hour)
        self.schedule_hourly_scoring()

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
        menu_frame = ctk.CTkFrame(self, height=45, corner_radius=0)
        menu_frame.pack(fill="x", side="top")

        # App Title
        ctk.CTkLabel(menu_frame, text=" 🩺 Support-Cockpit ", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)

        # Layout Switcher
        ctk.CTkLabel(menu_frame, text="Layout:").pack(side="left", padx=(15, 5))
        layout_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=[LayoutMode.COCKPIT.value, LayoutMode.TAB_VIEW.value, LayoutMode.SPLIT_VIEW.value],
            command=self.switch_layout,
            width=120,
        )
        layout_combo.set(self.profile.ui_settings.default_layout)
        layout_combo.pack(side="left", padx=5)

        # Action Buttons
        new_btn = ctk.CTkButton(menu_frame, text="+ Neuer Fall (Strg+N)", command=self.open_new_case_dialog, width=150, fg_color="forestgreen")
        new_btn.pack(side="left", padx=3)

        cust_btn = ctk.CTkButton(menu_frame, text="🏥 Praxen", command=self.open_customer_management_dialog, width=105)
        cust_btn.pack(side="left", padx=3)

        export_btn = ctk.CTkButton(menu_frame, text="📤 Export", command=lambda: self.open_export_dialog(self.active_case), width=110)
        export_btn.pack(side="left", padx=3)

        builder_btn = ctk.CTkButton(menu_frame, text="🛠️ Formulare", command=self.open_schema_builder_dialog, width=115)
        builder_btn.pack(side="left", padx=3)

        p2p_btn = ctk.CTkButton(menu_frame, text="🔄 P2P-Sync", command=self.open_p2p_dialog, width=110)
        p2p_btn.pack(side="left", padx=3)

        help_btn = ctk.CTkButton(menu_frame, text="📖 Hilfe", command=self.open_help_dialog, width=90, fg_color="gray40")
        help_btn.pack(side="left", padx=3)

        # Right side: User & Theme Toggle
        theme_btn = ctk.CTkButton(menu_frame, text="🌗 Theme", command=self.toggle_theme, width=80, fg_color=("gray70", "gray30"))
        theme_btn.pack(side="right", padx=6)

        self.user_btn = ctk.CTkButton(
            menu_frame,
            text=f"👤 {self.profile.user.name}",
            font=ctk.CTkFont(weight="bold"),
            command=self.open_profile_settings_dialog,
            width=130,
            fg_color="transparent",
            hover_color=("gray80", "gray25")
        )
        self.user_btn.pack(side="right", padx=6)

    def switch_layout(self, layout_name: str):
        if self.active_view:
            self.active_view.pack_forget()

        if layout_name == LayoutMode.TAB_VIEW.value:
            self.tab_view.pack(fill="both", expand=True)
            self.active_view = self.tab_view
        elif layout_name == LayoutMode.SPLIT_VIEW.value:
            self.split_view.pack(fill="both", expand=True)
            self.active_view = self.split_view
        else:
            self.cockpit_view.pack(fill="both", expand=True)
            self.active_view = self.cockpit_view

        self.profile.ui_settings.default_layout = layout_name
        self.refresh_views()

    def refresh_views(self):
        filtered_cases = SearchService.filter_cases(self.cases, self.search_query) if self.search_query else self.cases
        self.cockpit_view.set_schemas(self.schemas)
        self.cockpit_view.set_cases(filtered_cases)
        self.tab_view.set_cases(filtered_cases)
        self.split_view.set_cases(filtered_cases)

    def on_search_changed(self, query: str):
        self.search_query = query
        self.refresh_views()

    def on_case_selected(self, case: Case):
        self.active_case = case

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
        self.profile = self.storage_service.load_profile()
        self.user_btn.configure(text=f"👤 {self.profile.user.name}")
        ctk.set_appearance_mode(self.profile.ui_settings.theme)
        self.scoring_service = ScoringService(self.profile.scoring_matrix)
        self.refresh_views()

    def open_new_case_dialog(self, event=None):
        NewCaseDialog(
            self,
            customers=self.customers,
            schemas=self.schemas,
            created_by=self.profile.user.name,
            on_case_created=self.on_case_created,
            on_customer_added=self.on_quick_customer_added,
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

    def on_closing(self):
        logger.info("Saving application settings and profile before exit...")
        self.storage_service.save_profile(self.profile)
        self.destroy()
