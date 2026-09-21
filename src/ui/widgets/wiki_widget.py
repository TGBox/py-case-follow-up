import webbrowser
import customtkinter as ctk

from constants import (
    BORDER_WIDTH_CARD,
    BTN_WIDTH_WIKI_SYNC,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_DANGER,
    COLOR_MUTED_LABEL,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_WIKI_LINK,
    COLOR_WIKI_SNIPPET,
    CORNER_RADIUS_MD,
    CURSOR_HAND,
    DEBOUNCE_KEY_WIKI_SEARCH,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_WEIGHT_BOLD,
    ICON_DOC,
    ICON_SUCCESS,
    ICON_WARNING,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_XS,
    SEARCH_DEBOUNCE_MS,
    WIKI_SNIPPET_WRAP_LENGTH,
)
from services.i18n_service import tr
from services.wiki_sync_service import WikiSyncService
from utils.ui_utils import bind_mouse_wheel_to_canvas, create_highlighted_label, debounce


class WikiWidget(ctk.CTkFrame):
    def __init__(self, parent, wiki_service: WikiSyncService):
        super().__init__(parent)
        self.wiki_service = wiki_service
        self.create_widgets()

    def create_widgets(self):
        # Header & Sync Button
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_SM + 1))

        self.hdr_lbl = ctk.CTkLabel(
            top_frame,
            text=tr("wiki.header", "BookStack Offline Wiki"),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
        )
        self.hdr_lbl.pack(side="left")

        self.sync_btn = ctk.CTkButton(
            top_frame,
            text=tr("wiki.sync_btn", "🔄 Wiki Sync"),
            command=self.on_sync_wiki,
            width=BTN_WIDTH_WIKI_SYNC,
        )
        self.sync_btn.pack(side="right")

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(0, PAD_SM + 1))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=tr("wiki.search_placeholder", "📖 Wiki durchsuchen (z. B. ERR_DB_902)..."),
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)

        # Status
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=PAD_LG + 3, pady=(0, PAD_XS))

        # Scrollable Results Container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_SM + 1, pady=PAD_SM + 1)

    def refresh_ui_labels(self):
        if hasattr(self, "hdr_lbl"):
            self.hdr_lbl.configure(text=tr("wiki.header", "BookStack Offline Wiki"))
        if hasattr(self, "sync_btn"):
            self.sync_btn.configure(text=tr("wiki.sync_btn", "🔄 Wiki Sync"))
        if hasattr(self, "search_entry"):
            self.search_entry.configure(placeholder_text=tr("wiki.search_placeholder", "📖 Wiki durchsuchen (z. B. ERR_DB_902)..."))
        if hasattr(self, "search_entry") and self.search_entry.get().strip():
            self.on_search()
        elif hasattr(self, "status_label"):
            self.status_label.configure(text=tr("wiki.enter_query", "Bitte Suchbegriff eingeben."))

    def focus_search(self):
        self.search_entry.focus_set()

    def _on_search_keyrelease(self, event=None):
        """Debounces the SQLite wiki search instead of querying on every key press."""
        debounce(self, DEBOUNCE_KEY_WIKI_SEARCH, SEARCH_DEBOUNCE_MS, self.on_search)

    def on_search(self):
        query = self.search_entry.get().strip()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not query:
            self.status_label.configure(text=tr("wiki.enter_query", "Bitte Suchbegriff eingeben."))
            return

        results = self.wiki_service.search(query)
        self.status_label.configure(text=tr("wiki.articles_found_count", "{count} Wiki-Artikel gefunden", count=len(results)))

        if not results:
            ctk.CTkLabel(self.scroll_frame, text=tr("wiki.no_results", "Keine treffenden Artikel im Offline-Index.")).pack(pady=PAD_MD + PAD_XS)
            return

        for item in results:
            card_bg = COLOR_CARD_BG
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=card_bg,
                corner_radius=CORNER_RADIUS_MD,
                border_width=BORDER_WIDTH_CARD,
                border_color=COLOR_CARD_BORDER,
                cursor=CURSOR_HAND,
            )
            card.pack(fill="x", pady=PAD_SM, padx=PAD_SM)

            url = item.get("url", "")
            on_click = (lambda e, u=url: webbrowser.open(u)) if url else None
            if on_click:
                card.bind("<Button-1>", on_click)

            title_text = f"{ICON_DOC} {item['title']}"
            if query and query.lower() in title_text.lower():
                title_lbl = create_highlighted_label(
                    card,
                    text=title_text,
                    query=query,
                    font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY),
                    text_color=COLOR_WIKI_LINK,
                    bg_color=card_bg,
                    wrap="none",
                    on_click=on_click,
                    scroll_frame=self.scroll_frame,
                )
            else:
                title_lbl = ctk.CTkLabel(
                    card,
                    text=title_text,
                    anchor="w",
                    font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY),
                    text_color=COLOR_WIKI_LINK,
                )
                if on_click:
                    title_lbl.bind("<Button-1>", on_click)
            title_lbl.pack(fill="x", padx=PAD_MD, pady=(PAD_MD - PAD_XS, PAD_XS))

            snip_text = item.get("snippet", "")
            if query and query.lower() in snip_text.lower():
                snip_lbl = create_highlighted_label(
                    card,
                    text=snip_text,
                    query=query,
                    font=ctk.CTkFont(size=FONT_SIZE_SM),
                    text_color=COLOR_WIKI_SNIPPET,
                    bg_color=card_bg,
                    wrap="word",
                    on_click=on_click,
                    scroll_frame=self.scroll_frame,
                )
            else:
                snip_lbl = ctk.CTkLabel(
                    card,
                    text=snip_text,
                    anchor="w",
                    justify="left",
                    font=ctk.CTkFont(size=FONT_SIZE_SM),
                    text_color=COLOR_WIKI_SNIPPET,
                    wraplength=WIKI_SNIPPET_WRAP_LENGTH,
                )
                if on_click:
                    snip_lbl.bind("<Button-1>", on_click)
            snip_lbl.pack(fill="x", padx=PAD_MD, pady=(0, PAD_MD - PAD_XS))

            bind_mouse_wheel_to_canvas(card, self.scroll_frame)

    def on_sync_wiki(self):
        if getattr(self, "_is_syncing", False):
            return
        self._is_syncing = True
        self.status_label.configure(text=tr("wiki.syncing", "⏳ Synchronisiere Wiki im Hintergrund..."), text_color=COLOR_WARNING)

        def _completion_cb(success: bool, msg: str):
            self.after(0, lambda: self.on_sync_finished(success, msg))

        self.wiki_service.sync_from_bookstack_async(callback=_completion_cb)

    def on_sync_finished(self, success: bool, msg: str):
        self._is_syncing = False
        if success:
            self.status_label.configure(text=f"{ICON_SUCCESS} {msg}", text_color=COLOR_SUCCESS)
        else:
            self.status_label.configure(text=f"{ICON_WARNING} {msg}", text_color=COLOR_DANGER)
        self.on_search()
