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
from constants import COLOR_SASH_DARK, COLOR_SASH_LIGHT


import logging
import tkinter as tk

logger = logging.getLogger("SupportCockpit")


class CockpitView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        author_name: str,
        scoring_service: ScoringService,
        attachment_service: AttachmentService,
        wiki_service: WikiSyncService,
        on_case_updated: Callable[[Case], None] | None = None,
        on_case_selected: Callable[[Case], None] | None = None,
        on_search_changed: Callable[[str], None] | None = None,
        on_open_export_dialog: Callable[[Case], None] | None = None,
        on_archive_case: Callable[[Case], None] | None = None,
        app_config: Any | None = None,
        profile: UserProfile | None = None,
        storage_service: StorageService | None = None,
        on_manage_module_tags: Callable[[], None] | None = None,
        on_open_email_calendar: Callable[[Case], None] | None = None,
        on_open_email: Callable[[Case | None], None] | None = None,
        on_open_calendar: Callable[[Case], None] | None = None,
        on_open_snippet_picker: Callable[[Any], None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.author_name = author_name
        self.scoring_service = scoring_service
        self.attachment_service = attachment_service
        self.wiki_service = wiki_service
        self.on_case_updated: Callable[[Case], None] = on_case_updated if on_case_updated is not None else (lambda c: None)
        self.on_case_selected: Callable[[Case], None] = on_case_selected if on_case_selected is not None else (lambda c: None)
        self.on_search_changed: Callable[[str], None] = on_search_changed if on_search_changed is not None else (lambda s: None)
        self.on_open_export_dialog: Callable[[Case], None] = on_open_export_dialog if on_open_export_dialog is not None else (lambda c: None)
        self.on_archive_case: Callable[[Case], None] = on_archive_case if on_archive_case is not None else (lambda c: None)
        self.app_config = app_config
        self.profile = profile
        self.storage_service = storage_service
        self.on_manage_module_tags = on_manage_module_tags
        self.on_open_email_calendar = on_open_email_calendar
        self.on_open_email = on_open_email
        self.on_open_calendar = on_open_calendar
        self.on_open_snippet_picker = on_open_snippet_picker

        self.current_case: Case | None = None
        self.schemas: list[QuestionSchema] = []

        self.create_layout()

    def apply_column_widths(self, widths: dict[str, int]):
        w_left = widths.get("cockpit_left", 300)
        w_right = widths.get("cockpit_right", 320)
        if hasattr(self, "paned"):
            try:
                self.paned.paneconfigure(self.left_frame, width=w_left)
                self.paned.paneconfigure(self.right_tabview, width=w_right)
                total_w = self.paned.winfo_width()
                if total_w > 100:
                    self.paned.sash_place(0, w_left, 0)
                    self.paned.sash_place(1, max(w_left + 150, total_w - w_right), 0)
            except Exception:
                pass

    def restore_sash_positions(self):
        try:
            if not hasattr(self, "paned") or not self.paned.winfo_exists():
                return
            total_w = self.paned.winfo_width()
            if total_w <= 100:
                self.after(100, self.restore_sash_positions)
                return

            widths = {}
            if self.profile and hasattr(self.profile, "ui_settings") and hasattr(self.profile.ui_settings, "column_widths"):
                widths = self.profile.ui_settings.column_widths
            elif self.app_config and hasattr(self.app_config, "column_widths"):
                widths = self.app_config.column_widths

            w_left = widths.get("cockpit_left", 300)
            w_right = widths.get("cockpit_right", 320)

            self.paned.sash_place(0, w_left, 0)
            self.paned.sash_place(1, max(w_left + 150, total_w - w_right), 0)
        except Exception as e:
            logger.warning(f"Could not restore sash positions: {e}")

    def on_paned_sash_released(self, event=None):
        self.save_sash_widths()

    def save_sash_widths(self):
        try:
            if not hasattr(self, "paned") or not self.paned.winfo_exists():
                return
            total_w = self.paned.winfo_width()
            if total_w <= 100:
                return

            sash0 = self.paned.sash_coord(0)
            sash1 = self.paned.sash_coord(1)

            if sash0 and len(sash0) > 0 and sash0[0] > 0:
                w_left = max(100, sash0[0])
                if self.profile and hasattr(self.profile, "ui_settings"):
                    self.profile.ui_settings.column_widths["cockpit_left"] = w_left

            if sash1 and len(sash1) > 0 and sash1[0] > 0:
                w_right = max(100, total_w - sash1[0])
                if self.profile and hasattr(self.profile, "ui_settings"):
                    self.profile.ui_settings.column_widths["cockpit_right"] = w_right

            if self.profile and self.storage_service:
                self.storage_service.save_profile(self.profile)
        except Exception as e:
            logger.warning(f"Could not save paned sash positions: {e}")

    def update_sash_color(self):
        if hasattr(self, "paned") and self.paned.winfo_exists():
            is_dark = ctk.get_appearance_mode() == "Dark"
            sash_bg = COLOR_SASH_DARK if is_dark else COLOR_SASH_LIGHT
            try:
                self.paned.configure(bg=sash_bg)
            except Exception:
                pass

    def create_layout(self):
        widths = {}
        if self.profile and hasattr(self.profile, "ui_settings") and hasattr(self.profile.ui_settings, "column_widths"):
            widths = self.profile.ui_settings.column_widths
        elif self.app_config and hasattr(self.app_config, "column_widths"):
            widths = self.app_config.column_widths

        w_left = widths.get("cockpit_left", 300)
        w_right = widths.get("cockpit_right", 320)

        is_dark = ctk.get_appearance_mode() == "Dark"
        sash_bg = COLOR_SASH_DARK if is_dark else COLOR_SASH_LIGHT

        # Native PanedWindow for 100% reliable 60fps drag resizing
        self.paned = tk.PanedWindow(
            self,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            sashpad=1,
            bg=sash_bg,
            bd=0,
            relief="flat",
            handlesize=0,
            showhandle=False,
        )
        self.paned.pack(fill="both", expand=True, padx=2, pady=2)
        self.paned.bind("<ButtonRelease-1>", self.on_paned_sash_released)

        # 1. Left Pane: Case List
        self.left_frame = CaseListWidget(
            self.paned,
            on_case_selected=self.on_select_case_from_list,
            on_search_changed=self.on_search_changed,
            on_toggle_deep_search=lambda active: self.on_search_changed(self.left_frame.search_entry.get()),
        )

        # 2. Center Pane: Case Details & Dynamic Form
        self.center_frame = ctk.CTkFrame(self.paned)

        # Center Header Controls
        self.center_header = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.center_header.pack(fill="x", padx=10, pady=10)

        self.case_title_label = ctk.CTkLabel(
            self.center_header, text="Bitte einen Fall auswählen", font=ctk.CTkFont(size=16, weight="bold"), anchor="w"
        )
        self.case_title_label.pack(side="left", fill="x", expand=True)

        self.print_btn = ctk.CTkButton(
            self.center_header, text="🖨 Drucken", command=self.on_click_print, width=85, state="disabled", fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")
        )
        self.print_btn.pack(side="right", padx=2)

        self.cal_btn = ctk.CTkButton(
            self.center_header, text="📅 Kalender", command=self.on_click_calendar, width=88, state="disabled", fg_color="forestgreen", hover_color="darkgreen"
        )
        self.cal_btn.pack(side="right", padx=2)

        self.email_btn = ctk.CTkButton(
            self.center_header, text="✉ E-Mail & 🤖 KI", command=self.on_click_email, width=140, state="disabled", fg_color="#6366f1", hover_color="#4f46e5"
        )
        self.email_btn.pack(side="right", padx=2)

        self.export_btn = ctk.CTkButton(
            self.center_header, text="📤 Export", command=self.on_click_export, width=80, state="disabled"
        )
        self.export_btn.pack(side="right", padx=2)

        self.save_btn = ctk.CTkButton(
            self.center_header, text="💾 Speichern", command=self.on_click_save, width=85, state="disabled"
        )
        self.save_btn.pack(side="right", padx=2)

        # Customer & Status Info Bar (3 vertical info lines on left + action buttons on right)
        self.info_bar = ctk.CTkFrame(self.center_frame, fg_color=("gray85", "gray20"), corner_radius=6)
        self.info_bar.pack(fill="x", padx=10, pady=(0, 10))

        # Left Column: 3 vertical stacked lines for customer details
        self.info_left_frame = ctk.CTkFrame(self.info_bar, fg_color="transparent")
        self.info_left_frame.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        self.kunde_label = ctk.CTkLabel(self.info_left_frame, text="", font=ctk.CTkFont(size=12, weight="bold"), anchor="w", height=0)
        self.kunde_label.pack(fill="x", anchor="w")

        self.ansprechpartner_label = ctk.CTkLabel(self.info_left_frame, text="", font=ctk.CTkFont(size=11), anchor="w", height=0)

        # Multi-line Wiedervorlage container in Cockpit Center Pane
        self.wiedervorlage_frame = ctk.CTkFrame(self.info_left_frame, fg_color="transparent")

        self.wv_hdr_label = ctk.CTkLabel(
            self.wiedervorlage_frame,
            text="🔔 Nachfragen am:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="darkorange",
            anchor="w",
            justify="left",
            height=0,
        )
        self.wv_date_label = ctk.CTkLabel(
            self.wiedervorlage_frame,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="darkorange",
            anchor="w",
            justify="left",
            height=0,
        )
        self.wv_time_label = ctk.CTkLabel(
            self.wiedervorlage_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="darkorange",
            anchor="w",
            justify="left",
            height=0,
        )
        self.wv_note_label = ctk.CTkLabel(
            self.wiedervorlage_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="darkorange",
            anchor="w",
            justify="left",
            height=0,
        )
        self.wiedervorlage_label = self.wv_hdr_label

        # Full untruncated follow-up text & hover tooltip overlay
        self._wiedervorlage_full_text: str = ""
        self._wiedervorlage_is_truncated: bool = False
        from ui.widgets.ctk_tooltip import CTkTooltip
        self.wiedervorlage_tooltip = CTkTooltip(
            self.wiedervorlage_frame,
            self._get_wiedervorlage_tooltip_text,
            delay_ms=250,
        )
        for _lbl in (self.wv_hdr_label, self.wv_date_label, self.wv_time_label, self.wv_note_label):
            CTkTooltip(_lbl, self._get_wiedervorlage_tooltip_text, delay_ms=250)

        self.info_left_frame.bind("<Configure>", self._on_info_frame_configure, add="+")

        # Right Column: Action Buttons Container
        self.info_right_frame = ctk.CTkFrame(self.info_bar, fg_color="transparent")
        self.info_right_frame.pack(side="right", padx=6, pady=6)

        # Row 1 of right buttons
        self.info_btn_row1 = ctk.CTkFrame(self.info_right_frame, fg_color="transparent")
        self.info_btn_row1.pack(fill="x", anchor="e", pady=(0, 2))

        self.archive_btn = ctk.CTkButton(self.info_btn_row1, text="📦 Archivieren", command=self.on_click_archive, width=90, fg_color="darkred")
        self.archive_btn.pack(side="right", padx=2)

        self.complete_btn = ctk.CTkButton(self.info_btn_row1, text="✓ Erledigt", command=self.on_toggle_complete, width=85, fg_color="green")
        self.complete_btn.pack(side="right", padx=2)

        self.actor_combo = ctk.CTkOptionMenu(self.info_btn_row1, values=list(ACTOR_DISPLAY.values()), command=self.on_actor_changed, width=120)
        self.actor_combo.pack(side="right", padx=2)

        # Row 2 of right buttons
        self.info_btn_row2 = ctk.CTkFrame(self.info_right_frame, fg_color="transparent")
        self.info_btn_row2.pack(fill="x", anchor="e", pady=(2, 0))

        self.convert_schema_btn = ctk.CTkButton(self.info_btn_row2, text="🔄 Formular umwandeln", command=self.open_convert_schema_dialog, width=140, fg_color="#2563eb", hover_color="#1d4ed8", state="disabled")
        self.convert_schema_btn.pack(side="right", padx=2)

        self.add_note_btn = ctk.CTkButton(self.info_btn_row2, text="📝 Notiz", command=self.focus_timeline_note, width=75, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"))
        self.add_note_btn.pack(side="right", padx=2)

        self.followup_btn = ctk.CTkButton(self.info_btn_row2, text="🔔 Wiedervorlage", command=self.open_followup_dialog, width=110, fg_color="darkblue")
        self.followup_btn.pack(side="right", padx=2)

        # Dynamic Form Widget
        self.form_widget = DynamicFormWidget(
            self.center_frame,
            profile=self.profile,
            storage_service=self.storage_service,
            attachment_service=self.attachment_service,
            on_manage_module_tags=self.on_manage_module_tags,
        )
        self.form_widget.pack(fill="both", expand=True, padx=5, pady=5)

        # 3. Right Pane: Tabbed Sidebar
        self.right_tabview = ctk.CTkTabview(self.paned)

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

        # Add all 3 panes to native PanedWindow container
        self.paned.add(self.left_frame, minsize=120, width=w_left)
        self.paned.add(self.center_frame, minsize=150)
        self.paned.add(self.right_tabview, minsize=120, width=w_right)

        self.after(100, self.restore_sash_positions)
        self.after(500, self.restore_sash_positions)

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
            CasePrintDialog(self, self.current_case, attachment_service=self.attachment_service)

    def on_click_email(self):
        if self.on_open_email:
            self.on_open_email(self.current_case)
        elif self.on_open_email_calendar and self.current_case:
            self.on_open_email_calendar(self.current_case)
        else:
            from ui.dialogs.email_draft_dialog import EmailDraftDialog
            from services.calendar_email_service import CalendarEmailService
            svc = CalendarEmailService(self.app_config)
            EmailDraftDialog(
                self,
                case=self.current_case,
                calendar_email_service=svc,
                user_name=self.author_name,
                storage_service=self.storage_service,
            )

    def on_click_ai(self):
        if not self.current_case:
            return
        from ui.dialogs.ai_assistant_dialog import AiAssistantDialog
        wiki_articles = []
        if self.storage_service:
            try:
                from services.wiki_sync_service import WikiSyncService
                wiki_svc = WikiSyncService(self.storage_service.config)
                wiki_articles = wiki_svc.get_all_pages()
            except Exception:
                pass

        AiAssistantDialog(
            self.winfo_toplevel(),
            case=self.current_case,
            profile=self.profile,
            on_case_updated=self.on_case_updated,
            on_open_email_draft=lambda _c=None: self.on_click_email(),
            wiki_articles=wiki_articles,
        )

    def on_click_calendar(self):
        if self.current_case:
            if self.on_open_calendar:
                self.on_open_calendar(self.current_case)
            elif self.on_open_email_calendar:
                self.on_open_email_calendar(self.current_case)
            else:
                from ui.dialogs.calendar_export_dialog import CalendarExportDialog
                from services.calendar_email_service import CalendarEmailService
                svc = CalendarEmailService(self.app_config)
                CalendarExportDialog(self, self.current_case, calendar_email_service=svc)

    def on_click_email_calendar(self):
        self.on_click_email()

    def on_select_case_from_list(self, case: Case):
        self.current_case = case

        self.case_title_label.configure(text=f"{case.case_id}: {case.classification.title}")
        self.print_btn.configure(state="normal")
        self.email_btn.configure(state="normal")
        self.cal_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.convert_schema_btn.configure(state="normal")

        from utils.datetime_utils import format_german_datetime
        vip_str = " ★ VIP" if case.customer.is_vip else ""
        if case.is_internal:
            self.kunde_label.configure(text=f"🏢 Kunde: INTERNE AUFGABE / VORGANG ({case.customer.customer_id}){vip_str}")
        else:
            self.kunde_label.configure(text=f"🏥 Kunde: {case.customer.practice_name} ({case.customer.customer_id}){vip_str}")

        self.ansprechpartner_label.configure(text=f"👤 Ansprechpartner: {case.customer.contact_person}")

        self._update_wiedervorlage_display()

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

    _last_info_w: int = 0
    _updating_info: bool = False

    def _on_info_frame_configure(self, event=None):
        if self._updating_info:
            return
        if not self.current_case or not self.current_case.workflow_status.followup_at:
            return
        try:
            if not self.info_left_frame.winfo_exists():
                return
            w = self.info_left_frame.winfo_width()
            if w > 50 and abs(w - self._last_info_w) > 8:
                self._last_info_w = w
                self._updating_info = True
                wrap_w = max(180, w - 10)
                self.wv_hdr_label.configure(wraplength=wrap_w)
                self.wv_date_label.configure(wraplength=wrap_w)
                self.wv_time_label.configure(wraplength=wrap_w)
                self.wv_note_label.configure(wraplength=wrap_w)
        except Exception:
            pass
        finally:
            self._updating_info = False

    def _get_wiedervorlage_tooltip_text(self) -> str:
        if self._wiedervorlage_full_text:
            return self._wiedervorlage_full_text
        return ""

    def _update_wiedervorlage_display(self):
        if not self.current_case or not self.current_case.workflow_status.followup_at:
            self._wiedervorlage_full_text = ""
            self._wiedervorlage_is_truncated = False
            self.wv_hdr_label.configure(text="")
            self.wv_date_label.configure(text="")
            self.wv_time_label.configure(text="")
            self.wv_note_label.configure(text="")
            self.wiedervorlage_frame.pack_forget()
            return

        from utils.datetime_utils import format_german_date_with_relative, format_german_time, format_german_datetime

        fw_date_str = format_german_date_with_relative(self.current_case.workflow_status.followup_at)
        fw_time_str = format_german_time(self.current_case.workflow_status.followup_at, with_uhr=True)
        note = self.current_case.workflow_status.followup_note or ""

        fw_dt_str = format_german_datetime(self.current_case.workflow_status.followup_at)
        note_suffix = f" ({note})" if note else ""
        self._wiedervorlage_full_text = f"🔔 Nachfragen am: {fw_date_str}, {fw_time_str}{note_suffix}"

        # Compute available pixel width in info_left_frame
        w = self.info_left_frame.winfo_width()
        if w <= 50:
            bar_w = self.info_bar.winfo_width()
            right_w = self.info_right_frame.winfo_reqwidth()
            w = max(250, (bar_w - right_w - 30) if bar_w > right_w + 50 else 380)
        else:
            w = max(200, w - 10)

        self._last_info_w = w
        self.wv_hdr_label.configure(text="🔔 Nachfragen am:", wraplength=w)
        self.wv_date_label.configure(text=f"  {fw_date_str}", wraplength=w)
        self.wv_time_label.configure(text=f"  {fw_time_str}", wraplength=w)

        self.wv_hdr_label.pack(fill="x", anchor="w", pady=0)
        self.wv_date_label.pack(fill="x", anchor="w", pady=0)
        self.wv_time_label.pack(fill="x", anchor="w", pady=0)

        if note:
            self.wv_note_label.configure(text=f"  {note}", wraplength=w)
            self.wv_note_label.pack(fill="x", anchor="w", pady=0)
        else:
            self.wv_note_label.pack_forget()

        self.wiedervorlage_frame.pack(fill="x", anchor="w", pady=(2, 0))

    def focus_wiki_search(self):
        if hasattr(self, "wiki_widget") and hasattr(self.wiki_widget, "search_entry"):
            self.wiki_widget.search_entry.focus()
            self.wiki_widget.search_entry.select_range(0, "end")

    def focus_customer_search(self):
        if hasattr(self, "left_frame") and hasattr(self.left_frame, "search_entry"):
            self.left_frame.search_entry.focus()
            self.left_frame.search_entry.select_range(0, "end")

