import customtkinter as ctk
from typing import Callable
from models.profile import UserProfile
from services.storage_service import StorageService


class TagManagementDialog(ctk.CTkToplevel):
    def __init__(self, parent, profile: UserProfile, storage_service: StorageService, on_tags_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_tags_updated = on_tags_updated

        self.title("🏷️ System-Tags Verwaltung")
        self.geometry("560x500")
        self.minsize(480, 400)
        from utils.ui_utils import center_window
        center_window(self, 560, 500)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.render_tags_list()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="🏷️ System-Tags Verwalten", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # Add New Tag Box
        add_box = ctk.CTkFrame(main_frame)
        add_box.pack(fill="x", pady=(0, 10), padx=5)

        ctk.CTkLabel(add_box, text="Neuen Tag erstellen:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))

        add_row = ctk.CTkFrame(add_box, fg_color="transparent")
        add_row.pack(fill="x", padx=10, pady=(0, 10))

        self.new_tag_entry = ctk.CTkEntry(add_row, placeholder_text="z. B. Schnittstelle, Abrechnung, Telematik...")
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_btn = ctk.CTkButton(add_row, text="+ Tag Hinzufügen", command=self.on_add_tag, fg_color="forestgreen", width=140)
        add_btn.pack(side="right")

        # Tags List Scrollable
        ctk.CTkLabel(main_frame, text="Verfügbare Tags:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(5, 2))

        self.tags_scroll = ctk.CTkScrollableFrame(main_frame)
        self.tags_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # Status & Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(btn_frame, text="", text_color="green")
        self.status_lbl.pack(side="left")

        close_btn = ctk.CTkButton(btn_frame, text="Schließen", command=self.destroy, width=120)
        close_btn.pack(side="right")

    def render_tags_list(self):
        for w in self.tags_scroll.winfo_children():
            w.destroy()

        if not self.profile.available_tags:
            ctk.CTkLabel(self.tags_scroll, text="Keine Tags vorhanden.", text_color="gray").pack(pady=20)
            return

        for idx, tag in enumerate(self.profile.available_tags):
            row = ctk.CTkFrame(self.tags_scroll, fg_color="gray20" if idx % 2 == 0 else "transparent")
            row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(row, text=f"🏷️  {tag}", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(side="left", padx=10, expand=True, fill="x")

            del_btn = ctk.CTkButton(row, text="🗑️ Löschen", fg_color="red", hover_color="darkred", width=90, command=lambda t=tag: self.on_delete_tag(t))
            del_btn.pack(side="right", padx=5, pady=3)

    def on_add_tag(self):
        new_tag = self.new_tag_entry.get().strip()
        if not new_tag:
            self.status_lbl.configure(text="⚠️ Tag Name darf nicht leer sein!", text_color="red")
            return

        if new_tag in self.profile.available_tags:
            self.status_lbl.configure(text="⚠️ Tag existiert bereits!", text_color="red")
            return

        self.profile.available_tags.append(new_tag)
        self.storage_service.save_profile(self.profile)
        self.new_tag_entry.delete(0, "end")
        self.status_lbl.configure(text="✅ Tag erfolgreich hinzugefügt!", text_color="green")

        self.render_tags_list()
        if self.on_tags_updated:
            self.on_tags_updated()

    def on_delete_tag(self, tag_name: str):
        if tag_name in self.profile.available_tags:
            self.profile.available_tags.remove(tag_name)
            self.storage_service.save_profile(self.profile)
            self.status_lbl.configure(text=f"✅ Tag '{tag_name}' gelöscht.", text_color="green")
            self.render_tags_list()
            if self.on_tags_updated:
                self.on_tags_updated()
