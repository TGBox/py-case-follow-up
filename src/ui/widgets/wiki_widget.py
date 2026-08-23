import customtkinter as ctk
import webbrowser
from src.services.wiki_sync_service import WikiSyncService


class WikiWidget(ctk.CTkFrame):
    def __init__(self, parent, wiki_service: WikiSyncService):
        super().__init__(parent)
        self.wiki_service = wiki_service
        self.create_widgets()

    def create_widgets(self):
        # Header & Sync Button
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_frame, text="BookStack Offline Wiki", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        sync_btn = ctk.CTkButton(top_frame, text="🔄 Wiki Sync", command=self.on_sync_wiki, width=100)
        sync_btn.pack(side="right")

        # Search Bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="📖 Wiki durchsuchen (z. B. ERR_DB_902)...")
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.on_search())

        # Status
        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="gray70", anchor="w")
        self.status_label.pack(fill="x", padx=15, pady=(0, 2))

        # Scrollable Results Container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def focus_search(self):
        self.search_entry.focus_set()

    def on_search(self):
        query = self.search_entry.get().strip()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not query:
            self.status_label.configure(text="Bitte Suchbegriff eingeben.")
            return

        results = self.wiki_service.search(query)
        self.status_label.configure(text=f"{len(results)} Wiki-Artikel gefunden")

        if not results:
            ctk.CTkLabel(self.scroll_frame, text="Keine treffenden Artikel im Offline-Index.").pack(pady=10)
            return

        for item in results:
            card = ctk.CTkFrame(self.scroll_frame, fg_color="gray20", corner_radius=6, cursor="hand2")
            card.pack(fill="x", pady=4, padx=4)

            url = item.get("url", "")
            if url:
                card.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

            title_lbl = ctk.CTkLabel(card, text=f"📄 {item['title']}", anchor="w", font=ctk.CTkFont(weight="bold", size=12), text_color="dodgerblue")
            title_lbl.pack(fill="x", padx=8, pady=(6, 2))
            if url:
                title_lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

            snip_lbl = ctk.CTkLabel(card, text=item.get("snippet", ""), anchor="w", justify="left", font=ctk.CTkFont(size=11), text_color="gray80", wraplength=280)
            snip_lbl.pack(fill="x", padx=8, pady=(0, 6))
            if url:
                snip_lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

    def on_sync_wiki(self):
        self.status_label.configure(text="⏳ Synchronisiere mit BookStack...", text_color="orange")
        self.update()

        success, msg = self.wiki_service.sync_from_bookstack()
        if success:
            self.status_label.configure(text=f"✅ {msg}", text_color="green")
        else:
            self.status_label.configure(text=f"⚠️ {msg}", text_color="red")
        self.on_search()
