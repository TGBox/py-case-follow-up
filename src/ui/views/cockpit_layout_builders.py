"""Layout-Aufbau fuer CockpitView: die komplette Widget-Konstruktion aus dem
ehemals ~221-zeiligen create_layout() (PanedWindow-Grundgeruest, Fallliste links,
Header-Card in der Mitte mit Titel-/Info-/Toolbar-Zeile plus Formular, Tab-Sidebar
rechts).

CockpitLayoutBuilderMixin wird per Mixin-Vererbung in CockpitView eingemischt,
sodass `self` weiterhin dieselbe View-Instanz ist und alle hier gesetzten
self.-Attribute (self.paned, self.header_card, self.form_widget, usw.) wie
gewohnt von den uebrigen Methoden (on_select_case_from_list, on_click_save, ...)
weiterverwendet werden koennen. create_layout() selbst bleibt in cockpit_view.py
und baut nur noch das PanedWindow-Geruest sowie den finalen "Panes hinzufuegen"-
Schritt auf, bevor/nachdem es an die passenden _build_*()-Methoden hier
delegiert - reines Verschieben von Code, keine Verhaltensaenderung.
"""
import customtkinter as ctk
import tkinter as tk
from enums import ACTOR_DISPLAY
from constants import COLOR_SASH_DARK, COLOR_SASH_LIGHT

from typing import TYPE_CHECKING, Any, Callable, cast

from ui.widgets.case_list_widget import CaseListWidget
from ui.widgets.dynamic_form_widget import DynamicFormWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.attachment_widget import AttachmentWidget
from ui.widgets.wiki_widget import WikiWidget


class CockpitLayoutBuilderMixin:
    """Baut das Layout von CockpitView auf. Nur zusammen mit CockpitView (bzw.
    einer Klasse mit denselben self.paned / self.center_frame / self.profile /
    ... Attributen und Methoden) nutzbar.
    """

    if TYPE_CHECKING:
        profile: Any
        app_config: Any
        storage_service: Any
        attachment_service: Any
        wiki_service: Any
        author_name: str
        on_paned_sash_released: Callable[..., Any]
        on_select_case_from_list: Callable[..., Any]
        on_search_changed: Callable[..., Any]
        on_manage_module_tags: Callable[..., Any]
        _get_wiedervorlage_tooltip_text: Callable[..., Any]
        _on_info_frame_configure: Callable[..., Any]
        on_click_archive: Callable[..., Any]
        on_toggle_complete: Callable[..., Any]
        on_actor_changed: Callable[..., Any]
        on_click_email: Callable[..., Any]
        on_click_calendar: Callable[..., Any]
        open_followup_dialog: Callable[..., Any]
        focus_timeline_note: Callable[..., Any]
        on_click_save: Callable[..., Any]
        on_more_actions_selected: Callable[..., Any]
        _on_sidebar_tab_changed: Callable[..., Any]
        on_timeline_updated: Callable[..., Any]
        on_open_snippet_picker: Callable[..., Any]

    def _build_paned_window(self):
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
            cast(Any, self),
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
        return w_left, w_right

    def _build_left_pane(self):
        # 1. Left Pane: Case List
        self.left_frame = CaseListWidget(
            self.paned,
            on_case_selected=self.on_select_case_from_list,
            on_search_changed=self.on_search_changed,
            on_toggle_deep_search=lambda active: self.on_search_changed(self.left_frame.search_entry.get()),
        )

    def _build_center_pane(self):
        # 2. Center Pane: Case Details & Dynamic Form
        self.center_frame = ctk.CTkFrame(self.paned)

        # Unified Cockpit Header Card Frame
        self.header_card = ctk.CTkFrame(self.center_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        self.header_card.pack(fill="x", padx=8, pady=(8, 6))
        self._build_title_row()
        self._build_info_row()
        self._build_toolbar_row()

        # Dynamic Form Widget
        self.form_widget = DynamicFormWidget(
            self.center_frame,
            profile=self.profile,
            storage_service=self.storage_service,
            attachment_service=self.attachment_service,
            on_manage_module_tags=self.on_manage_module_tags,
        )
        self.form_widget.pack(fill="both", expand=True, padx=5, pady=5)

        self._loaded_tab_case_ids: dict[str, str] = {}

    def _build_title_row(self):
        # Row 1: Dedicated Full-Width Case Title Row (prevents button overlaps)
        self.title_row = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.title_row.pack(fill="x", padx=10, pady=(8, 4))

        from services.i18n_service import tr

        self.case_title_label = ctk.CTkLabel(
            self.title_row,
            text=tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen"),
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
            justify="left",
        )
        self.case_title_label.pack(side="left", fill="x", expand=True)

    def _build_info_row(self):
        # Row 2: Customer & Status Info Row
        self.info_row = ctk.CTkFrame(self.header_card, fg_color="transparent")
        self.info_row.pack(fill="x", padx=10, pady=(2, 6))
        self.info_bar = self.info_row

        # Left Column: Customer details & Wiedervorlage deadline
        self.info_left_frame = ctk.CTkFrame(self.info_row, fg_color="transparent")
        self.info_left_frame.pack(side="left", fill="both", expand=True)

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

        # Right Column: Status Controls (Actor, Erledigen, Archivieren)
        self.status_right_frame = ctk.CTkFrame(self.info_row, fg_color="transparent")
        self.status_right_frame.pack(side="right", anchor="e")
        self.info_right_frame = self.status_right_frame

        from services.i18n_service import tr

        self.archive_btn = ctk.CTkButton(self.status_right_frame, text=tr("cockpit.archive", "📦 Archivieren"), command=self.on_click_archive, width=95, fg_color="darkred")
        self.archive_btn.pack(side="right", padx=2)

        self.complete_btn = ctk.CTkButton(self.status_right_frame, text=tr("cockpit.complete", "✓ Erledigt"), command=self.on_toggle_complete, width=90, fg_color="green")
        self.complete_btn.pack(side="right", padx=2)

        self.actor_combo = ctk.CTkOptionMenu(self.status_right_frame, values=list(ACTOR_DISPLAY.values()), command=self.on_actor_changed, width=130)
        self.actor_combo.pack(side="right", padx=2)

    def _build_toolbar_row(self):
        # Row 3: Integrated Action Toolbar
        self.toolbar_row = ctk.CTkFrame(self.header_card, fg_color=("gray80", "gray25"), corner_radius=6)
        self.toolbar_row.pack(fill="x", padx=8, pady=(2, 8))

        self.toolbar_left = ctk.CTkFrame(self.toolbar_row, fg_color="transparent")
        self.toolbar_left.pack(side="left", padx=4, pady=4)

        from services.i18n_service import tr

        self.email_btn = ctk.CTkButton(self.toolbar_left, text=tr("cockpit.email_ai", "✉ E-Mail & 🤖 KI"), command=self.on_click_email, width=130, state="disabled", fg_color="#6366f1", hover_color="#4f46e5")
        self.email_btn.pack(side="left", padx=3)

        self.cal_btn = ctk.CTkButton(self.toolbar_left, text=tr("cockpit.calendar", "📅 Kalender"), command=self.on_click_calendar, width=95, state="disabled", fg_color="forestgreen", hover_color="darkgreen")
        self.cal_btn.pack(side="left", padx=3)

        self.followup_btn = ctk.CTkButton(self.toolbar_left, text=tr("cockpit.followup", "🔔 Wiedervorlage"), command=self.open_followup_dialog, width=115, fg_color="darkblue")
        self.followup_btn.pack(side="left", padx=3)

        self.add_note_btn = ctk.CTkButton(self.toolbar_left, text=tr("cockpit.note", "📝 Notiz"), command=self.focus_timeline_note, width=80, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"))
        self.add_note_btn.pack(side="left", padx=3)

        # Right Side of Toolbar: Save Button + Integrated Dropdown Menu for Utilities
        self.toolbar_right = ctk.CTkFrame(self.toolbar_row, fg_color="transparent")
        self.toolbar_right.pack(side="right", padx=4, pady=4)

        self.save_btn = ctk.CTkButton(self.toolbar_right, text=tr("cockpit.save", "💾 Speichern"), command=self.on_click_save, width=95, state="disabled")
        self.save_btn.pack(side="left", padx=3)

        self.more_actions_combo = ctk.CTkOptionMenu(
            self.toolbar_right,
            values=[
                tr("cockpit.copy_email", "📧 Praxis E-Mail kopieren"),
                tr("cockpit.export_case", "📤 Fall exportieren"),
                tr("cockpit.print_case", "🖨 Fall-Akte drucken"),
                tr("cockpit.convert_form", "🔄 Formular umwandeln"),
            ],
            command=self.on_more_actions_selected,
            width=165,
            fg_color=("gray70", "gray35"),
            button_color=("gray60", "gray40"),
        )
        self.more_actions_combo.set(tr("cockpit.more_actions", "⚙ Weitere Aktionen..."))
        self.more_actions_combo.pack(side="left", padx=3)

        # Aliases for export, print, convert_schema buttons to maintain backward compatibility
        self.export_btn = self.more_actions_combo
        self.print_btn = self.more_actions_combo
        self.convert_schema_btn = self.more_actions_combo

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        if hasattr(self, "more_actions_combo"):
            self.more_actions_combo.configure(values=[
                tr("cockpit.copy_email", "📧 Praxis E-Mail kopieren"),
                tr("cockpit.export_case", "📤 Fall exportieren"),
                tr("cockpit.print_case", "🖨 Fall-Akte drucken"),
                tr("cockpit.convert_form", "🔄 Formular umwandeln"),
            ])
            self.more_actions_combo.set(tr("cockpit.more_actions", "⚙ Weitere Aktionen..."))
        if hasattr(self, "email_btn"):
            self.email_btn.configure(text=tr("cockpit.email_ai", "✉ E-Mail & 🤖 KI"))
        if hasattr(self, "cal_btn"):
            self.cal_btn.configure(text=tr("cockpit.calendar", "📅 Kalender"))
        if hasattr(self, "followup_btn"):
            self.followup_btn.configure(text=tr("cockpit.followup", "🔔 Wiedervorlage"))
        if hasattr(self, "add_note_btn"):
            self.add_note_btn.configure(text=tr("cockpit.note", "📝 Notiz"))
        if hasattr(self, "save_btn"):
            self.save_btn.configure(text=tr("cockpit.save", "💾 Speichern"))
        if hasattr(self, "complete_btn"):
            self.complete_btn.configure(text=tr("cockpit.complete", "✓ Erledigt"))
        if hasattr(self, "archive_btn"):
            self.archive_btn.configure(text=tr("cockpit.archive", "📦 Archivieren"))

        # Aliases for export, print, convert_schema buttons to maintain backward compatibility
        self.export_btn = self.more_actions_combo
        self.print_btn = self.more_actions_combo
        self.convert_schema_btn = self.more_actions_combo

        # Refresh right pane tabs ("Zeitleiste", "Anhänge", "Wiki")
        if hasattr(self, "right_tabview") and hasattr(self.right_tabview, "_segmented_button") and hasattr(self.right_tabview._segmented_button, "_buttons_dict"):
            btns = self.right_tabview._segmented_button._buttons_dict
            if hasattr(self, "_sidebar_tab_names"):
                for tab_key, orig_name in self._sidebar_tab_names.items():
                    if orig_name in btns:
                        btns[orig_name].configure(text=tr(f"cockpit.tab_{tab_key}", orig_name))

        # Refresh child widgets
        if hasattr(self, "case_list_widget") and hasattr(self.case_list_widget, "refresh_ui_labels"):
            self.case_list_widget.refresh_ui_labels()
        if hasattr(self, "timeline_widget") and hasattr(self.timeline_widget, "refresh_ui_labels"):
            self.timeline_widget.refresh_ui_labels()
        if hasattr(self, "attachment_widget") and hasattr(self.attachment_widget, "refresh_ui_labels"):
            self.attachment_widget.refresh_ui_labels()
        if hasattr(self, "wiki_widget") and hasattr(self.wiki_widget, "refresh_ui_labels"):
            self.wiki_widget.refresh_ui_labels()
        if hasattr(self, "form_widget") and hasattr(self.form_widget, "refresh_ui_labels"):
            self.form_widget.refresh_ui_labels()

    def _build_right_pane(self):
        from services.i18n_service import tr
        # 3. Right Pane: Tabbed Sidebar
        self.right_tabview = ctk.CTkTabview(self.paned, command=self._on_sidebar_tab_changed)

        t_title = tr("cockpit.tab_timeline", "Zeitleiste")
        t_attach = tr("cockpit.tab_attachments", "Anhänge")
        t_wiki = tr("cockpit.tab_wiki", "Wiki")

        self._sidebar_tab_names = {
            "timeline": t_title,
            "attachments": t_attach,
            "wiki": t_wiki,
        }

        tab_timeline = self.right_tabview.add(t_title)
        tab_attachments = self.right_tabview.add(t_attach)
        tab_wiki = self.right_tabview.add(t_wiki)

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

