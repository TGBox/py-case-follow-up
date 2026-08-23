import customtkinter as ctk
from typing import Callable
from models.case import Case
from models.profile import Colleague
from enums import ACTOR_DISPLAY, get_actor_val_from_display, get_actor_display


HANDOVER_CHANNELS = [
    "Persönliche Absprache",
    "E-Mail",
    "Telefonanruf",
    "Slacknachricht / Chat",
    "GitLab Issue / Ticket",
    "Sonstiges",
]


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
        self.colleagues = colleagues or []
        self.on_handover_confirmed = on_handover_confirmed

        self.title(f"👤 Zuständigkeit übergeben (Fall {case.case_id})")
        self.geometry("500x440")
        self.resizable(False, False)
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

        # 3. Specific Person Name (Optional Entry or Dropdown)
        ctk.CTkLabel(main_frame, text="Empfänger / Name der Person (optional):").pack(anchor="w", pady=(4, 2))

        if self.colleagues:
            c_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            c_frame.pack(fill="x", pady=(0, 12))

            col_names = ["- Aus Liste wählen -"] + [f"{c.name} ({c.department})" for c in self.colleagues]
            self.colleague_combo = ctk.CTkOptionMenu(
                c_frame, values=col_names, command=self.on_colleague_selected, width=180
            )
            self.colleague_combo.pack(side="left", padx=(0, 5))

            self.person_entry = ctk.CTkEntry(
                c_frame, placeholder_text="Name oder aus Liste wählen..."
            )
            self.person_entry.pack(side="right", fill="x", expand=True)
        else:
            self.person_entry = ctk.CTkEntry(
                main_frame, placeholder_text="z. B. Max Mustermann, Hr. Becker..."
            )
            self.person_entry.pack(fill="x", pady=(0, 12))

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
            btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy, width=110
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="🤝 Übergabe bestätigen",
            fg_color="forestgreen",
            command=self.on_confirm,
            width=180,
        ).pack(side="right")

    def on_colleague_selected(self, selected_text: str):
        if selected_text and not selected_text.startswith("-"):
            # Extract name before parentheses
            name_part = selected_text.split(" (")[0]
            self.person_entry.delete(0, "end")
            self.person_entry.insert(0, name_part)

    def on_confirm(self):
        new_actor_display = self.actor_combo.get()
        new_actor_val = get_actor_val_from_display(new_actor_display)
        channel = self.channel_combo.get()
        person = self.person_entry.get().strip()
        note = self.note_entry.get().strip()

        if self.on_handover_confirmed:
            self.on_handover_confirmed(new_actor_val, channel, person, note)

        self.destroy()
