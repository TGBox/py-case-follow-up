import customtkinter as ctk
from typing import Callable, Any
from models.profile import Colleague
from services.storage_service import StorageService

DEPARTMENTS = ["Support", "Entwicklung", "Technik", "Vertrieb", "Buchhaltung", "Geschäftsführung", "Sonstige"]


class ColleagueManagementDialog(ctk.CTkToplevel):
    """Modal dialog for managing reference employees / colleagues (CRUD)."""

    def __init__(
        self,
        parent,
        storage_service: StorageService,
        on_colleagues_updated: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.storage_service = storage_service
        self.on_colleagues_updated = on_colleagues_updated

        self.title("👥 Mitarbeiter- & Kollegeneinträge")
        self.geometry("920x620")
        self.minsize(780, 500)
        from utils.ui_utils import center_window
        center_window(self, 920, 620)

        self.transient(parent)
        self.grab_set()

        self.colleagues: list[Colleague] = []
        self.filtered_colleagues: list[Colleague] = []
        self.selected_colleague: Colleague | None = None

        self.create_widgets()
        self.load_colleagues()

    def create_widgets(self):
        # Header Bar
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            top_bar,
            text="👥 Mitarbeiter- & Kollegeneinträge",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        new_btn = ctk.CTkButton(
            top_bar,
            text="+ Neuen Mitarbeiter anlegen",
            command=self.on_click_new_colleague,
            fg_color="forestgreen",
            width=180,
        )
        new_btn.pack(side="right", padx=10)

        # Body Frame
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left list panel
        left_frame = ctk.CTkFrame(body_frame, width=320)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(
            left_frame, placeholder_text="🔍 Name, Kürzel, Abteilung..."
        )
        self.search_entry.pack(fill="x", padx=10, pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        self.list_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right editor panel
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        self.form_header_lbl = ctk.CTkLabel(
            right_frame,
            text="Mitarbeiterdetails",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.form_header_lbl.pack(fill="x", padx=15, pady=(12, 8))

        form_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Fields
        ctk.CTkLabel(form_scroll, text="Kürzel / Username *:").pack(anchor="w", pady=(4, 2))
        self.username_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. mmueller")
        self.username_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="Name / Anzeigename *:").pack(anchor="w", pady=(4, 2))
        self.name_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. Max Müller")
        self.name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="Abteilung / Department:").pack(anchor="w", pady=(4, 2))
        self.dept_combo = ctk.CTkOptionMenu(form_scroll, values=DEPARTMENTS)
        self.dept_combo.set(DEPARTMENTS[0])
        self.dept_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="Durchwahl / Telefon:").pack(anchor="w", pady=(4, 2))
        self.ext_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. 4012")
        self.ext_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="E-Mail-Adresse:").pack(anchor="w", pady=(4, 2))
        self.email_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. m.mueller@praxis.de")
        self.email_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="Mobiltelefon:").pack(anchor="w", pady=(4, 2))
        self.mobile_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. 0170 1234567")
        self.mobile_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form_scroll, text="Aufgabengebiet / Notizen:").pack(anchor="w", pady=(4, 2))
        self.notes_entry = ctk.CTkEntry(form_scroll, placeholder_text="z. B. Zuständig für PVS-Schnittstellen...")
        self.notes_entry.pack(fill="x", pady=(0, 15))

        self.err_lbl = ctk.CTkLabel(form_scroll, text="", text_color="red", anchor="w")
        self.err_lbl.pack(fill="x", pady=(0, 5))

        # Bottom Action Bar
        action_bar = ctk.CTkFrame(right_frame, height=45, fg_color="transparent")
        action_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.delete_btn = ctk.CTkButton(
            action_bar,
            text="🗑️ Löschen",
            command=self.on_click_delete,
            fg_color="firebrick",
            hover_color="darkred",
            width=110,
            state="disabled",
        )
        self.delete_btn.pack(side="left")

        self.save_btn = ctk.CTkButton(
            action_bar,
            text="💾 Speichern",
            command=self.on_click_save,
            fg_color="forestgreen",
            width=140,
        )
        self.save_btn.pack(side="right")

    def load_colleagues(self):
        self.colleagues = self.storage_service.load_colleagues()
        self.filter_and_render_list()

    def filter_and_render_list(self):
        q = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""
        if q:
            self.filtered_colleagues = [
                c for c in self.colleagues
                if q in c.name.lower() or q in c.username.lower() or q in c.department.lower() or q in c.notes.lower()
            ]
        else:
            self.filtered_colleagues = list(self.colleagues)

        for child in self.list_scroll.winfo_children():
            child.destroy()

        if not self.filtered_colleagues:
            ctk.CTkLabel(self.list_scroll, text="Keine Einträge gefunden.", text_color="gray").pack(pady=20)
            return

        for col in self.filtered_colleagues:
            is_sel = self.selected_colleague and self.selected_colleague.username == col.username
            bg = ("gray75", "gray35") if is_sel else ("gray85", "gray20")

            card = ctk.CTkFrame(self.list_scroll, fg_color=bg, cursor="hand2")
            card.pack(fill="x", pady=3, padx=2)
            card.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))

            lbl_name = ctk.CTkLabel(card, text=f"{col.name} ({col.username})", font=ctk.CTkFont(weight="bold", size=12), anchor="w")
            lbl_name.pack(fill="x", padx=8, pady=(5, 1))
            lbl_name.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))

            sub_txt = f"🏢 {col.department}"
            if col.extension:
                sub_txt += f" | 📞 {col.extension}"
            lbl_sub = ctk.CTkLabel(card, text=sub_txt, font=ctk.CTkFont(size=10), text_color=("gray40", "gray70"), anchor="w")
            lbl_sub.pack(fill="x", padx=8, pady=(0, 5))
            lbl_sub.bind("<Button-1>", lambda e, c=col: self.select_colleague(c))

    def on_search_changed(self, event=None):
        self.filter_and_render_list()

    def select_colleague(self, col: Colleague | None):
        self.selected_colleague = col
        self.err_lbl.configure(text="")

        if col:
            self.form_header_lbl.configure(text=f"✏️ Bearbeiten: {col.name}")
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, col.username)
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, col.name)
            self.dept_combo.set(col.department if col.department in DEPARTMENTS else DEPARTMENTS[0])
            self.ext_entry.delete(0, "end")
            self.ext_entry.insert(0, col.extension)
            self.email_entry.delete(0, "end")
            self.email_entry.insert(0, col.email)
            self.mobile_entry.delete(0, "end")
            self.mobile_entry.insert(0, col.mobile)
            self.notes_entry.delete(0, "end")
            self.notes_entry.insert(0, col.notes)
            self.delete_btn.configure(state="normal")
        else:
            self.form_header_lbl.configure(text="➕ Neuen Mitarbeiter anlegen")
            self.username_entry.delete(0, "end")
            self.name_entry.delete(0, "end")
            self.dept_combo.set(DEPARTMENTS[0])
            self.ext_entry.delete(0, "end")
            self.email_entry.delete(0, "end")
            self.mobile_entry.delete(0, "end")
            self.notes_entry.delete(0, "end")
            self.delete_btn.configure(state="disabled")

        self.filter_and_render_list()

    def on_click_new_colleague(self):
        self.select_colleague(None)

    def on_click_save(self):
        username = self.username_entry.get().strip()
        name = self.name_entry.get().strip()
        department = self.dept_combo.get()
        extension = self.ext_entry.get().strip()
        email = self.email_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        notes = self.notes_entry.get().strip()

        col = Colleague(
            username=username,
            name=name,
            department=department,
            extension=extension,
            email=email,
            mobile=mobile,
            notes=notes,
        )

        errs = col.validate()
        if errs:
            self.err_lbl.configure(text=f"⚠️ {errs[0]}")
            return

        # Update existing or add new
        existing_idx = next((i for i, c in enumerate(self.colleagues) if c.username.lower() == username.lower()), -1)
        if existing_idx >= 0:
            self.colleagues[existing_idx] = col
        else:
            self.colleagues.append(col)

        self.storage_service.save_colleagues(self.colleagues)
        self.select_colleague(col)

        if self.on_colleagues_updated:
            self.on_colleagues_updated()

    def on_click_delete(self):
        if not self.selected_colleague:
            return
        username_to_del = self.selected_colleague.username
        self.colleagues = [c for c in self.colleagues if c.username != username_to_del]
        self.storage_service.save_colleagues(self.colleagues)
        self.select_colleague(None)

        if self.on_colleagues_updated:
            self.on_colleagues_updated()
