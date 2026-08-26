import customtkinter as ctk
from typing import Callable
from models.snippet import Snippet
from services.snippet_service import SnippetService
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES, STATUS_MESSAGES, LABEL_SNIPPET_SHORTCUT_FIELD, HOTKEY_RECORDER_BUTTON


class SnippetManagementDialog(ctk.CTkToplevel):
    """Management dialog for adding, editing, and removing text snippets."""

    def __init__(self, parent, snippet_service: SnippetService, on_snippets_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.service = snippet_service
        self.on_snippets_updated = on_snippets_updated
        self.selected_snippet: Snippet | None = None

        w, h = DIALOG_DIMENSIONS["snippet_mgmt"]
        self.title(DIALOG_TITLES["snippet_mgmt"])
        self.geometry(f"{w}x{h}")
        self.minsize(720, 500)

        from utils.ui_utils import center_window
        center_window(self, w, h)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(hdr_frame, text="📝 Textbaustein-Bibliothek verwalten", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkButton(
            hdr_frame,
            text="+ Neuer Textbaustein",
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.on_click_new,
        ).pack(side="right")

        # 2-Column Content (Left: List, Right: Edit Form)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1, minsize=320)
        content_frame.grid_columnconfigure(1, weight=1, minsize=380)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left List Container
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.list_scroll = ctk.CTkScrollableFrame(content_frame)
        self.list_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        enable_auto_hiding_scrollbar(self.list_scroll)

        # Right Edit Form Container
        self.form_box = ctk.CTkScrollableFrame(content_frame)
        self.form_box.grid(row=0, column=1, sticky="nsew")
        enable_auto_hiding_scrollbar(self.form_box)

        ctk.CTkLabel(self.form_box, text="Titel:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.title_entry = ctk.CTkEntry(self.form_box, placeholder_text="z. B. 📸 Rückfrage: Screenshots")
        self.title_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.form_box, text="Kategorie:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.category_entry = ctk.CTkEntry(self.form_box, placeholder_text="z. B. Rückfrage, Anleitung, SQL")
        self.category_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.form_box, text="Inhalt / Baustein-Text:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.content_textbox = ctk.CTkTextbox(self.form_box, height=180)
        self.content_textbox.pack(fill="x", expand=True, pady=(0, 8))

        ctk.CTkLabel(self.form_box, text="Tags (kommagetrennt):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.tags_entry = ctk.CTkEntry(self.form_box, placeholder_text="z. B. fehler, sql, anleitung")
        self.tags_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.form_box, text=LABEL_SNIPPET_SHORTCUT_FIELD, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        sc_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        sc_row.pack(fill="x", pady=(0, 12))

        self.shortcut_entry = ctk.CTkEntry(sc_row, placeholder_text="z. B. <Control-Alt-1>")
        self.shortcut_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        rec_btn = ctk.CTkButton(
            sc_row,
            text=HOTKEY_RECORDER_BUTTON,
            width=110,
            fg_color="gray30",
            hover_color="gray45",
            command=self.open_hotkey_recorder,
        )
        rec_btn.pack(side="right")

        # Status & Action Buttons
        self.status_lbl = ctk.CTkLabel(self.form_box, text="", font=ctk.CTkFont(size=11), text_color="dodgerblue")
        self.status_lbl.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        btn_row.pack(fill="x", pady=(5, 0))

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="💾 Speichern",
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.on_click_save,
        )
        self.save_btn.pack(side="left", padx=(0, 6))

        self.delete_btn = ctk.CTkButton(
            btn_row,
            text="🗑 Löschen",
            fg_color="crimson",
            hover_color="darkred",
            command=self.on_click_delete,
            state="disabled",
        )
        self.delete_btn.pack(side="left")

        # Bottom Close Button
        ctk.CTkButton(
            main_frame,
            text="Schließen",
            fg_color="gray50",
            command=self.destroy,
            width=90,
        ).pack(side="right", pady=(5, 0))

    def open_hotkey_recorder(self):
        from ui.dialogs.profile_settings_dialog import HotkeyRecorderDialog
        def on_recorded(key_str: str):
            self.shortcut_entry.delete(0, "end")
            self.shortcut_entry.insert(0, key_str)
        HotkeyRecorderDialog(self, on_recorded)

    def refresh_list(self):
        snippets = self.service.get_all_snippets()

        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        if not snippets:
            ctk.CTkLabel(self.list_scroll, text="Keine Textbausteine vorhanden.").pack(pady=20)
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

            title_text = f"{snip.title} ⌨ {snip.shortcut}" if snip.shortcut else snip.title
            title_lbl = ctk.CTkLabel(hdr_row, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
            title_lbl.pack(side="left", fill="x", expand=True)
            title_lbl.bind("<Button-1>", lambda e, s=snip: self.select_snippet(s))

            cat_lbl = ctk.CTkLabel(hdr_row, text=snip.category, font=ctk.CTkFont(size=10), text_color="dodgerblue")
            cat_lbl.pack(side="right")

    def select_snippet(self, snippet: Snippet):
        self.selected_snippet = snippet
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, snippet.title)

        self.category_entry.delete(0, "end")
        self.category_entry.insert(0, snippet.category)

        self.content_textbox.delete("1.0", "end")
        self.content_textbox.insert("1.0", snippet.content)

        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(snippet.tags))

        self.shortcut_entry.delete(0, "end")
        if snippet.shortcut:
            self.shortcut_entry.insert(0, snippet.shortcut)

        self.delete_btn.configure(state="normal")
        self.status_lbl.configure(text=f"Ausgewählt: {snippet.snippet_id}", text_color="dodgerblue")
        self.refresh_list()

    def on_click_new(self):
        self.selected_snippet = None
        self.title_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.category_entry.insert(0, "Allgemein")
        self.content_textbox.delete("1.0", "end")
        self.tags_entry.delete(0, "end")
        self.shortcut_entry.delete(0, "end")
        self.delete_btn.configure(state="disabled")
        self.status_lbl.configure(text="Neuer Textbaustein (wird beim Speichern angelegt)", text_color="gray")
        self.refresh_list()

    def on_click_save(self):
        title = self.title_entry.get().strip()
        cat = self.category_entry.get().strip() or "Allgemein"
        content = self.content_textbox.get("1.0", "end-1c").strip()
        tags_raw = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        sc = self.shortcut_entry.get().strip()

        if not title:
            self.status_lbl.configure(text="⚠ Bitte einen Titel eingeben.", text_color="crimson")
            return
        if not content:
            self.status_lbl.configure(text="⚠ Der Inhalt darf nicht leer sein.", text_color="crimson")
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
        self.status_lbl.configure(text=STATUS_MESSAGES["snippet_saved"], text_color="limegreen")
        self.refresh_list()

        if self.on_snippets_updated:
            self.on_snippets_updated()

    def on_click_delete(self):
        if self.selected_snippet:
            self.service.delete_snippet(self.selected_snippet.snippet_id)
            self.status_lbl.configure(text=STATUS_MESSAGES["snippet_deleted"], text_color="limegreen")
            self.on_click_new()
            if self.on_snippets_updated:
                self.on_snippets_updated()
