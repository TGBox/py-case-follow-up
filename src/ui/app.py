import logging
import sys
import threading
import ctypes
from typing import Any, Callable, cast
import customtkinter as ctk
from pathlib import Path

from config import AppConfig
from enums import LayoutMode, get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY
from models.case import Case
from models.customer import Customer
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from models.profile import UserProfile, Colleague
from constants import (
    APP_WINDOW_TITLE,
    APP_MIN_WIDTH,
    APP_MIN_HEIGHT,
    FOLLOWUP_CHECK_INITIAL_DELAY_MS,
    AUTO_ARCHIVE_THRESHOLD_DAYS,
    MENU_OPTIONS_STAMMDATEN,
    MENU_OPTIONS_VORLAGEN,
    MENU_OPTIONS_DATENAUSTAUSCH,
    TOAST_SNIPPET_MACRO_TITLE,
    TOAST_SNIPPET_NO_FOCUS,
)

from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from services.export_service import ExportService
from services.p2p_sync_service import P2PSyncService
from services.search_service import SearchService
from services.schema_service import SchemaService
from services.customer_service import CustomerService
from services.tray_service import TrayService
from services.i18n_service import tr

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
from ui.widgets.toast_notification import ToastNotification
from ui.app_dialogs import DialogLaunchersMixin

logger = logging.getLogger("SupportCockpit")


class SupportCockpitApp(DialogLaunchersMixin, ctk.CTk):
    def __init__(self, config: AppConfig):
        # Deactivate CustomTkinter's internal header manipulation which causes multiple withdraw/update/deiconify cycles on Windows
        setattr(ctk.CTk, "_deactivate_windows_window_header_manipulation", True)

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

        # Set Theme
        theme_mode = self.profile.ui_settings.theme
        ctk.set_appearance_mode(theme_mode)

        # Configure Window directly in maximized mode
        self.title(tr("app.window_title", APP_WINDOW_TITLE))
        self.geometry("1440x880")
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.apply_windows_theme(theme_mode == "Dark")

        # Load Working Data
        self.cases: list[Case] = []
        self.customers: list[Customer] = []
        self.schemas: list[QuestionSchema] = []
        self.templates: list[ExportTemplate] = []
        self.colleagues: list[Colleague] = []
        self.active_case: Case | None = None
        self.search_query: str = ""

        self.load_all_data()

        from services.i18n_service import get_i18n
        get_i18n().current_language = getattr(self.profile.ui_settings, "language", "de")
        get_i18n().register_listener(self.on_language_changed)

        # Build UI Structure
        self.menu_frame: ctk.CTkFrame | None = None
        self.create_menu_bar()

        self.container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.container_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Startup Splash Screen Overlay (prevents layout shifting on launch)
        self.splash_overlay: ctk.CTkFrame | None = ctk.CTkFrame(self, fg_color=("gray95", "gray12"))
        self.splash_overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        splash_box = ctk.CTkFrame(self.splash_overlay, fg_color="transparent")
        splash_box.place(relx=0.5, rely=0.5, anchor="center")

        self.splash_title_lbl = ctk.CTkLabel(splash_box, text=tr("splash.title", "🩺 Support-Cockpit"), font=ctk.CTkFont(size=26, weight="bold"), text_color="dodgerblue")
        self.splash_title_lbl.pack(pady=(0, 8))
        self.splash_msg_lbl = ctk.CTkLabel(splash_box, text=tr("splash.loading", "⏳ Anwendungsdaten und Layouts werden geladen..."), font=ctk.CTkFont(size=14), text_color=("gray40", "gray70"))
        self.splash_msg_lbl.pack()

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
            on_open_email=self.open_email_draft_dialog,
            on_open_calendar=self.open_calendar_export_dialog,
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

        # Geometry tracking for multi-monitor positioning
        self._last_geometry: tuple[int, int, int, int] | None = None
        self.bind("<Configure>", self._on_window_configure, add="+")

        # System Tray Service
        self.tray_service = TrayService()
        self.tray_service.start(
            on_restore=self._on_restore_from_tray,
            on_quit=self._on_quit_from_tray,
        )

        # Register Shortcuts & Lifecycle
        self.register_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Startup Wiki Sync in background thread if enabled
        if self.profile.wiki_settings.sync_on_startup:
            def _on_startup_sync_done(success: bool, msg: str):
                def _update_ui():
                    if hasattr(self, "cockpit_view") and hasattr(self.cockpit_view, "wiki_widget"):
                        self.cockpit_view.wiki_widget.on_sync_finished(success, msg)
                self.after(0, _update_ui)

            self.after(1000, lambda: self.wiki_service.sync_from_bookstack_async(callback=_on_startup_sync_done))

        # Scoring Timer (every hour) & Followup Timer
        self.schedule_hourly_scoring()
        self.after(FOLLOWUP_CHECK_INITIAL_DELAY_MS, self.check_due_followups)

        # Hide splash screen smoothly after initial layout pass
        self.update_idletasks()
        self.after(250, self._hide_splash_screen)

    def _on_window_configure(self, event=None):
        try:
            if self.state() != "iconic" and self.winfo_viewable():
                x, y, w, h = self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height()
                if x > -30000 and y > -30000 and w > 100 and h > 100:
                    self._last_geometry = (x, y, w, h)
        except Exception:
            pass

    def _hide_splash_screen(self):
        if hasattr(self, "splash_overlay") and self.splash_overlay:
            try:
                self.splash_overlay.destroy()
                self.splash_overlay = None
            except Exception:
                pass

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

    def on_language_changed(self, lang_code: str):
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

    def create_menu_bar(self):
        from services.i18n_service import tr
        if hasattr(self, "menu_frame") and self.menu_frame and self.menu_frame.winfo_exists():
            self.menu_frame.destroy()

        self.menu_frame = ctk.CTkFrame(self, height=48, corner_radius=8)
        if hasattr(self, "container_frame") and self.container_frame and self.container_frame.winfo_exists():
            self.menu_frame.pack(fill="x", side="top", padx=10, pady=(10, 6), before=self.container_frame)
        else:
            self.menu_frame.pack(fill="x", side="top", padx=10, pady=(10, 6))
        menu_frame = self.menu_frame

        # App Title
        ctk.CTkLabel(menu_frame, text=tr("menu.title", " 🩺 Support-Cockpit "), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=4)

        # Layout Switcher
        ctk.CTkLabel(menu_frame, text=tr("menu.layout", "Layout:")).pack(side="left", padx=(12, 5), pady=4)
        self.layout_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=list(LAYOUT_DISPLAY.values()),
            command=self.switch_layout,
            width=120,
        )
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        self.layout_combo.pack(side="left", padx=5, pady=4)

        # Action Buttons
        new_btn = ctk.CTkButton(menu_frame, text=tr("menu.new_case", "+ Neuer Fall (Strg+N)"), command=self.open_new_case_dialog, width=150, fg_color="forestgreen")
        new_btn.pack(side="left", padx=3, pady=4)

        from constants import (
            get_localized_menu_options_stammdaten,
            get_localized_menu_options_vorlagen,
            get_localized_menu_options_datenaustausch,
        )

        # Grouped Dropdown 1: Stammdaten
        self.stammdaten_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=get_localized_menu_options_stammdaten(),
            command=self._on_stammdaten_selected,
            width=150,
        )
        self.stammdaten_combo.set(tr("menu.master_data", "⚙ Stammdaten"))
        self.stammdaten_combo.pack(side="left", padx=3, pady=4)

        # Grouped Dropdown 2: Vorlagen & Formulare
        self.vorlagen_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=get_localized_menu_options_vorlagen(),
            command=self._on_vorlagen_selected,
            width=165,
        )
        self.vorlagen_combo.set(tr("menu.templates", "📄 Vorlagen & Formulare"))
        self.vorlagen_combo.pack(side="left", padx=3, pady=4)

        # Grouped Dropdown 3: Datenaustausch
        self.datenaustausch_combo = ctk.CTkOptionMenu(
            menu_frame,
            values=get_localized_menu_options_datenaustausch(),
            command=self._on_datenaustausch_selected,
            width=145,
        )
        self.datenaustausch_combo.set(tr("menu.data_exchange", "🔄 Datenaustausch"))
        self.datenaustausch_combo.pack(side="left", padx=3, pady=4)

        # Right side: User, Bell Badge & Theme Toggle
        quit_btn = ctk.CTkButton(menu_frame, text=tr("menu.quit", "❌ Beenden"), command=self.on_quit_app, width=90, fg_color="#8B0000", hover_color="#B22222")
        quit_btn.pack(side="right", padx=6, pady=4)

        theme_btn = ctk.CTkButton(menu_frame, text=tr("menu.theme", "🌗 Theme"), command=self.toggle_theme, width=80, fg_color=("gray70", "gray30"))
        theme_btn.pack(side="right", padx=4, pady=4)

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
            text=tr("menu.demo_on", "🧪 Beispieldaten: AN"),
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
            text_color=("gray10", "gray90"),
            hover_color=("gray80", "gray25")
        )
        self.user_btn.pack(side="right", padx=6, pady=4)

    def _on_stammdaten_selected(self, choice: str):
        from services.i18n_service import tr
        self.stammdaten_combo.set(tr("menu.master_data", "⚙ Stammdaten"))
        if choice.startswith("🏥"):
            self.open_customer_management_dialog()
        elif choice.startswith("🐍"):
            self.open_cobra_import_dialog()
        elif choice.startswith("👥"):
            self.open_colleague_management_dialog()
        elif choice.startswith("🧩"):
            self.open_module_tag_management_dialog()
        elif choice.startswith("🏷"):
            self.open_tag_management_dialog(initial_tab="tags")

    def _on_vorlagen_selected(self, choice: str):
        from services.i18n_service import tr
        self.vorlagen_combo.set(tr("menu.templates", "📄 Vorlagen & Formulare"))
        if choice.startswith("🛠"):
            self.open_schema_builder_dialog()
        elif choice.startswith("📄"):
            self.open_template_manager_dialog()
        elif choice.startswith("📝"):
            self.open_snippet_management_dialog()
        elif choice.startswith("🏷"):
            self.open_tag_management_dialog(initial_tab="tags")

    def _on_datenaustausch_selected(self, choice: str):
        from services.i18n_service import tr
        self.datenaustausch_combo.set(tr("menu.data_exchange", "🔄 Datenaustausch"))
        if choice.startswith("📥"):
            self.open_email_import_dialog()
        elif choice.startswith("📤"):
            self.open_export_dialog(self.active_case)
        elif choice.startswith("📦"):
            self.open_zip_export_dialog()
        elif choice.startswith("🔄"):
            self.open_p2p_dialog()
        elif choice.startswith("📖"):
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
        elif val == LayoutMode.ANALYTICS.value:
            self.analytics_view.pack(fill="both", expand=True)
            self.active_view = self.analytics_view
        else:
            self.cockpit_view.pack(fill="both", expand=True)
            self.active_view = self.cockpit_view

        if self.__dict__.get("layout_combo"):
            self.layout_combo.set(get_layout_display(val))

        self.profile.ui_settings.default_layout = val
        self.storage_service.save_profile(self.profile)
        self.refresh_views()

    def refresh_views(self, force_all: bool = False):
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

        # Optimize view updates: update active view immediately; mark inactive views dirty for layout switch
        if force_all:
            self.cockpit_view.set_cases(filtered_cases, deep_results=deep_results)
            if hasattr(self.cockpit_view, "update_sash_color"):
                self.cockpit_view.update_sash_color()
            self.board_view.set_cases(filtered_cases)
            self.table_view.set_schemas(self.schemas)
            self.table_view.set_cases(filtered_cases)
            self.analytics_view.set_cases(filtered_cases)
            self._cockpit_dirty = False
            self._board_dirty = False
            self._table_dirty = False
            self._analytics_dirty = False
        else:
            if self.active_view == self.board_view:
                self.board_view.set_cases(filtered_cases)
                self._board_dirty = False
                self._cockpit_dirty = True
                self._table_dirty = True
                self._analytics_dirty = True
            elif self.active_view == self.table_view:
                self.table_view.set_schemas(self.schemas)
                self.table_view.set_cases(filtered_cases)
                self._table_dirty = False
                self._cockpit_dirty = True
                self._board_dirty = True
                self._analytics_dirty = True
            elif self.active_view == self.analytics_view:
                self.analytics_view.set_cases(filtered_cases)
                self._analytics_dirty = False
                self._cockpit_dirty = True
                self._board_dirty = True
                self._table_dirty = True
            else:
                self.cockpit_view.set_cases(filtered_cases, deep_results=deep_results)
                if hasattr(self.cockpit_view, "update_sash_color"):
                    self.cockpit_view.update_sash_color()
                self._cockpit_dirty = False
                self._board_dirty = True
                self._table_dirty = True
                self._analytics_dirty = True

        user_cases = [c for c in self.cases if not getattr(c, "is_demo_data", False)]
        has_user_cases = len(user_cases) > 0
        if self.profile.ui_settings.show_demo_data is not None:
            show_demo = self.profile.ui_settings.show_demo_data
        else:
            show_demo = not has_user_cases

        from services.i18n_service import tr
        if self.__dict__.get("demo_toggle_btn"):
            if show_demo:
                self.demo_toggle_btn.configure(text=tr("menu.demo_on", "🧪 Beispieldaten: AN"), fg_color="darkblue")
            else:
                self.demo_toggle_btn.configure(text=tr("menu.demo_off", "🧪 Beispieldaten: AUS"), fg_color="gray40")

        self.check_due_followups()

    def bring_to_foreground(self):
        """Restore main window from minimized/withdrawn state and bring it to the foreground on OS level."""
        if "tk" not in self.__dict__ or self.tk is None:
            return

        def _restore():
            try:
                if self.state() == "iconic" or not self.winfo_viewable():
                    self.deiconify()
                if self.state() == "iconic":
                    self.state("zoomed")
                self.lift()
                self.focus_force()
                self.attributes("-topmost", True)
                self.attributes("-topmost", False)
            except Exception as e:
                logger.warning(f"Error bringing app window to foreground: {e}")

        try:
            self.after(0, _restore)
        except Exception:
            pass

    def switch_to_cockpit_view_for_case(self, case: Case):
        self.bring_to_foreground()
        self.active_case = case
        if self.active_view != self.cockpit_view:
            self.switch_layout(get_layout_display(LayoutMode.COCKPIT.value))
        self.cockpit_view.on_select_case_from_list(case)

    def apply_windows_theme(self, dark: bool):
        if sys.platform.startswith("win"):
            try:
                self.update_idletasks()
                wid = self.winfo_id()
                if not wid:
                    return
                hwnd = ctypes.windll.user32.GetParent(wid)
                if not hwnd:
                    hwnd = wid
                if hwnd:
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
                    value = ctypes.c_int(1 if dark else 0)
                    if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value)
                    ) != 0:
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ctypes.byref(value), ctypes.sizeof(value)
                        )
            except Exception:
                pass

    def _maximize_window(self):
        try:
            self.state("zoomed")
        except Exception as e:
            logger.warning(f"Could not maximize window: {e}")

    _ensure_maximized = _maximize_window

    def toggle_theme(self):
        curr = ctk.get_appearance_mode()
        new_theme = "Light" if curr == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self.apply_windows_theme(new_theme == "Dark")
        self.profile.ui_settings.theme = new_theme
        if hasattr(self, "cockpit_view"):
            self.cockpit_view.update_sash_color()
        self.refresh_views()

    def register_shortcuts(self):
        shortcuts = self.profile.shortcuts
        import tkinter as tk

        def safe_bind(key_str: str, func):
            if not key_str or not key_str.strip():
                return
            try:
                tk.Misc.bind_all(self, key_str.strip(), func)
            except Exception as e:
                logger.warning(f"Failed to bind shortcut '{key_str}': {e}")

        # App Actions Shortcuts
        safe_bind(shortcuts.new_case, lambda e: self.open_new_case_dialog())
        safe_bind(shortcuts.export_dialog, lambda e: self.open_export_dialog(self.active_case))
        safe_bind(shortcuts.wiki_search, lambda e: self.cockpit_view.focus_wiki_search() if hasattr(self, "cockpit_view") else None)
        safe_bind(shortcuts.save_case, lambda e: self.cockpit_view.on_click_save() if hasattr(self, "cockpit_view") else None)
        safe_bind(shortcuts.search_customer, lambda e: self.cockpit_view.focus_customer_search() if hasattr(self, "cockpit_view") else None)
        safe_bind(shortcuts.archive_case, lambda e: self.on_archive_current_case())
        safe_bind(shortcuts.open_settings, lambda e: self.open_profile_settings_dialog())
        safe_bind(shortcuts.snippet_picker, lambda e: self.trigger_snippet_picker())
        safe_bind(shortcuts.view_cockpit, lambda e: self.switch_layout(LayoutMode.COCKPIT.value))
        safe_bind(shortcuts.view_board, lambda e: self.switch_layout(LayoutMode.BOARD.value))
        safe_bind(shortcuts.view_table, lambda e: self.switch_layout(LayoutMode.TABLE.value))
        safe_bind(getattr(shortcuts, "view_analytics", "<Control-4>"), lambda e: self.switch_layout(LayoutMode.ANALYTICS.value))
        safe_bind(shortcuts.toggle_theme, lambda e: self.toggle_theme())
        safe_bind("<F1>", lambda e: self.open_help_dialog())

        # Text Snippet Macro Shortcuts
        if hasattr(self, "snippet_service"):
            for snip in self.snippet_service.get_all_snippets():
                if snip.shortcut and snip.shortcut.strip():
                    safe_bind(snip.shortcut, lambda e, content=snip.content: self.insert_snippet_shortcut(content))

    def on_archive_current_case(self):
        if self.active_case:
            self.on_archive_case(self.active_case)
        elif hasattr(self, "cockpit_view") and self.cockpit_view.current_case:
            self.on_archive_case(self.cockpit_view.current_case)

    def trigger_snippet_picker(self):
        focused = self.focus_get()
        def on_selected(text: str):
            if focused:
                self._insert_text_into_widget(focused, text)
        self.open_snippet_picker_dialog(on_selected)

    def insert_snippet_shortcut(self, text: str):
        focused = self.focus_get()
        if focused and self._insert_text_into_widget(focused, text):
            return "break"
        else:
            ToastNotification(self, title=TOAST_SNIPPET_MACRO_TITLE, message=TOAST_SNIPPET_NO_FOCUS)

    def _insert_text_into_widget(self, widget, text: str) -> bool:
        if not widget or not text:
            return False
        try:
            target = widget
            if hasattr(target, "_entry"):
                target = target._entry
            elif hasattr(target, "_textbox"):
                target = target._textbox

            import tkinter as tk
            if isinstance(target, (tk.Entry, ctk.CTkEntry)):
                target.insert(tk.INSERT, text)
                return True
            elif isinstance(target, (tk.Text, ctk.CTkTextbox)):
                target.insert(tk.INSERT, text)
                return True
        except Exception as e:
            logger.warning(f"Error inserting snippet text: {e}")
        return False

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
            title=tr("app.zip_backup_title", "Komplett-Datensicherung als ZIP speichern"),
            defaultextension=".zip",
            filetypes=[(tr("app.zip_filetypes", "ZIP-Archiv"), "*.zip")],
            initialfile="SupportCockpit_Backup.zip",
            parent=self,
        )
        if dest_file:
            res = ZipBackupService.export_backup_zip(self.storage_service, Path(dest_file))
            mb_size = res["total_bytes"] / (1024 * 1024)
            print(f"✅ ZIP-Backup exportiert: {res['file_count']} Dateien ({mb_size:.2f} MB)")

    def get_all_active_cases_for_reminder(self) -> list[Case]:
        all_cases: list[Case]
        get_filtered = getattr(self, "get_filtered_cases", None)
        if callable(get_filtered):
            res = get_filtered()
            all_cases = cast(list[Case], res) if isinstance(res, list) else []
        else:
            user_cases = [c for c in self.cases if not getattr(c, "is_demo_data", False)]
            has_user_cases = len(user_cases) > 0

            show_demo = None
            prof = getattr(self, "profile", None)
            if prof and hasattr(prof, "ui_settings"):
                show_demo = getattr(prof.ui_settings, "show_demo_data", None)

            if show_demo is None:
                show_demo = not has_user_cases

            all_cases = self.cases if show_demo else user_cases
        return [c for c in all_cases if not c.workflow_status.is_completed]


    def check_due_followups(self):
        from utils.datetime_utils import parse_followup_datetime, get_local_now
        now = get_local_now()
        due_cases = []

        for c in self.get_all_active_cases_for_reminder():
            if c.workflow_status.followup_at:
                dt = parse_followup_datetime(c.workflow_status.followup_at)
                if dt and dt <= now:
                    due_cases.append(c)

        due_count = len(due_cases)
        if due_count > 0:
            self.bell_btn.configure(text=f"🔔 {due_count}", fg_color="darkred")
            last_count = getattr(self, "_last_notified_due_count", None)
            if last_count is None or due_count > last_count:
                top_case = due_cases[0]
                if self.__dict__.get("tk") is not None:
                    try:
                        ToastNotification(
                            self,
                            title=tr("app.followup_due_toast_title", "🔔 Wiedervorlage fällig ({count})", count=due_count),
                            message=f"[{top_case.case_id}] {top_case.classification.title}",
                            on_open=lambda c=top_case: self.switch_to_cockpit_view_for_case(c),
                        )
                    except Exception as e:
                        logger.warning(f"Could not display toast notification: {e}")
            self._last_notified_due_count = due_count
        else:
            self.bell_btn.configure(text="🔔 0", fg_color="gray30")
            self._last_notified_due_count = 0

        # Update tray icon badge (guard: may be called before tray_service is initialized)
        if hasattr(self, "tray_service"):
            self.tray_service.update_badge(due_count)

        _timer_id = self.__dict__.get("_followup_timer_id")
        if _timer_id:
            try:
                self.after_cancel(_timer_id)
            except Exception:
                pass
        self._followup_timer_id = self.after(60000, self.check_due_followups)

    def open_followup_flyout(self):
        from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
        from utils.datetime_utils import parse_followup_datetime, get_local_now
        now = get_local_now()
        due_cases = []

        for c in self.get_all_active_cases_for_reminder():
            if c.workflow_status.followup_at:
                dt = parse_followup_datetime(c.workflow_status.followup_at)
                if dt and dt <= now:
                    due_cases.append(c)

        def on_refresh():
            self.storage_service.save_cases(self.cases)
            self.refresh_views()
            self.check_due_followups()

        FollowupFlyoutDialog(self, due_cases, on_case_selected=self.on_case_selected, on_refresh=on_refresh)

    def on_closing(self):
        """Minimize to system tray instead of closing the application."""
        logger.info("Minimizing to system tray...")
        if hasattr(self, "cockpit_view"):
            self.cockpit_view.save_sash_widths()
        self.storage_service.save_profile(self.profile)
        self.storage_service.flush_all_saves()
        self.withdraw()

    def _on_restore_from_tray(self):
        """Restore the application window from the system tray."""
        self.bring_to_foreground()
        if hasattr(self, "_pending_notification_callback") and self._pending_notification_callback:
            cb = self._pending_notification_callback
            self._pending_notification_callback = None
            try:
                cb()
            except Exception as e:
                logger.warning(f"Error executing pending notification callback: {e}")

    def _on_quit_from_tray(self):
        """Fully quit the application from the system tray context menu."""
        def _quit():
            if hasattr(self, "cockpit_view"):
                self.cockpit_view.save_sash_widths()
            self.storage_service.save_profile(self.profile)
            self.storage_service.flush_all_saves()
            self.tray_service.stop()
            self.destroy()
        self.after(0, _quit)

    def on_quit_app(self):
        """Fully quit the application via the in-app Beenden button."""
        logger.info("Quitting application...")
        if hasattr(self, "cockpit_view"):
            self.cockpit_view.save_sash_widths()
        self.storage_service.save_profile(self.profile)
        self.storage_service.flush_all_saves()
        self.tray_service.stop()
        self.destroy()

    def destroy(self):
        from services.i18n_service import get_i18n
        try:
            get_i18n().unregister_listener(self.on_language_changed)
        except Exception:
            pass
        super().destroy()
