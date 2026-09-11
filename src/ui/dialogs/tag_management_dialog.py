import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from collections.abc import Callable
from models.profile import UserProfile
from services.storage_service import StorageService
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES
from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas


class TagManagementDialog(BaseDialog):
    def __init__(
        self,
        parent,
        profile: UserProfile,
        storage_service: StorageService,
        on_tags_updated: Callable[[], None] | None = None,
        initial_tab: str = "tags",
    ):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_tags_updated = on_tags_updated
        self.initial_tab = initial_tab

        w, h = DIALOG_DIMENSIONS["tag_mgmt"]
        self.setup_window(
            parent,
            DIALOG_TITLES["tag_mgmt"],
            (w, h),
            min_size=(580, 520),

            title_factory=lambda: DIALOG_TITLES["tag_mgmt"],
        )

        self.create_widgets()
        if initial_tab == "modules":
            self.tabview.set("🧩 Programmbereiche")
        else:
            self.tabview.set("🏷 Allgemeine Tags")

        self.render_tags_list()
        self.render_modules_list()

    def create_widgets(self):
        from services.i18n_service import tr

        # Header Bar
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        self.register_i18n(ctk.CTkLabel(top_bar, text=tr("tag_mgmt.header", "🏷 System-Tags & Programmbereiche"), font=ctk.CTkFont(size=16, weight="bold")), "tag_mgmt.header", "🏷 System-Tags & Programmbereiche").pack(side="left", padx=10)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # Footer Status & Close (PINNED AT BOTTOM)
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(5, 0))

        self.status_lbl = ctk.CTkLabel(btn_frame, text="", text_color="green")
        self.status_lbl.pack(side="left")

        close_btn = self.register_i18n(ctk.CTkButton(btn_frame, text=tr("common.close", "Schließen"), command=self.destroy, width=120), "common.close", "Schließen")
        close_btn.pack(side="right")

        # Tabview (Fills remaining space above footer)
        self.tabview = ctk.CTkTabview(main_frame, command=self._on_tab_changed)
        self.tabview.pack(fill="both", expand=True, pady=(0, 5))

        tab_tags = self.tabview.add(tr("tag_mgmt.tab_tags", "🏷 Allgemeine Tags"))
        tab_modules = self.tabview.add(tr("tag_mgmt.tab_modules", "🧩 Programmbereiche"))

        # --- TAB 1: ALLGEMEINE TAGS ---
        # Search & Add Box
        add_box1 = ctk.CTkFrame(tab_tags)
        add_box1.pack(fill="x", pady=5, padx=5)

        self.search_tag_entry = self.register_i18n(ctk.CTkEntry(add_box1, placeholder_text=tr("tag_mgmt.search_tags_placeholder", "🔍 Tags durchsuchen...")), "tag_mgmt.search_tags_placeholder", "🔍 Tags durchsuchen...", attr="placeholder_text")
        self.search_tag_entry.pack(fill="x", padx=10, pady=(8, 4))
        self.search_tag_entry.bind("<KeyRelease>", lambda e: self.render_tags_list())

        add_row1 = ctk.CTkFrame(add_box1, fg_color="transparent")
        add_row1.pack(fill="x", padx=10, pady=(4, 8))

        self.new_tag_entry = self.register_i18n(ctk.CTkEntry(add_row1, placeholder_text=tr("tag_mgmt.new_tag_placeholder", "Neuen Tag erstellen (z. B. Schnittstelle)...")), "tag_mgmt.new_tag_placeholder", "Neuen Tag erstellen (z. B. Schnittstelle)...", attr="placeholder_text")
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_btn1 = self.register_i18n(ctk.CTkButton(add_row1, text=tr("tag_mgmt.add_tag_btn", "+ Tag Hinzufügen"), command=self.on_add_tag, fg_color="forestgreen", width=140), "tag_mgmt.add_tag_btn", "+ Tag Hinzufügen")
        add_btn1.pack(side="right")

        self.tags_scroll = ctk.CTkScrollableFrame(tab_tags)
        self.tags_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        from utils.ui_utils import enable_auto_hiding_scrollbar
        enable_auto_hiding_scrollbar(self.tags_scroll)

        # --- TAB 2: PROGRAMMBEREICHE ---
        add_box2 = ctk.CTkFrame(tab_modules)
        add_box2.pack(fill="x", pady=5, padx=5)

        self.search_mod_entry = self.register_i18n(ctk.CTkEntry(add_box2, placeholder_text=tr("tag_mgmt.search_modules_placeholder", "🔍 Programmbereiche durchsuchen...")), "tag_mgmt.search_modules_placeholder", "🔍 Programmbereiche durchsuchen...", attr="placeholder_text")
        self.search_mod_entry.pack(fill="x", padx=10, pady=(8, 4))
        self.search_mod_entry.bind("<KeyRelease>", lambda e: self.render_modules_list())

        add_row2 = ctk.CTkFrame(add_box2, fg_color="transparent")
        add_row2.pack(fill="x", padx=10, pady=(4, 8))

        self.new_mod_entry = self.register_i18n(ctk.CTkEntry(add_row2, placeholder_text=tr("tag_mgmt.new_module_placeholder", "Neuen Programmbereich erstellen (z. B. Rezeptdruck)...")), "tag_mgmt.new_module_placeholder", "Neuen Programmbereich erstellen (z. B. Rezeptdruck)...", attr="placeholder_text")
        self.new_mod_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_btn2 = self.register_i18n(ctk.CTkButton(add_row2, text=tr("tag_mgmt.add_module_btn", "+ Bereich Hinzufügen"), command=self.on_add_module, fg_color="dodgerblue", width=160), "tag_mgmt.add_module_btn", "+ Bereich Hinzufügen")
        add_btn2.pack(side="right")

        self.modules_scroll = ctk.CTkScrollableFrame(tab_modules)
        self.modules_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        enable_auto_hiding_scrollbar(self.modules_scroll)

    def _reset_scroll_to_top(self, scroll_frame: ctk.CTkScrollableFrame):
        def _do_reset():
            try:
                canvas = getattr(scroll_frame, "_parent_canvas", getattr(scroll_frame, "_canvas", None))
                if canvas:
                    canvas.yview_moveto(0.0)
            except Exception:
                pass
        _do_reset()
        self.after(50, _do_reset)
        self.after(200, _do_reset)

    def _on_tab_changed(self):
        curr = self.tabview.get()
        if "Programmbereiche" in curr:
            self._reset_scroll_to_top(self.modules_scroll)
        else:
            self._reset_scroll_to_top(self.tags_scroll)

    # --- TAGS LOGIC ---
    def render_tags_list(self):
        for w in self.tags_scroll.winfo_children():
            w.destroy()

        raw_query = self.search_tag_entry.get().strip() if hasattr(self, "search_tag_entry") else ""
        query = raw_query.lower()
        tags = [t for t in self.profile.available_tags if query in t.lower()] if query else self.profile.available_tags

        from services.i18n_service import tr

        if not tags:
            self.register_i18n(ctk.CTkLabel(self.tags_scroll, text=tr("tag_mgmt.no_tags", "Keine Tags gefunden."), text_color="gray"), "tag_mgmt.no_tags", "Keine Tags gefunden.").pack(pady=20)
        else:
            for idx, tag in enumerate(tags):
                row_bg = ("gray90", "gray20") if idx % 2 == 0 else "transparent"
                row = ctk.CTkFrame(self.tags_scroll, fg_color=row_bg)
                row.pack(fill="x", pady=2, padx=5)

                tag_text = f"🏷  {tag}"
                if raw_query and query in tag.lower():
                    lbl = create_highlighted_label(
                        row,
                        text=tag_text,
                        query=raw_query,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=("gray10", "gray90"),
                        bg_color=row_bg,
                        wrap="none",
                        scroll_frame=self.tags_scroll,
                    )
                else:
                    lbl = ctk.CTkLabel(row, text=tag_text, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
                lbl.pack(side="left", padx=10, expand=True, fill="x")

                del_btn = self.register_i18n(ctk.CTkButton(row, text=tr("common.delete", "🗑 Löschen"), fg_color="red", hover_color="darkred", width=90, command=lambda t=tag: self.confirm_delete_tag(t)), "common.delete", "🗑 Löschen")
                del_btn.pack(side="right", padx=5, pady=3)

                bind_mouse_wheel_to_canvas(row, self.tags_scroll)

        self._reset_scroll_to_top(self.tags_scroll)

    def on_add_tag(self):
        from services.i18n_service import tr

        new_tag = self.new_tag_entry.get().strip()
        if not new_tag:
            self.status_lbl.configure(text=tr("tag_mgmt.tag_empty", "⚠ Tag Name darf nicht leer sein!"), text_color="red")
            return

        if new_tag in self.profile.available_tags:
            self.status_lbl.configure(text=tr("tag_mgmt.tag_exists", "⚠ Tag existiert bereits!"), text_color="red")
            return

        self.profile.available_tags.append(new_tag)
        self.storage_service.save_profile(self.profile)
        self.new_tag_entry.delete(0, "end")
        self.status_lbl.configure(text=tr("tag_mgmt.tag_added", "✅ Tag erfolgreich hinzugefügt!"), text_color="green")

        self.render_tags_list()
        if self.on_tags_updated:
            self.on_tags_updated()

    def confirm_delete_tag(self, tag_name: str):
        """Asks before removing the tag - this deletion cannot be undone."""
        from services.i18n_service import tr
        from ui.dialogs.confirm_dialog import ask_confirmation
        if ask_confirmation(
            self,
            tr("confirm.delete_tag", "Tag „{name}“ wirklich dauerhaft entfernen?", name=tag_name),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_delete_tag(tag_name)

    def on_delete_tag(self, tag_name: str):
        from services.i18n_service import tr
        if tag_name in self.profile.available_tags:
            self.profile.available_tags.remove(tag_name)
            self.storage_service.save_profile(self.profile)
            self.status_lbl.configure(text=tr("tag_mgmt.tag_deleted", "✅ Tag '{name}' gelöscht.", name=tag_name), text_color="green")
            self.render_tags_list()
            if self.on_tags_updated:
                self.on_tags_updated()

    # --- MODULE TAGS LOGIC ---
    def render_modules_list(self):
        from services.i18n_service import tr

        for w in self.modules_scroll.winfo_children():
            w.destroy()

        raw_query = self.search_mod_entry.get().strip() if hasattr(self, "search_mod_entry") else ""
        query = raw_query.lower()
        mods = [m for m in self.profile.available_module_tags if query in m.lower()] if query else self.profile.available_module_tags

        if not mods:
            self.register_i18n(ctk.CTkLabel(self.modules_scroll, text=tr("tag_mgmt.no_modules", "Keine Programmbereiche gefunden."), text_color="gray"), "tag_mgmt.no_modules", "Keine Programmbereiche gefunden.").pack(pady=20)
        else:
            for idx, mod in enumerate(mods):
                row_bg = ("gray90", "gray20") if idx % 2 == 0 else "transparent"
                row = ctk.CTkFrame(self.modules_scroll, fg_color=row_bg)
                row.pack(fill="x", pady=2, padx=5)

                mod_text = f"🧩  {mod}"
                if raw_query and query in mod.lower():
                    lbl = create_highlighted_label(
                        row,
                        text=mod_text,
                        query=raw_query,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=("gray10", "gray90"),
                        bg_color=row_bg,
                        wrap="none",
                        scroll_frame=self.modules_scroll,
                    )
                else:
                    lbl = ctk.CTkLabel(row, text=mod_text, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
                lbl.pack(side="left", padx=10, expand=True, fill="x")

                del_btn = self.register_i18n(ctk.CTkButton(row, text=tr("common.delete", "🗑 Löschen"), fg_color="red", hover_color="darkred", width=90, command=lambda m=mod: self.confirm_delete_module(m)), "common.delete", "🗑 Löschen")
                del_btn.pack(side="right", padx=5, pady=3)

                bind_mouse_wheel_to_canvas(row, self.modules_scroll)

        self._reset_scroll_to_top(self.modules_scroll)

    def on_add_module(self):
        from services.i18n_service import tr
        new_mod = self.new_mod_entry.get().strip()
        if not new_mod:
            self.status_lbl.configure(text=tr("tag_mgmt.module_empty", "⚠ Programmbereich darf nicht leer sein!"), text_color="red")
            return

        if new_mod in self.profile.available_module_tags:
            self.status_lbl.configure(text=tr("tag_mgmt.module_exists", "⚠ Programmbereich existiert bereits!"), text_color="red")
            return

        self.profile.available_module_tags.append(new_mod)
        self.storage_service.save_profile(self.profile)
        self.new_mod_entry.delete(0, "end")
        self.status_lbl.configure(text=tr("tag_mgmt.module_added", "✅ Programmbereich erfolgreich hinzugefügt!"), text_color="green")

        self.render_modules_list()
        if self.on_tags_updated:
            self.on_tags_updated()

    def confirm_delete_module(self, mod_name: str):
        """Asks before removing the program area - this deletion cannot be undone."""
        from services.i18n_service import tr
        from ui.dialogs.confirm_dialog import ask_confirmation
        if ask_confirmation(
            self,
            tr("confirm.delete_module", "Programmbereich „{name}“ wirklich dauerhaft entfernen?", name=mod_name),
            title=tr("confirm.delete_title", "Löschen bestätigen"),
            confirm_text=tr("confirm.yes_delete", "🗑 Ja, löschen"),
        ):
            self.on_delete_module(mod_name)

    def on_delete_module(self, mod_name: str):
        from services.i18n_service import tr
        if mod_name in self.profile.available_module_tags:
            self.profile.available_module_tags.remove(mod_name)
            self.storage_service.save_profile(self.profile)
            self.status_lbl.configure(text=tr("tag_mgmt.module_deleted", "✅ Programmbereich '{name}' gelöscht.", name=mod_name), text_color="green")
            self.render_modules_list()
            if self.on_tags_updated:
                self.on_tags_updated()
