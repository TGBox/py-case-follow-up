import customtkinter as ctk
from collections.abc import Callable

from constants import (
    BTN_WIDTH_QUIT,
    COLOR_BTN_GRAY,
    COLOR_PILL_ACTIVE,
    COLOR_PILL_HOVER,
    COLOR_SNIPPET_CARD_BG,
    COLOR_SNIPPET_CARD_SEL,
    COLOR_SNIPPET_PREVIEW_TEXT,
    COLOR_TEXT_PRIMARY,
    COMBO_WIDTH_CATEGORY,
    CORNER_RADIUS_MD,
    CURSOR_HAND,
    DEBOUNCE_KEY_SNIPPET_SEARCH,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_SNIPPET_PICKER,
    DIALOG_TITLES,
    ENTRY_WIDTH_LG,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XL,
    PAD_XS,
    SEARCH_DEBOUNCE_MS,
    SNIPPET_PICKER_COL0_MIN_WIDTH,
    SNIPPET_PICKER_COL1_MIN_WIDTH,
    SNIPPET_PREVIEW_MAX_LEN,
)
from models.snippet import Snippet
from services.snippet_service import SnippetService
from ui.dialogs.base_dialog import BaseDialog
from utils.ui_utils import (
    bind_mouse_wheel_to_canvas,
    create_highlighted_label,
    debounce,
    enable_auto_hiding_scrollbar,
)


class SnippetPickerDialog(BaseDialog):
    """Modal dialog for searching and picking a text snippet to insert into text fields."""

    def __init__(
        self,
        parent,
        snippet_service: SnippetService,
        on_snippet_selected: Callable[[str], None],
    ):
        super().__init__(parent)
        self.service = snippet_service
        self.on_snippet_selected = on_snippet_selected
        self.selected_snippet: Snippet | None = None

        w, h = DIALOG_DIMENSIONS["snippet_picker"]
        self.setup_window(
            parent,
            DIALOG_TITLES["snippet_picker"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_SNIPPET_PICKER,
            title_factory=lambda: DIALOG_TITLES["snippet_picker"],
        )

        self.create_widgets()
        self.refresh_snippet_list()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_XL - 1, pady=PAD_XL - 1)

        # Header & Search Controls
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD + PAD_XS))

        from services.i18n_service import tr

        self.search_entry = self.register_i18n(ctk.CTkEntry(
            hdr_frame, placeholder_text=tr("snippet_picker.search", "🔍 Textbaustein suchen..."), width=ENTRY_WIDTH_LG
        ), "snippet_picker.search", "🔍 Textbaustein suchen...", attr="placeholder_text")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_MD))
        self.search_entry.bind("<KeyRelease>", lambda e: debounce(self, DEBOUNCE_KEY_SNIPPET_SEARCH, SEARCH_DEBOUNCE_MS, self.refresh_snippet_list))

        self.cat_combo = ctk.CTkOptionMenu(
            hdr_frame,
            values=self.service.get_categories(),
            command=lambda v: self.refresh_snippet_list(),
            width=COMBO_WIDTH_CATEGORY,
        )
        self.cat_combo.pack(side="right")

        # 2-Column Content Layout (Left: Snippets List, Right: Content Preview)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD + PAD_XS))
        content_frame.grid_columnconfigure(0, weight=1, minsize=SNIPPET_PICKER_COL0_MIN_WIDTH)
        content_frame.grid_columnconfigure(1, weight=1, minsize=SNIPPET_PICKER_COL1_MIN_WIDTH)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left List Container
        self.list_scroll = ctk.CTkScrollableFrame(content_frame)
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=(PAD_NONE, PAD_MD))
        enable_auto_hiding_scrollbar(self.list_scroll)

        # Right Preview Container
        preview_box = ctk.CTkFrame(content_frame)
        preview_box.grid(row=0, column=1, sticky="nsew")

        self.register_i18n(ctk.CTkLabel(preview_box, text=tr("snippet_picker.preview", "Vorschau des Textbausteins:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "snippet_picker.preview", "Vorschau des Textbausteins:").pack(anchor="w", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM))

        self.preview_textbox = ctk.CTkTextbox(preview_box)
        self.preview_textbox.pack(fill="both", expand=True, padx=PAD_MD + PAD_XS, pady=(PAD_NONE, PAD_MD + PAD_XS))

        # Bottom Action Bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(PAD_CONTAINER, PAD_NONE))

        self.insert_btn = self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("snippet_picker.insert_btn", "Ausgewählten Baustein einfügen"),
            fg_color=COLOR_PILL_ACTIVE,
            hover_color=COLOR_PILL_HOVER,
            command=self.on_click_insert,
            state="disabled",
        ), "snippet_picker.insert_btn", "Ausgewählten Baustein einfügen")
        self.insert_btn.pack(side="right", padx=(CORNER_RADIUS_MD, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=COLOR_BTN_GRAY,
            command=self.destroy,
            width=BTN_WIDTH_QUIT,
        ), "common.cancel", "Abbrechen").pack(side="right")

    def refresh_snippet_list(self):
        from services.i18n_service import tr
        query = self.search_entry.get()
        cat = self.cat_combo.get()
        snippets = self.service.search_snippets(query=query, category=cat)

        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        if not snippets:
            self.register_i18n(ctk.CTkLabel(self.list_scroll, text=tr("snippet_picker.no_snippets", "Keine Textbausteine gefunden.")), "snippet_picker.no_snippets", "Keine Textbausteine gefunden.").pack(pady=PAD_2XL)
            return

        for snip in snippets:
            is_sel = self.selected_snippet and self.selected_snippet.snippet_id == snip.snippet_id
            bg = COLOR_SNIPPET_CARD_SEL if is_sel else COLOR_SNIPPET_CARD_BG

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, corner_radius=CORNER_RADIUS_MD, cursor=CURSOR_HAND)
            card.pack(fill="x", pady=PAD_SM, padx=PAD_SM)
            card.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            hdr_row = ctk.CTkFrame(card, fg_color="transparent")
            hdr_row.pack(fill="x", padx=PAD_MD, pady=(CORNER_RADIUS_MD, PAD_XS))
            hdr_row.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            title_text = f"{snip.title} ⌨ {snip.shortcut}" if snip.shortcut else snip.title
            if query and query.strip() and query.strip().lower() in title_text.lower():
                title_lbl = create_highlighted_label(
                    hdr_row,
                    text=title_text,
                    query=query.strip(),
                    font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
                    text_color=COLOR_TEXT_PRIMARY,
                    bg_color=bg,
                    wrap="none",
                    on_click=lambda e, s=snip: self.select_snippet(s),
                    scroll_frame=self.list_scroll,
                )
            else:
                title_lbl = ctk.CTkLabel(hdr_row, text=title_text, font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD), anchor="w")
                title_lbl.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))
            title_lbl.pack(side="left", fill="x", expand=True)

            cat_lbl = ctk.CTkLabel(hdr_row, text=snip.category, font=ctk.CTkFont(size=FONT_SIZE_XS), text_color=COLOR_PILL_ACTIVE)
            cat_lbl.pack(side="right")

            preview_str = snip.content.replace("\n", " ")[:SNIPPET_PREVIEW_MAX_LEN] + "..." if len(snip.content) > SNIPPET_PREVIEW_MAX_LEN else snip.content.replace("\n", " ")
            if query and query.strip() and query.strip().lower() in preview_str.lower():
                body_lbl = create_highlighted_label(
                    card,
                    text=preview_str,
                    query=query.strip(),
                    font=ctk.CTkFont(size=FONT_SIZE_SM),
                    text_color=COLOR_SNIPPET_PREVIEW_TEXT,
                    bg_color=bg,
                    wrap="word",
                    on_click=lambda e, s=snip: self.select_snippet(s),
                    scroll_frame=self.list_scroll,
                )
            else:
                body_lbl = ctk.CTkLabel(card, text=preview_str, font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_SNIPPET_PREVIEW_TEXT, anchor="w")
                body_lbl.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))
            body_lbl.pack(fill="x", padx=PAD_MD, pady=(PAD_NONE, CORNER_RADIUS_MD))

            bind_mouse_wheel_to_canvas(card, self.list_scroll)

    def select_snippet(self, snippet: Snippet):
        self.selected_snippet = snippet
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", snippet.content)
        self.insert_btn.configure(state="normal")
        self.refresh_snippet_list()

    def on_click_insert(self):
        if self.selected_snippet:
            self.on_snippet_selected(self.selected_snippet.content)
            self.destroy()

