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
from ui.views.cockpit_layout_builders import CockpitLayoutBuilderMixin


import logging
import tkinter as tk

logger = logging.getLogger("SupportCockpit")


class CockpitView(CockpitLayoutBuilderMixin, ctk.CTkFrame):
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
        self.on_manage_module_tags = on_manage_module_tags if on_manage_module_tags is not None else (lambda: None)
        self.on_open_email_calendar = on_open_email_calendar
        self.on_open_email = on_open_email
        self.on_open_calendar = on_open_calendar
        self.on_open_snippet_picker = on_open_snippet_picker if on_open_snippet_picker is not None else (lambda x=None: None)

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
        w_left, w_right = self._build_paned_window()

        self._build_left_pane()
        self._build_center_pane()
        self._build_right_pane()

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
        wiki_tab = getattr(self, "_sidebar_tab_names", {}).get("wiki", "Wiki")
        self.right_tabview.set(wiki_tab)
        self.wiki_widget.focus_search()

    def focus_timeline_note(self):
        tl_tab = getattr(self, "_sidebar_tab_names", {}).get("timeline", "Zeitleiste")
        self.right_tabview.set(tl_tab)
        self._on_sidebar_tab_changed(tl_tab)
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

    def _update_title_label(self):
        if not self.current_case:
            return
        from services.i18n_service import tr
        status_tag = f"  [{tr('cockpit.status_completed_tag', '✓ ERLEDIGT')}]" if self.current_case.workflow_status.is_completed else ""
        self.case_title_label.configure(text=f"{self.current_case.case_id}: {self.current_case.classification.title}{status_tag}")

    def on_select_case_from_list(self, case: Case):
        self.current_case = case

        self._update_title_label()
        self.print_btn.configure(state="normal")
        self.email_btn.configure(state="normal")
        self.cal_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.convert_schema_btn.configure(state="normal")

        from utils.datetime_utils import format_german_datetime
        from services.i18n_service import tr
        vip_str = " ★ VIP" if case.customer.is_vip else ""
        if case.is_internal:
            self.kunde_label.configure(text=f"🏢 {tr('cockpit.customer', 'Kunde')}: {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')} ({case.customer.customer_id}){vip_str}")
        else:
            self.kunde_label.configure(text=f"🏥 {tr('cockpit.customer', 'Kunde')}: {case.customer.practice_name} ({case.customer.customer_id}){vip_str}")

        full_addr = getattr(case.customer, "full_address", "")
        addr_str = f" | 🏠 {full_addr}" if full_addr else ""
        self.ansprechpartner_label.configure(text=f"👤 {tr('cockpit.contact_person', 'Ansprechpartner')}: {case.customer.contact_person}{addr_str}")

        self._update_wiedervorlage_display()

        self.actor_combo.set(get_actor_display(case.workflow_status.current_actor))
        self.complete_btn.configure(text=tr("cockpit.reopen", "✓ Wieder öffnen") if case.workflow_status.is_completed else tr("cockpit.complete", "✓ Erledigt"))

        # Reset sidebar loaded tabs cache for new case
        self._loaded_tab_case_ids.clear()

        # Load active schema
        schema = next((s for s in self.schemas if s.schema_id == case.classification.schema_id), None)
        if schema:
            SchemaService.update_case_completion(case, schema)
        self.form_widget.load_schema(schema, case.form_data, case.missing_required_fields, case=case)

        # Lazy load active sidebar tab content on-demand
        self._on_sidebar_tab_changed()

    def _on_sidebar_tab_changed(self, tab_name: str | None = None):
        if not self.current_case:
            return
        curr_tab = tab_name or self.right_tabview.get()
        if self._loaded_tab_case_ids.get(curr_tab) == self.current_case.case_id:
            return

        self._loaded_tab_case_ids[curr_tab] = self.current_case.case_id
        tl_tab = getattr(self, "_sidebar_tab_names", {}).get("timeline", "Zeitleiste")
        att_tab = getattr(self, "_sidebar_tab_names", {}).get("attachments", "Anhänge")
        if curr_tab == tl_tab or curr_tab == "Zeitleiste":
            self.timeline_widget.load_timeline(self.current_case.timeline)
        elif curr_tab == att_tab or curr_tab == "Anhänge":
            self.attachment_widget.load_attachments(self.current_case)

    def on_more_actions_selected(self, choice: str):
        if choice.startswith("📧"):
            self.on_copy_practice_email()
        elif choice.startswith("📤"):
            self.on_click_export()
        elif choice.startswith("🖨"):
            self.on_click_print()
        elif choice.startswith("🔄"):
            self.open_convert_schema_dialog()
        if hasattr(self, "more_actions_combo"):
            from services.i18n_service import tr
            self.more_actions_combo.set(tr("cockpit.more_actions", "⚙ Weitere Aktionen..."))

    def on_copy_practice_email(self):
        if not self.current_case or not self.current_case.customer:
            return

        email = self.current_case.customer.email
        if not email and getattr(self.current_case.customer, "all_emails", None):
            emails = self.current_case.customer.all_emails
            if emails:
                email = emails[0]

        if email and email.strip():
            email_clean = email.strip()
            self.clipboard_clear()
            self.clipboard_append(email_clean)
            from ui.widgets.toast_notification import ToastNotification
            from services.i18n_service import tr
            ToastNotification(
                self.winfo_toplevel(),
                title=tr("cockpit.email_copied_title", "📋 E-Mail kopiert"),
                message=tr("cockpit.email_copied_message", "Praxis-E-Mail '{email}' wurde in die Zwischenablage kopiert.", email=email_clean),
            )
        else:
            from ui.widgets.toast_notification import ToastNotification
            from services.i18n_service import tr
            ToastNotification(
                self.winfo_toplevel(),
                title=tr("cockpit.no_email_title", "⚠ Keine E-Mail-Adresse"),
                message=tr("cockpit.no_email_msg", "Für diese Praxis ist keine E-Mail-Adresse hinterlegt."),
            )

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
            # Formular neu aufbauen, damit rote Umrandungen fehlender Pflichtfelder
            # sofort verschwinden (bzw. neu erscheinen), sobald sich der
            # Vollstaendigkeitsstatus durch das Speichern geaendert hat.
            self.form_widget.load_schema(schema, self.current_case.form_data, self.current_case.missing_required_fields, case=self.current_case)

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
                    from services.i18n_service import tr
                    prev_actor_val = self.current_case.workflow_status.current_actor
                    self.current_case.workflow_status.current_actor = new_actor_val
                    self.current_case.workflow_status.actor_since = now_iso()

                    person_str = f" ({person})" if person else ""
                    note_str = f" | Details: {note}" if note else ""
                    note_text = tr("timeline.handover_note", "Zuständigkeit übergeben an: {actor}{person} via {channel}{note}", actor=get_actor_display(new_actor_val), person=person_str, channel=channel, note=note_str)
                    change_text = tr("timeline.handover_status", "ZUSTÄNDIGKEIT: {prev} -> {curr}", prev=get_actor_display(prev_actor_val), curr=get_actor_display(new_actor_val))

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
            self._update_wiedervorlage_display()
            self.on_click_save()

    def on_toggle_complete(self):
        if self.current_case:
            from services.i18n_service import tr
            new_state = not self.current_case.workflow_status.is_completed
            self.current_case.workflow_status.is_completed = new_state
            if new_state:
                self.current_case.workflow_status.followup_at = ""
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
                author=self.author_name,
                channel=Channel.INTERNAL_NOTE.value,
                note=note_text,
                status_change=change_text,
            )
            self.current_case.timeline.append(entry)
            self.timeline_widget.load_timeline(self.current_case.timeline)

            self.complete_btn.configure(text=tr("cockpit.reopen", "✓ Wieder öffnen") if new_state else tr("cockpit.complete", "✓ Erledigen"))
            self._update_title_label()
            self._update_wiedervorlage_display()
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
        from services.i18n_service import tr
        self._wiedervorlage_full_text = f"{tr('cockpit.followup_at', '🔔 Nachfragen am:')} {fw_date_str}, {fw_time_str}{note_suffix}"

        # Compute available pixel width in info_left_frame
        w = self.info_left_frame.winfo_width()
        if w <= 50:
            bar_w = self.info_row.winfo_width()
            right_w = self.status_right_frame.winfo_reqwidth()
            w = max(250, (bar_w - right_w - 30) if bar_w > right_w + 50 else 380)
        else:
            w = max(200, w - 10)

        self._last_info_w = w
        from services.i18n_service import tr
        self.wv_hdr_label.configure(text=tr("cockpit.followup_at", "🔔 Nachfragen am:"), wraplength=w)
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

