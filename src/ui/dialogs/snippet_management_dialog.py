import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from collections.abc import Callable
from models.snippet import Snippet
from services.snippet_service import SnippetService
from services.i18n_service import tr
from constants import (
    BTN_WIDTH_CANCEL,
    BTN_WIDTH_MD,
    COLOR_BTN_CANCEL,
    COLOR_BTN_GRAY30,
    COLOR_BTN_GRAY45,
    COLOR_DANGER,
    COLOR_DARKGREEN_HOVER,
    COLOR_DARKRED_HOVER,
    COLOR_DEEPSKYBLUE_HOVER,
    COLOR_LABEL_GRAY70,
    COLOR_PRIMARY_BLUE,
    COLOR_SNIPPET_CARD_ACTIVE,
    COLOR_SNIPPET_CARD_INACTIVE,
    COLOR_SUCCESS,
    COLOR_TEXT_GRAY,
    COLOR_TEXT_GREEN,
    CORNER_RADIUS_MD,
    CURSOR_HAND,
    DEFAULT_SNIPPET_CATEGORY,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_SNIPPET_MGMT,
    DIALOG_TITLES,
    EVENT_BUTTON_1,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    HOTKEY_RECORDER_BUTTON,
    LABEL_SNIPPET_SHORTCUT_FIELD,
    PAD_10,
    PAD_15,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    SNIPPET_FORM_MIN_WIDTH,
    SNIPPET_LIST_MIN_WIDTH,
    STATUS_MESSAGES,
    TEXTBOX_HEIGHT_SNIPPET_CONTENT,
)


class SnippetManagementDialog(BaseDialog):
    """Management dialog for adding, editing, and removing text snippets."""

    def __init__(self, parent, snippet_service: SnippetService, on_snippets_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.service = snippet_service
        self.on_snippets_updated = on_snippets_updated
        self.selected_snippet: Snippet | None = None

        w, h = DIALOG_DIMENSIONS["snippet_mgmt"]
        self.setup_window(
            parent,
            DIALOG_TITLES["snippet_mgmt"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_SNIPPET_MGMT,
            title_factory=lambda: DIALOG_TITLES["snippet_mgmt"],
        )

        self.create_widgets()
        self.refresh_list()
        # Closing now asks before throwing away an edited text block.
        self.enable_unsaved_guard()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_15)

        # Title Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(PAD_NONE, PAD_10))

        self.register_i18n(
            ctk.CTkLabel(
                hdr_frame,
                text=tr("snippet_mgmt.header", "📝 Textbaustein-Bibliothek verwalten"),
                font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD),
            ),
            "snippet_mgmt.header",
            "📝 Textbaustein-Bibliothek verwalten",
        ).pack(side="left")

        self.register_i18n(
            ctk.CTkButton(
                hdr_frame,
                text=tr("snippet_mgmt.new_snippet", "+ Neuer Textbaustein"),
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_DARKGREEN_HOVER,
                command=self.on_click_new,
            ),
            "snippet_mgmt.new_snippet",
            "+ Neuer Textbaustein",
        ).pack(side="right")

        # 2-Column Content (Left: List, Right: Edit Form)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_10))
        content_frame.grid_columnconfigure(0, weight=1, minsize=SNIPPET_LIST_MIN_WIDTH)
        content_frame.grid_columnconfigure(1, weight=1, minsize=SNIPPET_FORM_MIN_WIDTH)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left List Container
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.list_scroll = ctk.CTkScrollableFrame(content_frame)
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=(PAD_NONE, PAD_MD))
        enable_auto_hiding_scrollbar(self.list_scroll)

        # Right Edit Form Container
        self.form_box = ctk.CTkScrollableFrame(content_frame)
        self.form_box.grid(row=0, column=1, sticky="nsew")
        enable_auto_hiding_scrollbar(self.form_box)

        self.register_i18n(
            ctk.CTkLabel(
                self.form_box,
                text=tr("snippet_mgmt.title_lbl", "Titel:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "snippet_mgmt.title_lbl",
            "Titel:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.title_entry = self.register_i18n(
            ctk.CTkEntry(
                self.form_box,
                placeholder_text=tr("snippet_mgmt.title_placeholder", "z. B. 📸 Rückfrage: Screenshots"),
            ),
            "snippet_mgmt.title_placeholder",
            "z. B. 📸 Rückfrage: Screenshots",
            attr="placeholder_text",
        )
        self.title_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(
                self.form_box,
                text=tr("snippet_mgmt.cat_lbl", "Kategorie:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "snippet_mgmt.cat_lbl",
            "Kategorie:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.category_entry = self.register_i18n(
            ctk.CTkEntry(
                self.form_box,
                placeholder_text=tr("snippet_mgmt.category_placeholder", "z. B. Rückfrage, Anleitung, SQL"),
            ),
            "snippet_mgmt.category_placeholder",
            "z. B. Rückfrage, Anleitung, SQL",
            attr="placeholder_text",
        )
        self.category_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(
                self.form_box,
                text=tr("snippet_mgmt.content_lbl", "Inhalt / Baustein-Text:"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "snippet_mgmt.content_lbl",
            "Inhalt / Baustein-Text:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.content_textbox = ctk.CTkTextbox(self.form_box, height=TEXTBOX_HEIGHT_SNIPPET_CONTENT)
        self.content_textbox.pack(fill="x", expand=True, pady=(PAD_NONE, PAD_MD))

        self.register_i18n(
            ctk.CTkLabel(
                self.form_box,
                text=tr("snippet_mgmt.tags_lbl", "Tags (kommagetrennt):"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            ),
            "snippet_mgmt.tags_lbl",
            "Tags (kommagetrennt):",
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.tags_entry = self.register_i18n(
            ctk.CTkEntry(
                self.form_box,
                placeholder_text=tr("snippet_mgmt.tags_placeholder", "z. B. fehler, sql, anleitung"),
            ),
            "snippet_mgmt.tags_placeholder",
            "z. B. fehler, sql, anleitung",
            attr="placeholder_text",
        )
        self.tags_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        ctk.CTkLabel(
            self.form_box,
            text=LABEL_SNIPPET_SHORTCUT_FIELD,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        ).pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        sc_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        sc_row.pack(fill="x", pady=(PAD_NONE, PAD_LG))

        self.shortcut_entry = self.register_i18n(
            ctk.CTkEntry(
                sc_row,
                placeholder_text=tr("snippet_mgmt.shortcut_placeholder", "z. B. <Control-Alt-1>"),
            ),
            "snippet_mgmt.shortcut_placeholder",
            "z. B. <Control-Alt-1>",
            attr="placeholder_text",
        )
        self.shortcut_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_CONTAINER))

        rec_btn = ctk.CTkButton(
            sc_row,
            text=HOTKEY_RECORDER_BUTTON,
            width=BTN_WIDTH_MD,
            fg_color=COLOR_BTN_GRAY30,
            hover_color=COLOR_BTN_GRAY45,
            command=self.open_hotkey_recorder,
        )
        rec_btn.pack(side="right")

        # Status & Action Buttons
        self.status_lbl = ctk.CTkLabel(
            self.form_box,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_PRIMARY_BLUE,
        )
        self.status_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_GAP))

        btn_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        btn_row.pack(fill="x", pady=(PAD_CONTAINER, PAD_NONE))

        self.save_btn = self.register_i18n(
            ctk.CTkButton(
                btn_row,
                text=tr("cockpit.save", "💾 Speichern"),
                fg_color=COLOR_PRIMARY_BLUE,
                hover_color=COLOR_DEEPSKYBLUE_HOVER,
                command=self.on_click_save,
            ),
            "cockpit.save",
            "💾 Speichern",
        )
        self.save_btn.pack(side="left", padx=(PAD_NONE, PAD_GAP))

        self.delete_btn = self.register_i18n(
            ctk.CTkButton(
                btn_row,
                text=tr("common.delete", "🗑 Löschen"),
                fg_color=COLOR_DANGER,
                hover_color=COLOR_DARKRED_HOVER,
                command=self.confirm_click_delete,
                state="disabled",
            ),
            "common.delete",
            "🗑 Löschen",
        )
        self.delete_btn.pack(side="left")

        # Bottom Close Button
        self.register_i18n(
            ctk.CTkButton(
                main_frame,
                text=tr("common.close", "Schließen"),
                fg_color=COLOR_BTN_CANCEL,
                command=self.destroy,
                width=BTN_WIDTH_CANCEL,
            ),
            "common.close",
            "Schließen",
        ).pack(side="right", pady=(PAD_CONTAINER, PAD_NONE))

    def open_hotkey_recorder(self):
        from ui.dialogs.profile_settings_shortcuts_tab import HotkeyRecorderDialog

        def on_recorded(key_str: str):
            self.shortcut_entry.delete(0, "end")
            self.shortcut_entry.insert(0, key_str)

        HotkeyRecorderDialog(self, on_recorded)

    def refresh_list(self):
        snippets = self.service.get_all_snippets()

        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        if not snippets:
            self.register_i18n(
                ctk.CTkLabel(
                    self.list_scroll,
                    text=tr("snippet_mgmt.no_snippets", "Keine Textbausteine vorhanden."),
                ),
                "snippet_mgmt.no_snippets",
                "Keine Textbausteine vorhanden.",
            ).pack(pady=PAD_2XL)
            return

        for snip in snippets:
            is_sel = self.selected_snippet and self.selected_snippet.snippet_id == snip.snippet_id
            bg = COLOR_SNIPPET_CARD_ACTIVE if is_sel else COLOR_SNIPPET_CARD_INACTIVE

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, corner_radius=CORNER_RADIUS_MD, cursor=CURSOR_HAND)
            card.pack(fill="x", pady=PAD_SM, padx=PAD_SM)
            card.bind(EVENT_BUTTON_1, lambda e, s=snip: self.select_snippet(s))

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=PAD_GAP, pady=(PAD_SM, PAD_TINY))

            lbl_t = ctk.CTkLabel(
                top,
                text=snip.title,
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
                anchor="w",
            )
            lbl_t.pack(side="left", fill="x", expand=True)
            lbl_t.bind(EVENT_BUTTON_1, lambda e, s=snip: self.select_snippet(s))

            if snip.shortcut:
                lbl_sc = ctk.CTkLabel(
                    top,
                    text=f"⌨ {snip.shortcut}",
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_PRIMARY_BLUE,
                )
                lbl_sc.pack(side="right")
                lbl_sc.bind(EVENT_BUTTON_1, lambda e, s=snip: self.select_snippet(s))

            cat_lbl = ctk.CTkLabel(
                card,
                text=tr("snippet_mgmt.category_line", "Kategorie: {category}", category=snip.category),
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_LABEL_GRAY70,
                anchor="w",
            )
            cat_lbl.pack(fill="x", padx=PAD_GAP, pady=(PAD_NONE, PAD_SM))
            cat_lbl.bind(EVENT_BUTTON_1, lambda e, s=snip: self.select_snippet(s))

    def select_snippet(self, snip: Snippet):
        self.selected_snippet = snip
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, snip.title)

        self.category_entry.delete(0, "end")
        self.category_entry.insert(0, snip.category)

        self.content_textbox.delete("1.0", "end")
        self.content_textbox.insert("1.0", snip.content)

        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(snip.tags))

        self.shortcut_entry.delete(0, "end")
        if snip.shortcut:
            self.shortcut_entry.insert(0, snip.shortcut)

        self.delete_btn.configure(state="normal")
        self.status_lbl.configure(
            text=tr("snippet_mgmt.selected_status", "Ausgewählt: {id}", id=snip.snippet_id),
            text_color=COLOR_PRIMARY_BLUE,
        )
        self.refresh_list()
        # The form now shows the picked block, not the user's edits.
        self.mark_clean()

    def on_click_new(self):
        self.selected_snippet = None
        self.title_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.category_entry.insert(0, DEFAULT_SNIPPET_CATEGORY)
        self.content_textbox.delete("1.0", "end")
        self.tags_entry.delete(0, "end")
        self.shortcut_entry.delete(0, "end")
        self.delete_btn.configure(state="disabled")
        self.status_lbl.configure(
            text=tr("snippet_mgmt.new_snippet_status", "Neuer Textbaustein (wird beim Speichern angelegt)"),
            text_color=COLOR_TEXT_GRAY,
        )
        self.refresh_list()
        self.mark_clean()

    def on_click_save(self):
        title = self.title_entry.get().strip()
        cat = self.category_entry.get().strip() or DEFAULT_SNIPPET_CATEGORY
        content = self.content_textbox.get("1.0", "end-1c").strip()
        tags_raw = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        sc = self.shortcut_entry.get().strip()

        if not title:
            self.status_lbl.configure(
                text=tr("snippet_mgmt.title_required", "⚠ Bitte einen Titel eingeben."),
                text_color=COLOR_DANGER,
            )
            return
        if not content:
            self.status_lbl.configure(
                text=tr("snippet_mgmt.content_required", "⚠ Der Inhalt darf nicht leer sein."),
                text_color=COLOR_DANGER,
            )
            return

        sid = self.selected_snippet.snippet_id if self.selected_snippet else ""
        snip = Snippet(
            snippet_id=sid,
            title=title,
            category=cat,
            content=content,
            tags=tags,
            shortcut=sc,
        )

        self.service.add_or_update_snippet(snip)
        self.selected_snippet = snip
        self.delete_btn.configure(state="normal")
        self.status_lbl.configure(text=STATUS_MESSAGES["snippet_saved"], text_color=COLOR_TEXT_GREEN)
        self.refresh_list()
        # Saved - what is on screen is now what is stored.
        self.mark_clean()

        if self.on_snippets_updated:
            self.on_snippets_updated()

    def confirm_click_delete(self):
        """Asks before deleting the selected text block."""
        from ui.dialogs.confirm_dialog import ask_confirmation

        if not self.selected_snippet:
            return
        if ask_confirmation(
            self,
            tr("confirm.delete_snippet", "Textbaustein „{name}“ wirklich dauerhaft löschen?", name=self.selected_snippet.title),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_click_delete()

    def on_click_delete(self):
        if self.selected_snippet:
            self.service.delete_snippet(self.selected_snippet.snippet_id)
            self.status_lbl.configure(text=STATUS_MESSAGES["snippet_deleted"], text_color=COLOR_TEXT_GREEN)
            self.on_click_new()
            if self.on_snippets_updated:
                self.on_snippets_updated()
