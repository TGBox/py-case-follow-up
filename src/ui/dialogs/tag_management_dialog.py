import customtkinter as ctk
from collections.abc import Callable

from constants import (
    BTN_WIDTH_ACTION,
    BTN_WIDTH_CLOSE,
    BTN_WIDTH_QUIT,
    BTN_WIDTH_TAG_APPLY,
    COLOR_BTN_ADD_TAG,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_PILL_ACTIVE,
    COLOR_ROW_ALT,
    COLOR_SUCCESS,
    COLOR_USER_BTN_TEXT,
    CORNER_RADIUS_NONE,
    DEBOUNCE_KEY_MODULE_SEARCH,
    DEBOUNCE_KEY_TAG_SEARCH,
    DELAY_SCROLL_RESET_LONG_MS,
    DELAY_SCROLL_RESET_SHORT_MS,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_TAG_MGMT,
    DIALOG_TITLES,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_TITLE_SM,
    FONT_WEIGHT_BOLD,
    HEIGHT_HEADER_BAR,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XL,
    PAD_XS,
    SEARCH_DEBOUNCE_MS,
)
from models.profile import UserProfile
from services.storage_service import StorageService
from ui.dialogs.base_dialog import BaseDialog
from utils.ui_utils import (
    bind_mouse_wheel_to_canvas,
    create_highlighted_label,
    debounce,
    enable_auto_hiding_scrollbar,
)

#: Key/default pairs for the two tabs, and the program values the caller uses
#: to preselect one. Same order, so the tab position maps onto a value without
#: ever comparing the translated tab caption.
TAG_TAB_CHOICES = [
    ("tag_mgmt.tab_tags", "🏷 Allgemeine Tags"),
    ("tag_mgmt.tab_modules", "🧩 Programmbereiche"),
]
TAG_TAB_KEYS = ("tags", "modules")


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
            min_size=DIALOG_MIN_SIZE_TAG_MGMT,
            title_factory=lambda: DIALOG_TITLES["tag_mgmt"],
        )

        self.create_widgets()
        # Select by position: the captions are translated, so the German ones
        # that used to stand here matched nothing once the UI ran in EN or SV.
        initial_index = TAG_TAB_KEYS.index(initial_tab) if initial_tab in TAG_TAB_KEYS else 0
        self.tabview.set(self._tab_names[initial_index])

        self.render_tags_list()
        self.render_modules_list()

    def create_widgets(self):
        from services.i18n_service import tr

        # Header Bar
        top_bar = ctk.CTkFrame(self, height=HEIGHT_HEADER_BAR, corner_radius=CORNER_RADIUS_NONE)
        top_bar.pack(fill="x", side="top", padx=PAD_MD + PAD_XS, pady=(PAD_MD + PAD_XS, PAD_CONTAINER))

        self.register_i18n(ctk.CTkLabel(top_bar, text=tr("tag_mgmt.header", "🏷 System-Tags & Programmbereiche"), font=ctk.CTkFont(size=FONT_SIZE_TITLE_SM, weight=FONT_WEIGHT_BOLD)), "tag_mgmt.header", "🏷 System-Tags & Programmbereiche").pack(side="left", padx=PAD_MD + PAD_XS)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_XL - 1, pady=(PAD_CONTAINER, PAD_MD + PAD_XS))

        # Footer Status & Close (PINNED AT BOTTOM)
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(PAD_CONTAINER, PAD_NONE))

        self.status_lbl = ctk.CTkLabel(btn_frame, text="", text_color=COLOR_SUCCESS)
        self.status_lbl.pack(side="left")

        close_btn = self.register_i18n(ctk.CTkButton(btn_frame, text=tr("common.close", "Schließen"), command=self.destroy, width=BTN_WIDTH_CLOSE), "common.close", "Schließen")
        close_btn.pack(side="right")

        # Tabview (Fills remaining space above footer)
        self.tabview = ctk.CTkTabview(main_frame, command=self._on_tab_changed)
        self.tabview.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_CONTAINER))

        self._tab_names = [tr(key, default) for key, default in TAG_TAB_CHOICES]
        tab_tags = self.tabview.add(self._tab_names[0])
        tab_modules = self.tabview.add(self._tab_names[1])

        # --- TAB 1: ALLGEMEINE TAGS ---
        # Search & Add Box
        add_box1 = ctk.CTkFrame(tab_tags)
        add_box1.pack(fill="x", pady=PAD_CONTAINER, padx=PAD_CONTAINER)

        self.search_tag_entry = self.register_i18n(ctk.CTkEntry(add_box1, placeholder_text=tr("tag_mgmt.search_tags_placeholder", "🔍 Tags durchsuchen...")), "tag_mgmt.search_tags_placeholder", "🔍 Tags durchsuchen...", attr="placeholder_text")
        self.search_tag_entry.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD, PAD_SM))
        self.search_tag_entry.bind("<KeyRelease>", lambda e: debounce(self, DEBOUNCE_KEY_TAG_SEARCH, SEARCH_DEBOUNCE_MS, self.render_tags_list))

        add_row1 = ctk.CTkFrame(add_box1, fg_color="transparent")
        add_row1.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_SM, PAD_MD))

        self.new_tag_entry = self.register_i18n(ctk.CTkEntry(add_row1, placeholder_text=tr("tag_mgmt.new_tag_placeholder", "Neuen Tag erstellen (z. B. Schnittstelle)...")), "tag_mgmt.new_tag_placeholder", "Neuen Tag erstellen (z. B. Schnittstelle)...", attr="placeholder_text")
        self.new_tag_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_MD + PAD_XS))

        add_btn1 = self.register_i18n(ctk.CTkButton(add_row1, text=tr("tag_mgmt.add_tag_btn", "+ Tag Hinzufügen"), command=self.on_add_tag, fg_color=COLOR_BTN_ADD_TAG, width=BTN_WIDTH_ACTION), "tag_mgmt.add_tag_btn", "+ Tag Hinzufügen")
        add_btn1.pack(side="right")

        self.tags_scroll = ctk.CTkScrollableFrame(tab_tags)
        self.tags_scroll.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=PAD_CONTAINER)
        enable_auto_hiding_scrollbar(self.tags_scroll)

        # --- TAB 2: PROGRAMMBEREICHE ---
        add_box2 = ctk.CTkFrame(tab_modules)
        add_box2.pack(fill="x", pady=PAD_CONTAINER, padx=PAD_CONTAINER)

        self.search_mod_entry = self.register_i18n(ctk.CTkEntry(add_box2, placeholder_text=tr("tag_mgmt.search_modules_placeholder", "🔍 Programmbereiche durchsuchen...")), "tag_mgmt.search_modules_placeholder", "🔍 Programmbereiche durchsuchen...", attr="placeholder_text")
        self.search_mod_entry.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_MD, PAD_SM))
        self.search_mod_entry.bind("<KeyRelease>", lambda e: debounce(self, DEBOUNCE_KEY_MODULE_SEARCH, SEARCH_DEBOUNCE_MS, self.render_modules_list))

        add_row2 = ctk.CTkFrame(add_box2, fg_color="transparent")
        add_row2.pack(fill="x", padx=PAD_MD + PAD_XS, pady=(PAD_SM, PAD_MD))

        self.new_mod_entry = self.register_i18n(ctk.CTkEntry(add_row2, placeholder_text=tr("tag_mgmt.new_module_placeholder", "Neuen Programmbereich erstellen (z. B. Rezeptdruck)...")), "tag_mgmt.new_module_placeholder", "Neuen Programmbereich erstellen (z. B. Rezeptdruck)...", attr="placeholder_text")
        self.new_mod_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_MD + PAD_XS))

        add_btn2 = self.register_i18n(ctk.CTkButton(add_row2, text=tr("tag_mgmt.add_module_btn", "+ Bereich Hinzufügen"), command=self.on_add_module, fg_color=COLOR_PILL_ACTIVE, width=BTN_WIDTH_TAG_APPLY), "tag_mgmt.add_module_btn", "+ Bereich Hinzufügen")
        add_btn2.pack(side="right")

        self.modules_scroll = ctk.CTkScrollableFrame(tab_modules)
        self.modules_scroll.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=PAD_CONTAINER)
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
        self.after(DELAY_SCROLL_RESET_SHORT_MS, _do_reset)
        self.after(DELAY_SCROLL_RESET_LONG_MS, _do_reset)

    def _on_tab_changed(self):
        # CTkTabview identifies a tab by its caption, which is translated, so
        # the position in self._tab_names is what stays stable across languages.
        try:
            index = self._tab_names.index(self.tabview.get())
        except ValueError:
            index = 0
        if TAG_TAB_KEYS[index] == "modules":
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
            self.register_i18n(ctk.CTkLabel(self.tags_scroll, text=tr("tag_mgmt.no_tags", "Keine Tags gefunden."), text_color=COLOR_MUTED_LABEL), "tag_mgmt.no_tags", "Keine Tags gefunden.").pack(pady=PAD_2XL)
        else:
            for idx, tag in enumerate(tags):
                row_bg = COLOR_ROW_ALT if idx % 2 == 0 else "transparent"
                row = ctk.CTkFrame(self.tags_scroll, fg_color=row_bg)
                row.pack(fill="x", pady=PAD_XS, padx=PAD_CONTAINER)

                del_btn = self.register_i18n(ctk.CTkButton(row, text=tr("common.delete", "🗑 Löschen"), fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, width=BTN_WIDTH_QUIT, command=lambda t=tag: self.confirm_delete_tag(t)), "common.delete", "🗑 Löschen")
                del_btn.pack(side="right", padx=PAD_CONTAINER, pady=PAD_SM - 1)

                tag_text = f"🏷  {tag}"
                if raw_query and query in tag.lower():
                    lbl = create_highlighted_label(
                        row,
                        text=tag_text,
                        query=raw_query,
                        font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight=FONT_WEIGHT_BOLD),
                        text_color=COLOR_USER_BTN_TEXT,
                        bg_color=row_bg,
                        wrap="none",
                        scroll_frame=self.tags_scroll,
                    )
                else:
                    lbl = ctk.CTkLabel(row, text=tag_text, font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight=FONT_WEIGHT_BOLD), anchor="w")
                lbl.pack(side="left", padx=PAD_MD + PAD_XS, expand=True, fill="x")

                bind_mouse_wheel_to_canvas(row, self.tags_scroll)

        self._reset_scroll_to_top(self.tags_scroll)

    def on_add_tag(self):
        from services.i18n_service import tr

        new_tag = self.new_tag_entry.get().strip()
        if not new_tag:
            self.status_lbl.configure(text=tr("tag_mgmt.tag_empty", "⚠ Tag Name darf nicht leer sein!"), text_color=COLOR_DANGER)
            return

        if new_tag in self.profile.available_tags:
            self.status_lbl.configure(text=tr("tag_mgmt.tag_exists", "⚠ Tag existiert bereits!"), text_color=COLOR_DANGER)
            return

        self.profile.available_tags.append(new_tag)
        self.storage_service.save_profile(self.profile)
        self.new_tag_entry.delete(0, "end")
        self.status_lbl.configure(text=tr("tag_mgmt.tag_added", "✅ Tag erfolgreich hinzugefügt!"), text_color=COLOR_SUCCESS)

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
            self.status_lbl.configure(text=tr("tag_mgmt.tag_deleted", "✅ Tag '{name}' gelöscht.", name=tag_name), text_color=COLOR_SUCCESS)
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
            self.register_i18n(ctk.CTkLabel(self.modules_scroll, text=tr("tag_mgmt.no_modules", "Keine Programmbereiche gefunden."), text_color=COLOR_MUTED_LABEL), "tag_mgmt.no_modules", "Keine Programmbereiche gefunden.").pack(pady=PAD_2XL)
        else:
            for idx, mod in enumerate(mods):
                row_bg = COLOR_ROW_ALT if idx % 2 == 0 else "transparent"
                row = ctk.CTkFrame(self.modules_scroll, fg_color=row_bg)
                row.pack(fill="x", pady=PAD_XS, padx=PAD_CONTAINER)

                del_btn = self.register_i18n(ctk.CTkButton(row, text=tr("common.delete", "🗑 Löschen"), fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, width=BTN_WIDTH_QUIT, command=lambda m=mod: self.confirm_delete_module(m)), "common.delete", "🗑 Löschen")
                del_btn.pack(side="right", padx=PAD_CONTAINER, pady=PAD_SM - 1)

                mod_text = f"🧩  {mod}"
                if raw_query and query in mod.lower():
                    lbl = create_highlighted_label(
                        row,
                        text=mod_text,
                        query=raw_query,
                        font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight=FONT_WEIGHT_BOLD),
                        text_color=COLOR_USER_BTN_TEXT,
                        bg_color=row_bg,
                        wrap="none",
                        scroll_frame=self.modules_scroll,
                    )
                else:
                    lbl = ctk.CTkLabel(row, text=mod_text, font=ctk.CTkFont(size=FONT_SIZE_CONFIRM, weight=FONT_WEIGHT_BOLD), anchor="w")
                lbl.pack(side="left", padx=PAD_MD + PAD_XS, expand=True, fill="x")

                bind_mouse_wheel_to_canvas(row, self.modules_scroll)

        self._reset_scroll_to_top(self.modules_scroll)

    def on_add_module(self):
        from services.i18n_service import tr
        new_mod = self.new_mod_entry.get().strip()
        if not new_mod:
            self.status_lbl.configure(text=tr("tag_mgmt.module_empty", "⚠ Programmbereich darf nicht leer sein!"), text_color=COLOR_DANGER)
            return

        if new_mod in self.profile.available_module_tags:
            self.status_lbl.configure(text=tr("tag_mgmt.module_exists", "⚠ Programmbereich existiert bereits!"), text_color=COLOR_DANGER)
            return

        self.profile.available_module_tags.append(new_mod)
        self.storage_service.save_profile(self.profile)
        self.new_mod_entry.delete(0, "end")
        self.status_lbl.configure(text=tr("tag_mgmt.module_added", "✅ Programmbereich erfolgreich hinzugefügt!"), text_color=COLOR_SUCCESS)

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
            self.status_lbl.configure(text=tr("tag_mgmt.module_deleted", "✅ Programmbereich '{name}' gelöscht.", name=mod_name), text_color=COLOR_SUCCESS)
            self.render_modules_list()
            if self.on_tags_updated:
                self.on_tags_updated()
