import customtkinter as ctk
from typing import Callable
from models.snippet import Snippet
from services.snippet_service import SnippetService


class SnippetPickerDialog(ctk.CTkToplevel):
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

        self.title("🧩 Textbaustein auswählen & einfügen")
        self.geometry("780x560")
        self.minsize(680, 480)

        from utils.ui_utils import center_window
        center_window(self, 780, 560)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.refresh_snippet_list()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header & Search Controls
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            hdr_frame, placeholder_text="🔍 Textbaustein suchen...", width=320
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_snippet_list())

        self.cat_combo = ctk.CTkOptionMenu(
            hdr_frame,
            values=self.service.get_categories(),
            command=lambda v: self.refresh_snippet_list(),
            width=160,
        )
        self.cat_combo.pack(side="right")

        # 2-Column Content Layout (Left: Snippets List, Right: Content Preview)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1, minsize=300)
        content_frame.grid_columnconfigure(1, weight=1, minsize=340)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left List Container
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.list_scroll = ctk.CTkScrollableFrame(content_frame)
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        enable_auto_hiding_scrollbar(self.list_scroll)

        # Right Preview Container
        preview_box = ctk.CTkFrame(content_frame)
        preview_box.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(preview_box, text="Vorschau des Textbausteins:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 4))
        
        self.preview_textbox = ctk.CTkTextbox(preview_box)
        self.preview_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom Action Bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))

        self.insert_btn = ctk.CTkButton(
            btn_frame,
            text="🧩 Ausgewählten Baustein einfügen",
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.on_click_insert,
            state="disabled",
        )
        self.insert_btn.pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_frame,
            text="Abbrechen",
            fg_color="gray50",
            command=self.destroy,
            width=90,
        ).pack(side="right")

    def refresh_snippet_list(self):
        query = self.search_entry.get()
        cat = self.cat_combo.get()
        snippets = self.service.search_snippets(query=query, category=cat)

        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        if not snippets:
            ctk.CTkLabel(self.list_scroll, text="Keine Textbausteine gefunden.").pack(pady=20)
            return

        for snip in snippets:
            is_sel = self.selected_snippet and self.selected_snippet.snippet_id == snip.snippet_id
            bg = ("gray80", "gray25") if is_sel else ("gray90", "gray15")

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, corner_radius=6, cursor="hand2")
            card.pack(fill="x", pady=4, padx=4)
            card.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            hdr_row = ctk.CTkFrame(card, fg_color="transparent")
            hdr_row.pack(fill="x", padx=8, pady=(6, 2))
            hdr_row.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            title_lbl = ctk.CTkLabel(hdr_row, text=snip.title, font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            title_lbl.pack(side="left", fill="x", expand=True)
            title_lbl.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            cat_lbl = ctk.CTkLabel(hdr_row, text=snip.category, font=ctk.CTkFont(size=10), text_color="dodgerblue")
            cat_lbl.pack(side="right")

            preview_str = snip.content.replace("\n", " ")[:60] + "..." if len(snip.content) > 60 else snip.content.replace("\n", " ")
            body_lbl = ctk.CTkLabel(card, text=preview_str, font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"), anchor="w")
            body_lbl.pack(fill="x", padx=8, pady=(0, 6))
            body_lbl.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

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
