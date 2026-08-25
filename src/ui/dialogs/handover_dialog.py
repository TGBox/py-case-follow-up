import customtkinter as ctk
from typing import Callable
from models.case import Case
from models.profile import Colleague
from enums import ACTOR_DISPLAY, get_actor_val_from_display, get_actor_display
from constants import DEFAULT_HANDOVER_CHANNELS, DIALOG_DIMENSIONS, DIALOG_TITLES

HANDOVER_CHANNELS = DEFAULT_HANDOVER_CHANNELS


class HandoverDialog(ctk.CTkToplevel):
    """Modal dialog for handing over case responsibility to a department/colleague."""

    def __init__(
        self,
        parent,
        case: Case,
        colleagues: list[Colleague] | None = None,
        on_handover_confirmed: Callable[[str, str, str, str], None] | None = None,
    ):
        super().__init__(parent)
        self.case = case
        self.colleagues = list(colleagues) if colleagues else []
        if not self.colleagues:
            storage = getattr(parent, "storage_service", None)
            if not storage and hasattr(parent, "master"):
                storage = getattr(parent.master, "storage_service", None)
            if storage:
                self.colleagues = storage.load_colleagues()

        self.on_handover_confirmed = on_handover_confirmed

        w, h = DIALOG_DIMENSIONS["handover"]
        self.title(f"{DIALOG_TITLES['handover']} (Fall {case.case_id})")
        self.geometry(f"{w}x{h}")
        self.minsize(520, 460)
        from utils.ui_utils import center_window
        center_window(self, w, h)
        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            main_frame,
            text=f"👤 Zuständigkeit für {self.case.case_id} übergeben",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))

        curr_actor = get_actor_display(self.case.workflow_status.current_actor)
        ctk.CTkLabel(
            main_frame,
            text=f"Aktuelle Zuständigkeit: {curr_actor} | Kunde: {self.case.customer.practice_name}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(anchor="w", pady=(0, 15))

        # 1. New Actor Dropdown
        ctk.CTkLabel(main_frame, text="Neue verantwortliche Stelle *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(4, 2))
        actor_options = list(ACTOR_DISPLAY.values())
        self.actor_combo = ctk.CTkOptionMenu(main_frame, values=actor_options, width=320)
        self.actor_combo.set(curr_actor if curr_actor in actor_options else actor_options[0])
        self.actor_combo.pack(anchor="w", fill="x", pady=(0, 12))

        # 2. Handover Channel / Medium Dropdown
        ctk.CTkLabel(main_frame, text="Art der Weitergabe / Kanal *:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(4, 2))
        self.channel_combo = ctk.CTkOptionMenu(main_frame, values=HANDOVER_CHANNELS, width=320)
        self.channel_combo.set(HANDOVER_CHANNELS[0])
        self.channel_combo.pack(anchor="w", fill="x", pady=(0, 12))

        # 3. Specific Person Name (Select from Colleagues or custom entry)
        ctk.CTkLabel(main_frame, text="Empfänger / Name der Person (aus Mitarbeiterliste wählen oder eingeben):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(4, 2))

        c_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        c_frame.pack(fill="x", pady=(0, 12))

        col_names = ["- Aus Mitarbeiterliste wählen -"] + [f"{c.name} ({c.department})" for c in self.colleagues] if self.colleagues else ["- Keine Mitarbeiter in Liste -"]
        self.colleague_combo = ctk.CTkOptionMenu(
            c_frame, values=col_names, command=self.on_colleague_selected, width=220
        )
        self.colleague_combo.pack(side="left", padx=(0, 5))

        self.person_entry = ctk.CTkEntry(
            c_frame, placeholder_text="Empfänger-Name..."
        )
        self.person_entry.pack(side="right", fill="x", expand=True)

        self.absence_warn_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11, weight="bold"))
        self.absence_warn_lbl.pack(anchor="w", pady=(0, 4))

        # 4. Optional Note
        ctk.CTkLabel(main_frame, text="Notiz / Details zur Übergabe (optional):").pack(anchor="w", pady=(4, 2))
        self.note_entry = ctk.CTkEntry(
            main_frame, placeholder_text="z. B. Ticket #104 im GitLab angelegt, Rückruf erbeten..."
        )
        self.note_entry.pack(fill="x", pady=(0, 15))

        self.err_lbl = ctk.CTkLabel(main_frame, text="", text_color="red")
        self.err_lbl.pack(anchor="w", pady=(0, 5))

        # Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(
            btn_frame, text="Abbrechen", fg_color="gray", command=self.on_cancel, width=110
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="🤝 Übergabe bestätigen",
            fg_color="forestgreen",
            command=self.on_confirm,
            width=180,
        ).pack(side="right")

    def on_colleague_selected(self, selected_text: str):
        self.absence_warn_lbl.configure(text="")
        if selected_text and not selected_text.startswith("-"):
            name_part = selected_text.split(" (")[0]
            self.person_entry.delete(0, "end")
            self.person_entry.insert(0, name_part)

            # Check absence
            for c in self.colleagues:
                if c.name == name_part:
                    if c.is_absent:
                        reason = f" ({c.absence_reason})" if c.absence_reason else ""
                        self.absence_warn_lbl.configure(text=f"⚠ ACHTUNG: {c.name} ist aktuell abwesend{reason}!", text_color="darkorange")
                    break

            col = next((c for c in self.colleagues if c.name == name_part), None)
            if col and col.department:
                dept_lower = col.department.lower()
                from enums import Actor
                if "entwickl" in dept_lower or "dev" in dept_lower:
                    self.actor_combo.set(ACTOR_DISPLAY[Actor.DEVELOPMENT])
                elif "tech" in dept_lower or "sys" in dept_lower or "it" in dept_lower:
                    self.actor_combo.set(ACTOR_DISPLAY[Actor.TECH])
                elif "supp" in dept_lower or "serv" in dept_lower:
                    self.actor_combo.set(ACTOR_DISPLAY[Actor.SUPPORT])

    def on_cancel(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def on_confirm(self):
        new_actor_display = self.actor_combo.get()
        new_actor_val = get_actor_val_from_display(new_actor_display)
        channel = self.channel_combo.get()
        person = self.person_entry.get().strip()
        note = self.note_entry.get().strip()

        cb = self.on_handover_confirmed
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

        if cb:
            cb(new_actor_val, channel, person, note)
