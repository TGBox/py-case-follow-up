import customtkinter as ctk
from typing import Callable, Any
from models.case import Case, TimelineEntry
from models.customer import Customer
from models.schema import QuestionSchema
from enums import BoardColumn, Actor, get_actor_display, get_actor_val_from_display, ACTOR_DISPLAY
from models.profile import UserProfile
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from services.schema_service import SchemaService

from ui.widgets.case_list_widget import CaseListWidget
from ui.widgets.dynamic_form_widget import DynamicFormWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.attachment_widget import AttachmentWidget
from ui.widgets.wiki_widget import WikiWidget


class CockpitColumnSplitter(ctk.CTkFrame):
    """Interactive vertical splitter bar to drag and resize Cockpit sidebars."""

    def __init__(
        self,
        parent,
        column_key: str,
        profile: UserProfile | None,
        storage_service: StorageService | None,
        on_width_changed: Callable[[str, int], None] | None = None,
    ):
        super().__init__(parent, fg_color=("gray75", "gray35"), width=5, cursor="sb_h_double_arrow")
        self.column_key = column_key
        self.profile = profile
        self.storage_service = storage_service
        self.on_width_changed = on_width_changed
        self.start_x = 0
        self.start_width = 300

        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x = event.x_root
        if self.profile and hasattr(self.profile, "ui_settings") and hasattr(self.profile.ui_settings, "column_widths"):
            self.start_width = self.profile.ui_settings.column_widths.get(self.column_key, 300)
        else:
            self.start_width = 300

    def on_drag(self, event):
        delta = event.x_root - self.start_x
        if self.column_key == "cockpit_right":
            new_w = max(200, min(650, self.start_width - delta))
        else:
            new_w = max(180, min(600, self.start_width + delta))

        if self.profile and hasattr(self.profile, "ui_settings"):
            self.profile.ui_settings.column_widths[self.column_key] = new_w

        if self.on_width_changed:
            self.on_width_changed(self.column_key, new_w)

    def on_release(self, event):
        if self.profile and self.storage_service:
            self.storage_service.save_profile(self.profile)


class CockpitView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        author_name: str,
        scoring_service: ScoringService,
        attachment_service: AttachmentService,
        wiki_service: WikiSyncService,
        on_case_updated: Callable[[Case], None],
        on_case_selected: Callable[[Case], None],
        on_search_changed: Callable[[str], None],
        on_open_export_dialog: Callable[[Case], None],
        on_archive_case: Callable[[Case], None],
        app_config: Any | None = None,
        profile: UserProfile | None = None,
        storage_service: StorageService | None = None,
        on_manage_module_tags: Callable[[], None] | None = None,
        on_open_email_calendar: Callable[[Case], None] | None = None,
        on_open_snippet_picker: Callable[[Callable[[str], None]], None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.author_name = author_name
        self.scoring_service = scoring_service
        self.attachment_service = attachment_service
        self.wiki_service = wiki_service
        self.on_case_updated = on_case_updated
        self.on_case_selected = on_case_selected
        self.on_search_changed = on_search_changed
        self.on_open_export_dialog = on_open_export_dialog
        self.on_archive_case = on_archive_case
        self.app_config = app_config
        self.profile = profile
        self.storage_service = storage_service
        self.on_manage_module_tags = on_manage_module_tags
        self.on_open_email_calendar = on_open_email_calendar
        self.on_open_snippet_picker = on_open_snippet_picker

        self.current_case: Case | None = None
        self.schemas: list[QuestionSchema] = []

        self.create_layout()

    def apply_column_widths(self, widths: dict[str, int]):
        w_left = widths.get("cockpit_left", 300)
        w_center = widths.get("cockpit_center", 420)
        w_right = widths.get("cockpit_right", 320)
        self.grid_columnconfigure(0, weight=w_left, minsize=180)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=w_center, minsize=260)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=w_right, minsize=200)

    def on_splitter_width_changed(self, column_key: str, new_width: int):
        if column_key == "cockpit_left":
            self.grid_columnconfigure(0, weight=new_width)
        elif column_key == "cockpit_right":
            self.grid_columnconfigure(4, weight=new_width)

    def create_layout(self):
        # 5-Column Layout with splitters (Col 0: Left, Col 1: Splitter L, Col 2: Center, Col 3: Splitter R, Col 4: Right)
        widths = {}
        if self.profile and hasattr(self.profile, "ui_settings") and hasattr(self.profile.ui_settings, "column_widths"):
            widths = self.profile.ui_settings.column_widths
        elif self.app_config and hasattr(self.app_config, "column_widths"):
            widths = self.app_config.column_widths

        w_left = widths.get("cockpit_left", 300)
        w_center = widths.get("cockpit_center", 420)
        w_right = widths.get("cockpit_right", 320)

        self.grid_columnconfigure(0, weight=w_left, minsize=180)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=w_center, minsize=260)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=w_right, minsize=200)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Column: Case List
        self.left_frame = CaseListWidget(
            self,
            on_case_selected=self.on_select_case_from_list,
            on_search_changed=self.on_search_changed,
            on_toggle_deep_search=lambda active: self.on_search_changed(self.left_frame.search_entry.get()),
        )
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 1), pady=5)

        # Splitter 1: Left / Center
        self.splitter_left = CockpitColumnSplitter(
            self,
            column_key="cockpit_left",
            profile=self.profile,
            storage_service=self.storage_service,
            on_width_changed=self.on_splitter_width_changed,
        )
        self.splitter_left.grid(row=0, column=1, sticky="ns", padx=1, pady=5)

        # 2. Center Column: Case Details & Dynamic Form
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.grid(row=0, column=2, sticky="nsew", padx=1, pady=5)

        # Center Header Controls
        self.center_header = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.center_header.pack(fill="x", padx=10, pady=10)

        self.case_title_label = ctk.CTkLabel(
            self.center_header, text="Bitte einen Fall auswählen", font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.case_title_label.pack(side="left", fill="x", expand=True)

        self.print_btn = ctk.CTkButton(
            self.center_header, text="🖨️ Drucken", command=self.on_click_print, width=100, state="disabled", fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")
        )
        self.print_btn.pack(side="right", padx=5)

        self.email_cal_btn = ctk.CTkButton(
            self.center_header, text="✉️ E-Mail / Kalender", command=self.on_click_email_calendar, width=145, state="disabled", fg_color="forestgreen", hover_color="darkgreen"
        )
        self.email_cal_btn.pack(side="right", padx=5)

        self.export_btn = ctk.CTkButton(
            self.center_header, text="📤 Export", command=self.on_click_export, width=100, state="disabled"
        )
        self.export_btn.pack(side="right", padx=5)

        self.save_btn = ctk.CTkButton(
            self.center_header, text="💾 Speichern", command=self.on_click_save, width=100, state="disabled"
        )
        self.save_btn.pack(side="right", padx=5)

        # Customer & Status Info Bar
        self.info_bar = ctk.CTkFrame(self.center_frame, fg_color=("gray85", "gray20"), corner_radius=6)
        self.info_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.info_label = ctk.CTkLabel(self.info_bar, text="", font=ctk.CTkFont(size=12), anchor="w")
        self.info_label.pack(side="left", padx=10, pady=6)

        # Actor Selector, Followup & Action Buttons
        self.actor_combo = ctk.CTkOptionMenu(
            self.info_bar,
            values=list(ACTOR_DISPLAY.values()),
            command=self.on_actor_changed,
            width=130,
        )
        self.actor_combo.pack(side="right", padx=5, pady=4)

        self.convert_schema_btn = ctk.CTkButton(
            self.info_bar, text="🔄 Formular umwandeln...", command=self.open_convert_schema_dialog, width=150, fg_color="#2563eb", hover_color="#1d4ed8", state="disabled"
        )
        self.convert_schema_btn.pack(side="right", padx=5, pady=4)

        self.add_note_btn = ctk.CTkButton(
            self.info_bar, text="📝 Notiz / Ereignis", command=self.focus_timeline_note, width=120, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")
        )
        self.add_note_btn.pack(side="right", padx=5, pady=4)

        self.followup_btn = ctk.CTkButton(
            self.info_bar, text="🔔 Wiedervorlage", command=self.open_followup_dialog, width=120, fg_color="darkblue"
        )
        self.followup_btn.pack(side="right", padx=5, pady=4)

        self.complete_btn = ctk.CTkButton(
            self.info_bar, text="✓ Erledigt", command=self.on_toggle_complete, width=90, fg_color="green"
        )
        self.complete_btn.pack(side="right", padx=5, pady=4)

        self.archive_btn = ctk.CTkButton(
            self.info_bar, text="📦 Archivieren", command=self.on_click_archive, width=100, fg_color="darkred"
        )
        self.archive_btn.pack(side="right", padx=5, pady=4)

        # Dynamic Form
        self.form_widget = DynamicFormWidget(
            self.center_frame,
            profile=self.profile,
            storage_service=self.storage_service,
            attachment_service=self.attachment_service,
            on_manage_module_tags=self.on_manage_module_tags,
        )
        self.form_widget.pack(fill="both", expand=True, padx=5, pady=5)

        # Splitter 2: Center / Right
        self.splitter_right = CockpitColumnSplitter(
            self,
            column_key="cockpit_right",
            profile=self.profile,
            storage_service=self.storage_service,
            on_width_changed=self.on_splitter_width_changed,
        )
        self.splitter_right.grid(row=0, column=3, sticky="ns", padx=1, pady=5)

        # 3. Right Column: Tabbed Sidebar (Timeline, Attachments, Wiki)
        self.right_tabview = ctk.CTkTabview(self)
        self.right_tabview.grid(row=0, column=4, sticky="nsew", padx=(1, 5), pady=5)

        tab_timeline = self.right_tabview.add("Zeitleiste")
        tab_attachments = self.right_tabview.add("Anhänge")
        tab_wiki = self.right_tabview.add("Wiki")

        self.timeline_widget = TimelineWidget(
            tab_timeline,
            self.author_name,
            self.on_timeline_updated,
            on_open_snippet_picker=self.on_open_snippet_picker,
        )
        self.timeline_widget.pack(fill="both", expand=True)

        self.attachment_widget = AttachmentWidget(tab_attachments, self.attachment_service)
        self.attachment_widget.pack(fill="both", expand=True)

        self.wiki_widget = WikiWidget(tab_wiki, self.wiki_service)
        self.wiki_widget.pack(fill="both", expand=True)

    def set_cases(self, cases: list[Case], deep_results: dict[str, dict] | None = None):
        self.left_frame.set_cases(cases, deep_results=deep_results)

    def set_schemas(self, schemas: list[QuestionSchema]):
        self.schemas = schemas

    def focus_wiki_search(self):
        self.right_tabview.set("Wiki")
        self.wiki_widget.focus_search()

    def focus_timeline_note(self):
        self.right_tabview.set("Zeitleiste")
        self.timeline_widget.note_textbox.focus_set()

    def on_click_print(self):
        if self.current_case:
            from ui.dialogs.case_print_dialog import CasePrintDialog
            CasePrintDialog(self, self.current_case)

    def on_click_email_calendar(self):
        if self.current_case and self.on_open_email_calendar:
            self.on_open_email_calendar(self.current_case)

    def on_select_case_from_list(self, case: Case):
        self.current_case = case

        self.case_title_label.configure(text=f"{case.case_id}: {case.classification.title}")
        self.print_btn.configure(state="normal")
        self.email_cal_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.convert_schema_btn.configure(state="normal")

        from utils.datetime_utils import format_german_datetime
        vip_str = " ★ VIP" if case.customer.is_vip else ""
        fw_str = f" | 🔔 Wiedervorlage: {format_german_datetime(case.workflow_status.followup_at)}" if case.workflow_status.followup_at else ""
        info_str = f"Kunde: {case.customer.practice_name} ({case.customer.customer_id}){vip_str} | Ansprechpartner: {case.customer.contact_person}{fw_str}"
        self.info_label.configure(text=info_str)

        self.actor_combo.set(get_actor_display(case.workflow_status.current_actor))
        self.complete_btn.configure(text="✓ Wieder öffnen" if case.workflow_status.is_completed else "✓ Erledigen")

        # Load active schema
        schema = next((s for s in self.schemas if s.schema_id == case.classification.schema_id), None)
        if schema:
            SchemaService.update_case_completion(case, schema)
        self.form_widget.load_schema(schema, case.form_data, case.missing_required_fields, case=case)

        # Load right sidebar
        self.timeline_widget.load_timeline(case.timeline)
        self.attachment_widget.load_attachments(case)

    def open_convert_schema_dialog(self):
        if not self.current_case:
            return
        from ui.dialogs.convert_schema_dialog import ConvertSchemaDialog
        ConvertSchemaDialog(
            self,
            case=self.current_case,
            schemas=self.schemas,
            author_name=self.author_name,
            on_schema_converted=self.on_schema_converted,
        )

    def on_schema_converted(self, case: Case, new_schema: QuestionSchema):
        SchemaService.update_case_completion(case, new_schema)
        if self.scoring_service:
            self.scoring_service.update_case_scoring(case)
        self.on_select_case_from_list(case)
        if self.on_case_updated:
            self.on_case_updated(case)

    def on_click_save(self):
        if not self.current_case:
            return
        form_data = self.form_widget.get_form_data()
        self.current_case.form_data = form_data

        schema = next((s for s in self.schemas if s.schema_id == self.current_case.classification.schema_id), None)
        if schema:
            SchemaService.update_case_completion(self.current_case, schema)

        self.scoring_service.update_case_scoring(self.current_case)
        self.on_case_updated(self.current_case)

    def on_actor_changed(self, new_actor_display: str):
        if self.current_case:
            from ui.dialogs.handover_dialog import HandoverDialog
            from utils.datetime_utils import now_iso
            from models.case import TimelineEntry
            from enums import Channel, get_actor_display

            def on_confirmed(new_actor_val: str, channel: str, person: str, note: str):
                if self.current_case:
                    prev_actor_val = self.current_case.workflow_status.current_actor
                    self.current_case.workflow_status.current_actor = new_actor_val
                    self.current_case.workflow_status.actor_since = now_iso()

                    person_str = f" ({person})" if person else ""
                    note_str = f" | Details: {note}" if note else ""
                    note_text = f"Zuständigkeit übergeben an: {get_actor_display(new_actor_val)}{person_str} via {channel}{note_str}"
                    change_text = f"ZUSTÄNDIGKEIT: {get_actor_display(prev_actor_val)} -> {get_actor_display(new_actor_val)}"

                    entry = TimelineEntry(
                        timestamp=now_iso(),
                        author=self.author_name,
                        channel=Channel.INTERNAL_NOTE.value,
                        note=note_text,
                        status_change=change_text,
                    )
                    self.current_case.timeline.append(entry)
                    self.timeline_widget.load_timeline(self.current_case.timeline)

                    self.on_click_save()
                    self.open_followup_dialog()

            HandoverDialog(
                self,
                case=self.current_case,
                on_handover_confirmed=on_confirmed,
            )

    def open_followup_dialog(self):
        if not self.current_case:
            return
        from ui.dialogs.followup_dialog import FollowupDialog
        FollowupDialog(self, self.current_case, self.on_followup_set)

    def on_followup_set(self, followup_at: str, followup_note: str):
        if self.current_case:
            self.current_case.workflow_status.followup_at = followup_at
            self.current_case.workflow_status.followup_note = followup_note
            self.on_click_save()
            self.on_select_case_from_list(self.current_case)

    def on_toggle_complete(self):
        if self.current_case:
            self.current_case.workflow_status.is_completed = not self.current_case.workflow_status.is_completed
            self.complete_btn.configure(text="✓ Wieder öffnen" if self.current_case.workflow_status.is_completed else "✓ Erledigen")
            self.on_click_save()

    def on_click_archive(self):
        if self.current_case:
            self.on_archive_case(self.current_case)

    def on_click_export(self):
        if self.current_case:
            self.on_open_export_dialog(self.current_case)

    def on_timeline_updated(self, entries: list[TimelineEntry]):
        if self.current_case:
            self.current_case.timeline = entries
            self.on_click_save()
