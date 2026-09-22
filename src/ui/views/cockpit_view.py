import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from models.case import Case, TimelineEntry
from models.schema import QuestionSchema
from models.profile import UserProfile
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from services.schema_service import SchemaService

from constants import (
    COCKPIT_CENTER_MIN_WIDTH,
    COCKPIT_SIDEBAR_MIN_WIDTH,
    COLOR_PANED_PANE_BG,
    COLOR_SASH_DARK,
    COLOR_SASH_LIGHT,
    COMBO_WIDTH_SM,
    DEFAULT_COLUMN_WIDTHS,
    DEFAULT_SIDEBAR_TAB_ATTACHMENTS,
    DEFAULT_SIDEBAR_TAB_TIMELINE,
    DEFAULT_SIDEBAR_TAB_WIKI,
    INFO_FRAME_MIN_WIDTH_THRESHOLD,
    INFO_FRAME_RESIZE_DELTA,
    PAD_NONE,
    PAD_XS,
    PANED_MIN_TOTAL_WIDTH,
    PANED_PANE_MIN_WIDTH,
    SASH_RESTORE_DELAY_FAST_MS,
    SASH_RESTORE_DELAY_SLOW_MS,
    SASH_SETTLE_DELAY_MS,
    SASH_VERIFY_MAX_ATTEMPTS,
    SASH_VERIFY_RETRY_MS,
    SASH_WIDTH_TOLERANCE,
    VIP_TAG_DISPLAY,
    WIEDERVORLAGE_FALLBACK_DEFAULT_WIDTH,
    WIEDERVORLAGE_FALLBACK_MIN_WIDTH,
    WIEDERVORLAGE_MIN_WIDTH,
    WIEDERVORLAGE_MIN_WRAP_WIDTH,
    WIEDERVORLAGE_WRAP_OFFSET,
)
from ui.views.cockpit_layout_builders import CockpitLayoutBuilderMixin


import logging

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
        on_change_practice: Callable[[Case], None] | None = None,
        on_delete_case: Callable[[Case], None] | None = None,
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
        self.on_change_practice: Callable[[Case], None] = on_change_practice if on_change_practice is not None else (lambda c: None)
        self.on_delete_case: Callable[[Case], None] = on_delete_case if on_delete_case is not None else (lambda c: None)

        self.current_case: Case | None = None
        self.schemas: list[QuestionSchema] = []

        # Solange False, zieht jede Breitenaenderung des PanedWindow den Restore
        # nach - noetig, weil das Fenster erst nach dem Bauen maximiert wird.
        self._sash_user_dragged = False
        self._sash_restored = False
        self._sash_restore_after_id = None

        self.create_layout()


    def _sash_extra(self) -> int:
        """Pixel, die eine Sash zwischen zwei Panes belegt (sashwidth + 2*sashpad).

        sash_coord() liefert die linke Kante der Sash, nicht den Anfang des
        rechten Panes. Ohne diesen Zuschlag ist die gespeicherte Breite der
        rechten Spalte um genau diese Pixel zu gross.
        """
        try:
            return int(self.paned.cget("sashwidth")) + 2 * int(self.paned.cget("sashpad"))
        except Exception:
            return 8

    def _pin_pane_widths(self, w_left: int, w_right: int):
        """Schreibt die Breiten als -width in die Pane-Optionen der Seitenspalten.

        Der entscheidende Punkt gegen das Zurueckspringen: sash_place() setzt nur
        die momentane Groesse. Sobald ein Kind eine neue Wunschbreite anmeldet -
        und der CTkTabview rechts tut das bei jedem Tab-Wechsel, seine reqwidth
        pendelt zwischen 303 und 361 - leitet Tk die Pane-Groessen neu aus den
        Wunschbreiten ab und die per Sash gesetzte Breite ist weg. Im Log war das
        als Sprung der rechten Spalte auf 120px (= minsize) sichtbar, wobei die
        Mitte als einziger Pane mit stretch="always" alles geschluckt hat.

        Mit gesetztem -width auf beiden Seitenspalten haelt Tk sie fest und gibt
        nur noch der Mitte den Rest. Beim Ziehen aktualisiert save_sash_widths()
        die Option, damit der neue Wert der massgebliche bleibt.
        """
        try:
            self.paned.paneconfigure(self.left_frame, width=w_left)
            self.paned.paneconfigure(self.right_tabview, width=w_right)
        except Exception as e:
            logger.warning(f"Could not pin pane widths: {e}")

    def _stored_column_widths(self) -> tuple[int, int]:
        widths = {}
        if self.profile and hasattr(self.profile, "ui_settings") and hasattr(self.profile.ui_settings, "column_widths"):
            widths = self.profile.ui_settings.column_widths
        elif self.app_config and hasattr(self.app_config, "column_widths"):
            widths = self.app_config.column_widths
        return (
            widths.get("cockpit_left", DEFAULT_COLUMN_WIDTHS["cockpit_left"]),
            widths.get("cockpit_right", DEFAULT_COLUMN_WIDTHS["cockpit_right"]),
        )

    def apply_column_widths(self, widths: dict[str, int]):
        w_left = widths.get("cockpit_left", DEFAULT_COLUMN_WIDTHS["cockpit_left"])
        w_right = widths.get("cockpit_right", DEFAULT_COLUMN_WIDTHS["cockpit_right"])
        if hasattr(self, "paned"):
            try:
                total_w = self.paned.winfo_width()
                if total_w > PANED_MIN_TOTAL_WIDTH:
                    self._place_sashes(total_w, w_left, w_right)
            except Exception:
                pass

    def _place_sashes(self, total_w: int, w_left: int, w_right: int):
        extra = self._sash_extra()
        self.paned.sash_place(0, w_left, 0)
        self.paned.sash_place(
            1,
            max(w_left + COCKPIT_CENTER_MIN_WIDTH, total_w - w_right - extra),
            0,
        )
        self._pin_pane_widths(w_left, w_right)

    def restore_sash_positions(self):
        try:
            if not hasattr(self, "paned") or not self.paned.winfo_exists():
                return
            total_w = self.paned.winfo_width()
            if total_w <= PANED_MIN_TOTAL_WIDTH:
                self.after(SASH_RESTORE_DELAY_FAST_MS, self.restore_sash_positions)
                return

            w_left, w_right = self._stored_column_widths()
            self._place_sashes(total_w, w_left, w_right)
            self._last_paned_width = total_w
            self._sash_restored = True
            self._schedule_verify(w_left, w_right, 0, None)
        except Exception as e:
            logger.warning(f"Could not restore sash positions: {e}")

    def _schedule_verify(self, w_left: int, w_right: int, attempt: int, delay: int | None):
        """Plant die Breitenkontrolle ein; ohne Tk-Kontext einfach nicht."""
        try:
            cb = lambda: self._verify_right_width(w_left, w_right, attempt)
            if delay is None:
                self.after_idle(cb)
            else:
                self.after(delay, cb)
        except Exception:
            pass

    def _verify_right_width(self, w_left: int, w_right: int, attempt: int):
        """Prueft nach dem Idle-Durchlauf, ob Tk die Breite behalten hat.

        Guertel und Hosentraeger: sash_place() allein hat nicht gehalten, weil Tk
        die Pane-Groessen beim naechsten Geometry-Recompute aus den Wunschbreiten
        der Kinder neu ableitet - im Log fiel die rechte Spalte dabei jedes Mal
        auf 120px. _pin_pane_widths() sollte das verhindern; falls nicht, merkt
        es diese Kontrolle und zieht nach, statt die Spalte falsch stehen zu
        lassen. Begrenzt auf wenige Versuche, damit daraus keine Endlosschleife
        gegen den Geometry-Manager wird, und still, sobald der Nutzer selbst
        zieht.
        """
        if getattr(self, "_sash_user_dragged", False):
            return
        try:
            if not hasattr(self, "paned") or not self.paned.winfo_exists():
                return
            if not hasattr(self, "right_tabview") or not self.right_tabview.winfo_exists():
                return
            actual = self.right_tabview.winfo_width()
            if abs(actual - w_right) <= SASH_WIDTH_TOLERANCE:
                return
            if attempt >= SASH_VERIFY_MAX_ATTEMPTS:
                logger.warning(
                    f"Right column stayed at {actual}px instead of {w_right}px "
                    f"after {attempt} corrections - giving up to avoid fighting the geometry manager."
                )
                return
            total_w = self.paned.winfo_width()
            if total_w > PANED_MIN_TOTAL_WIDTH:
                self._place_sashes(total_w, w_left, w_right)
            self._schedule_verify(w_left, w_right, attempt + 1, SASH_VERIFY_RETRY_MS)
        except Exception as e:
            logger.warning(f"Could not verify right column width: {e}")

    def on_paned_sash_released(self, event=None):
        self._sash_user_dragged = True
        self.save_sash_widths()
        self._refresh_sidebar_after_resize()

    def _refresh_sidebar_after_resize(self):
        """Erzwingt einen sauberen Neuaufbau der CTk-Zeichnungen rechts.

        CustomTkinter zeichnet auf interne Canvas-Flaechen und raeumt die beim
        Groessenwechsel des Panes nicht immer vollstaendig ab - sichtbar als
        blauer Rest neben dem Kanal-Dropdown der Zeitleiste. configure() mit dem
        unveraenderten Wert loest ein vollstaendiges _draw() aus und ist dabei
        oeffentliche API, im Gegensatz zu einem Griff in die Interna.
        """
        combo = getattr(getattr(self, "timeline_widget", None), "channel_combo", None)
        try:
            if combo is not None and combo.winfo_exists():
                combo.configure(width=COMBO_WIDTH_SM)
        except Exception as e:
            # Reines Neuzeichnen - nie ein Grund, das Speichern zu stoeren.
            logger.debug(f"Could not redraw channel combo: {e}")
        try:
            self.right_tabview.update_idletasks()
        except Exception as e:
            logger.debug(f"Could not refresh sidebar after resize: {e}")

    def _on_paned_configure(self, event=None):
        """Merkt sich die Breite und zieht den Erst-Restore nach, bis er sitzt.

        Die drei Spaltenbreiten hier neu zu berechnen und beide Sashes neu zu
        setzen war frueher falsch: das hat gegen den Geometry-Manager gearbeitet,
        der den Platz laut stretch-Einstellung schon verteilt hatte, und verloren -
        ein um 600px breiteres Fenster endete mit einer *schmaleren* Mitte.

        Was hier passieren muss, ist etwas anderes: Das Fenster wird versteckt mit
        1440x880 gebaut und erst in _reveal_window() maximiert. Im Log lag der
        erste Restore bei 404ms noch auf total=1426, das PanedWindow erreichte
        seine echten 1906 erst bei 443ms. Da die rechte Spalte als Abstand vom
        rechten Rand wiederhergestellt wird, braucht sie zwingend die *endgueltige*
        Gesamtbreite - feste Delays treffen die nicht zuverlaessig. Also wird bis
        zum ersten Zug des Nutzers bei jeder Breitenaenderung nachgezogen.
        """
        if event is not None and getattr(event, "widget", None) != self.paned:
            return
        try:
            total_w = self.paned.winfo_width() if event is None else event.width
            if total_w <= PANED_MIN_TOTAL_WIDTH:
                return
            prev = getattr(self, "_last_paned_width", None)
            self._last_paned_width = total_w
            if prev == total_w:
                return

            if getattr(self, "_sash_user_dragged", False):
                return
            # Entprellt: waehrend das Fenster maximiert wird, kommen mehrere
            # Configure-Events kurz hintereinander.
            pending = getattr(self, "_sash_restore_after_id", None)
            if pending:
                try:
                    self.after_cancel(pending)
                except Exception:
                    pass
            self._sash_restore_after_id = self.after(SASH_SETTLE_DELAY_MS, self._restore_after_settle)
        except Exception:
            pass

    def _restore_after_settle(self):
        self._sash_restore_after_id = None
        if getattr(self, "_sash_user_dragged", False):
            return
        self.restore_sash_positions()

    def save_sash_widths(self):
        try:
            if not hasattr(self, "paned") or not self.paned.winfo_exists():
                return
            total_w = self.paned.winfo_width()
            if total_w <= PANED_MIN_TOTAL_WIDTH:
                return

            self._last_paned_width = total_w

            sash0 = self.paned.sash_coord(0)
            sash1 = self.paned.sash_coord(1)
            extra = self._sash_extra()

            w_left = w_right = None
            if sash0 and len(sash0) > 0 and sash0[0] > 0:
                w_left = max(PANED_PANE_MIN_WIDTH, sash0[0])
                if self.profile and hasattr(self.profile, "ui_settings"):
                    self.profile.ui_settings.column_widths["cockpit_left"] = w_left

            if sash1 and len(sash1) > 0 and sash1[0] > 0:
                # extra abziehen: sash_coord() gibt die linke Sash-Kante zurueck,
                # der rechte Pane beginnt erst dahinter.
                w_right = max(PANED_PANE_MIN_WIDTH, total_w - sash1[0] - extra)
                if self.profile and hasattr(self.profile, "ui_settings"):
                    self.profile.ui_settings.column_widths["cockpit_right"] = w_right


            # Die gezogene Breite wird zur neuen Pane-Option, sonst holt sich Tk
            # beim naechsten Geometry-Recompute die alte zurueck.
            if w_left is not None and w_right is not None:
                self._pin_pane_widths(w_left, w_right)

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
            target_bg = COLOR_PANED_PANE_BG
            for attr in ("left_frame", "center_frame", "right_tabview"):
                w = getattr(self, attr, None)
                if w is not None and hasattr(w, "configure") and hasattr(w, "winfo_exists") and w.winfo_exists():
                    try:
                        w.configure(bg_color=target_bg)
                    except Exception:
                        pass

    def create_layout(self):
        w_left, w_right = self._build_paned_window()

        self._build_left_pane()
        self._build_center_pane()
        self._build_right_pane()

        # stretch decides who gets the space when the window changes size, and
        # it has to be set: Tk's default is "last", so the whole gain went to the
        # right sidebar - widening the window by 600px made the middle column
        # *narrower*. The middle column is the one that should grow; the two
        # outer ones keep the width the user dragged them to.
        #
        # Kein width= hier beim add(): zu diesem Zeitpunkt sind die gespeicherten
        # Breiten noch nicht angewandt. Gesetzt wird -width nachtraeglich in
        # _pin_pane_widths(), aufgerufen aus restore_sash_positions() und
        # save_sash_widths(). Ohne dieses -width haelt Tk die per sash_place()
        # gesetzten Groessen nicht: sobald ein Kind eine neue Wunschbreite
        # anmeldet, leitet Tk die Pane-Groessen neu aus den Wunschbreiten ab, und
        # die rechte Spalte fiel dabei auf minsize (120px) zurueck, waehrend die
        # Mitte als einziger stretch="always"-Pane alles geschluckt hat.
        self.paned.add(self.left_frame, minsize=COCKPIT_SIDEBAR_MIN_WIDTH, stretch="never")
        self.paned.add(self.center_frame, minsize=COCKPIT_CENTER_MIN_WIDTH, stretch="always")
        self.paned.add(self.right_tabview, minsize=COCKPIT_SIDEBAR_MIN_WIDTH, stretch="never")
        self._initial_widths = (w_left, w_right)

        self.after(SASH_RESTORE_DELAY_FAST_MS, self.restore_sash_positions)
        self.after(SASH_RESTORE_DELAY_SLOW_MS, self.restore_sash_positions)

    def set_cases(self, cases: list[Case], deep_results: dict[str, dict] | None = None):
        self.left_frame.set_cases(cases, deep_results=deep_results)

    def set_schemas(self, schemas: list[QuestionSchema]):
        self.schemas = schemas

    def focus_timeline_note(self):
        tl_tab = getattr(self, "_sidebar_tab_names", {}).get("timeline", DEFAULT_SIDEBAR_TAB_TIMELINE)
        self.right_tabview.set(tl_tab)
        self._on_sidebar_tab_changed(tl_tab)
        self.timeline_widget.note_textbox.focus_set()

    def on_click_print(self):
        if self.current_case:
            from ui.dialogs.case_print_dialog import CasePrintDialog
            CasePrintDialog(self, self.current_case, attachment_service=self.attachment_service, schemas=self.schemas)

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

    def clear_current_case(self) -> None:
        """Empties the detail pane after the open case disappeared.

        Deleting a case used to leave every panel showing it until the user
        clicked another one, because nothing reset the pane - the caller only
        set current_case to None, which the individual panels never see.
        """
        from services.i18n_service import tr

        self.current_case = None

        self.case_title_label.configure(text=tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen"))
        self.kunde_label.configure(text="")
        self.ansprechpartner_label.configure(text="")

        for widget in (
            self.print_btn, self.email_btn, self.cal_btn,
            self.export_btn, self.save_btn, self.convert_schema_btn,
        ):
            try:
                widget.configure(state="disabled")
            except Exception:
                pass

        self.actor_combo.set(tr("cockpit.handover_action", "Übergabe"))
        self.complete_btn.configure(text=tr("cockpit.complete", "✓ Erledigt"))

        self._update_wiedervorlage_display()

        # The sidebar caches which case each tab last rendered; without this the
        # tab would consider itself up to date and keep the deleted case around.
        self._loaded_tab_case_ids.clear()

        self.form_widget.load_schema(None, {}, [], case=None)
        self.timeline_widget.load_timeline([])
        self.attachment_widget.load_attachments(None)

    def on_select_case_from_list(self, case: Case):
        self.current_case = case
        if self.on_case_selected:
            self.on_case_selected(case)

        self._update_title_label()
        self.print_btn.configure(state="normal")
        self.email_btn.configure(state="normal")
        self.cal_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.convert_schema_btn.configure(state="normal")

        from services.i18n_service import tr
        vip_str = VIP_TAG_DISPLAY if case.customer.is_vip else ""
        if case.is_internal:
            self.kunde_label.configure(text=f"🏢 {tr('cockpit.customer', 'Kunde')}: {tr('cockpit.internal_task_title', 'INTERNE AUFGABE / VORGANG')} ({case.customer.customer_id}){vip_str}")
        else:
            self.kunde_label.configure(text=f"🏥 {tr('cockpit.customer', 'Kunde')}: {case.customer.practice_name} ({case.customer.customer_id}){vip_str}")

        full_addr = getattr(case.customer, "full_address", "")
        addr_str = f" | 🏠 {full_addr}" if full_addr else ""
        self.ansprechpartner_label.configure(text=f"👤 {tr('cockpit.contact_person', 'Ansprechpartner')}: {case.customer.contact_person}{addr_str}")

        self._update_wiedervorlage_display()

        self.actor_combo.set(tr("cockpit.handover_action", "Übergabe"))
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
        tl_tab = getattr(self, "_sidebar_tab_names", {}).get("timeline", DEFAULT_SIDEBAR_TAB_TIMELINE)
        att_tab = getattr(self, "_sidebar_tab_names", {}).get("attachments", DEFAULT_SIDEBAR_TAB_ATTACHMENTS)
        if curr_tab in (tl_tab, DEFAULT_SIDEBAR_TAB_TIMELINE):
            self.timeline_widget.load_timeline(self.current_case.timeline)
        elif curr_tab in (att_tab, DEFAULT_SIDEBAR_TAB_ATTACHMENTS):
            self.attachment_widget.load_attachments(self.current_case)

    def on_more_actions_selected(self, choice: str):
        if choice.startswith("📤"):
            self.on_click_export()
        elif choice.startswith("✉"):
            self.on_click_email_calendar()
        elif choice.startswith("📅"):
            self.on_click_calendar()
        elif choice.startswith("📦"):
            self.on_click_archive()
        elif choice.startswith("🔄"):
            self.open_convert_schema_dialog()
        elif choice.startswith("📧"):
            self.on_copy_practice_email()
        elif choice.startswith("🖨"):
            self.on_click_print()
        elif choice.startswith("🏥"):
            if self.current_case:
                self.on_change_practice(self.current_case)
        elif choice.startswith("🗑"):
            if self.current_case:
                self.on_delete_case(self.current_case)
        if hasattr(self, "more_actions_combo"):
            from services.i18n_service import tr
            self.more_actions_combo.set(tr("cockpit.more_actions", "⚙ Weitere Aktionen..."))

    def on_copy_practice_email(self):
        if not self.current_case or not self.current_case.customer:
            return

        email = self.current_case.customer.email
        if not email:
            # case.customer is a CaseCustomer snapshot (single `email` field
            # only); all_emails is a property on the full Customer record.
            # Kept as a defensive getattr() in case a caller ever attaches a
            # full Customer here instead.
            emails = getattr(self.current_case.customer, "all_emails", None)
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
            # Nur die roten Umrandungen der Pflichtfelder nachziehen. Frueher lief
            # hier load_schema(), was saemtliche Widgets des Formulars neu gebaut
            # hat - fuer eine reine Farbaenderung, und mit dem Nebeneffekt, dass
            # Cursorposition und Scrollstand bei jedem Speichern verloren gingen.
            self.form_widget.apply_missing_field_highlight(self.current_case.missing_required_fields)

        self.scoring_service.update_case_scoring(self.current_case)
        self.on_case_updated(self.current_case)

    def on_actor_changed(self, new_actor_display: str):
        from services.i18n_service import tr
        if hasattr(self, "actor_combo"):
            self.actor_combo.set(tr("cockpit.handover_action", "Übergabe"))
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
                target_actor=new_actor_display,
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
            if w > INFO_FRAME_MIN_WIDTH_THRESHOLD and abs(w - self._last_info_w) > INFO_FRAME_RESIZE_DELTA:
                self._last_info_w = w
                self._updating_info = True
                wrap_w = max(WIEDERVORLAGE_MIN_WRAP_WIDTH, w - WIEDERVORLAGE_WRAP_OFFSET)
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

        from utils.datetime_utils import format_german_date_with_relative, format_german_time

        fw_date_str = format_german_date_with_relative(self.current_case.workflow_status.followup_at)
        fw_time_str = format_german_time(self.current_case.workflow_status.followup_at, with_uhr=True)
        note = self.current_case.workflow_status.followup_note or ""

        note_suffix = f" ({note})" if note else ""
        from services.i18n_service import tr
        self._wiedervorlage_full_text = f"{tr('cockpit.followup_at', '🔔 Nachfragen am:')} {fw_date_str}, {fw_time_str}{note_suffix}"

        # Compute available pixel width in info_left_frame
        w = self.info_left_frame.winfo_width()
        if w <= INFO_FRAME_MIN_WIDTH_THRESHOLD:
            bar_w = self.info_row.winfo_width()
            right_w = self.status_right_frame.winfo_reqwidth()
            w = max(WIEDERVORLAGE_FALLBACK_MIN_WIDTH, (bar_w - right_w - 30) if bar_w > right_w + INFO_FRAME_MIN_WIDTH_THRESHOLD else WIEDERVORLAGE_FALLBACK_DEFAULT_WIDTH)
        else:
            w = max(WIEDERVORLAGE_MIN_WIDTH, w - WIEDERVORLAGE_WRAP_OFFSET)

        self._last_info_w = w
        from services.i18n_service import tr
        self.wv_hdr_label.configure(text=tr("cockpit.followup_at", "🔔 Nachfragen am:"), wraplength=w)
        self.wv_date_label.configure(text=f"  {fw_date_str}", wraplength=w)
        self.wv_time_label.configure(text=f"  {fw_time_str}", wraplength=w)

        self.wv_hdr_label.pack(fill="x", anchor="w", pady=PAD_NONE)
        self.wv_date_label.pack(fill="x", anchor="w", pady=PAD_NONE)
        self.wv_time_label.pack(fill="x", anchor="w", pady=PAD_NONE)

        if note:
            self.wv_note_label.configure(text=f"  {note}", wraplength=w)
            self.wv_note_label.pack(fill="x", anchor="w", pady=PAD_NONE)
        else:
            self.wv_note_label.pack_forget()

        self.wiedervorlage_frame.pack(fill="x", anchor="w", pady=(PAD_XS, PAD_NONE))

    def focus_wiki_search(self):
        # cockpit_view.py used to define focus_wiki_search() twice; this was
        # the second (active - Python/pyright both use the last definition)
        # of the two, and it never switched to the Wiki tab first, so the
        # shortcut bound to it in app.py silently focused a hidden widget.
        # Restoring the tab-switch from the (until now dead) first definition.
        if hasattr(self, "right_tabview"):
            wiki_tab = getattr(self, "_sidebar_tab_names", {}).get("wiki", DEFAULT_SIDEBAR_TAB_WIKI)
            self.right_tabview.set(wiki_tab)
        if hasattr(self, "wiki_widget") and hasattr(self.wiki_widget, "search_entry"):
            self.wiki_widget.search_entry.focus()
            self.wiki_widget.search_entry.select_range(0, "end")

    def focus_customer_search(self):
        if hasattr(self, "left_frame") and hasattr(self.left_frame, "search_entry"):
            self.left_frame.search_entry.focus()
            self.left_frame.search_entry.select_range(0, "end")

