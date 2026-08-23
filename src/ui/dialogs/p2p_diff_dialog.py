import customtkinter as ctk
from typing import Callable
from models.profile import Colleague
from models.case import Case
from services.p2p_sync_service import P2PSyncService, CaseDiffItem


class P2PDiffDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        colleagues: list[Colleague],
        p2p_service: P2PSyncService,
        on_sync_completed: Callable[[], None],
    ):
        super().__init__(parent)
        self.title("Multi-User P2P-Sync & Kollegendaten-Abgleich")
        self.geometry("920x720")
        self.minsize(820, 620)
        from utils.ui_utils import center_window
        center_window(self, 920, 720)

        self.colleagues = colleagues
        self.p2p_service = p2p_service
        self.on_sync_completed = on_sync_completed

        self.active_colleague = colleagues[0] if colleagues else None
        self.diff_items: list[CaseDiffItem] = []
        self.selected_vars: dict[str, ctk.BooleanVar] = {}

        self.grab_set()
        self.create_widgets()
        if self.active_colleague:
            self.load_and_compare()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header & Colleague Selector
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(top_frame, text="Kollege auswählen:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        colleague_names = [f"{c.name} (@{c.username})" for c in self.colleagues]
        self.colleague_combo = ctk.CTkOptionMenu(
            top_frame,
            values=colleague_names if colleague_names else ["Keine Kollegen konfiguriert"],
            command=self.on_colleague_selected,
            width=360,
        )
        if self.active_colleague:
            self.colleague_combo.set(f"{self.active_colleague.name} (@{self.active_colleague.username})")
        self.colleague_combo.pack(side="left", padx=(0, 10))

        load_btn = ctk.CTkButton(top_frame, text="Neu Laden / Vergleichen", command=self.load_and_compare, width=180)
        load_btn.pack(side="left")

        # Status Banner
        self.status_label = ctk.CTkLabel(main_frame, text="", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(fill="x", pady=(0, 10))

        # Diff Table Scroll Area
        self.diff_scroll = ctk.CTkScrollableFrame(main_frame, width=780, height=440)
        self.diff_scroll.pack(fill="both", expand=True, pady=(0, 15))

        # Bottom Bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        close_btn = ctk.CTkButton(btn_frame, text="Schließen", fg_color="gray", command=self.destroy, width=120)
        close_btn.pack(side="left")

        import_btn = ctk.CTkButton(btn_frame, text="Ausgewählte Fälle übernehmen", command=self.on_import_selected, width=240)
        import_btn.pack(side="right")

    def on_colleague_selected(self, selected_str: str):
        self.active_colleague = next((c for c in self.colleagues if f"{c.name} (@{c.username})" == selected_str), None)
        self.load_and_compare()

    def load_and_compare(self):
        if not self.active_colleague:
            self.status_label.configure(text="Kein Kollege ausgewählt.", text_color="red")
            return

        success, msg, remote_cases = self.p2p_service.read_colleague_cases(self.active_colleague)
        if not success:
            self.status_label.configure(text=f"⚠️ {msg}", text_color="red")
            self.render_diff_list([])
            return

        self.diff_items = self.p2p_service.compute_diff(remote_cases)
        self.status_label.configure(
            text=f"✅ {len(remote_cases)} Fälle von {self.active_colleague.name} geladen.", text_color="green"
        )
        self.render_diff_list(self.diff_items)

    def render_diff_list(self, items: list[CaseDiffItem]):
        for widget in self.diff_scroll.winfo_children():
            widget.destroy()
        self.selected_vars.clear()

        if not items:
            ctk.CTkLabel(self.diff_scroll, text="Keine abweichenden Fälle vorhanden.").pack(pady=20)
            return

        for idx, item in enumerate(items):
            row = ctk.CTkFrame(self.diff_scroll, fg_color=("gray90", "gray20") if idx % 2 == 0 else "transparent")
            row.pack(fill="x", pady=2, padx=5)

            # Checkbox
            var = ctk.BooleanVar(value=item.status in ("NEW", "REMOTE_NEWER"))
            self.selected_vars[item.case_id] = var
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=30)
            chk.pack(side="left", padx=5)

            # Status Badge Color
            if item.status == "NEW":
                badge_color = "dodgerblue"
                status_text = "[NEU]"
            elif item.status == "REMOTE_NEWER":
                badge_color = "orange"
                status_text = "[KOLLEGE NEUER]"
            elif item.status == "LOCAL_NEWER":
                badge_color = "gray"
                status_text = "[LOKAL NEUER]"
            else:
                badge_color = "gray30"
                status_text = "[IDENTISCH]"

            badge = ctk.CTkLabel(row, text=status_text, text_color=badge_color, font=ctk.CTkFont(weight="bold"), width=130, anchor="w")
            badge.pack(side="left", padx=5)

            # Info string
            practice = item.remote_case.customer.practice_name
            title = item.remote_case.classification.title
            info_str = f"{item.case_id} — {practice}: {title}"
            lbl = ctk.CTkLabel(row, text=info_str, anchor="w", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", expand=True, fill="x", padx=5)

            # Timestamps
            ts_str = f"Fremd: {item.remote_updated_at} | Lokal: {item.local_updated_at or 'Keine'}"
            ctk.CTkLabel(row, text=ts_str, text_color="gray70", font=ctk.CTkFont(size=11)).pack(side="right", padx=10)

    def on_import_selected(self):
        selected_cases = []
        for item in self.diff_items:
            if self.selected_vars.get(item.case_id, ctk.BooleanVar()).get():
                selected_cases.append(item.remote_case)

        if not selected_cases:
            self.status_label.configure(text="Bitte mindestens einen Fall zur Übernahme auswählen.", text_color="orange")
            return

        count = self.p2p_service.import_selected_cases(selected_cases)
        self.status_label.configure(text=f"✅ {count} Fälle erfolgreich in lokale Arbeitsdaten übernommen!", text_color="green")
        self.on_sync_completed()
        self.load_and_compare()
