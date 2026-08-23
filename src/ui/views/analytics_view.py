import customtkinter as ctk
from models.case import Case
from enums import UrgencyLevel, Actor, get_actor_display


class AnalyticsView(ctk.CTkFrame):
    """Analytics and KPI dashboard view for case statistics, urgency breakdown, and practice rankings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.cases: list[Case] = []
        self.create_widgets()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(top_bar, text="📊 Auswertungen & Support Cockpit KPIs", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

        # Scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.render_dashboard()

    def render_dashboard(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.cases:
            ctk.CTkLabel(self.scroll_frame, text="Keine Auswertungsdaten verfügbar.").pack(pady=20)
            return

        total_count = len(self.cases)
        open_cases = [c for c in self.cases if not c.workflow_status.is_completed and not c.workflow_status.is_archived]
        completed_cases = [c for c in self.cases if c.workflow_status.is_completed]
        archived_cases = [c for c in self.cases if c.workflow_status.is_archived]

        # 1. Summary Cards Row
        summary_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        summary_row.pack(fill="x", pady=(0, 15))

        self.create_card(summary_row, "📋 Fälle Gesamt", str(total_count), "dodgerblue")
        self.create_card(summary_row, "⏳ Offene Fälle", str(len(open_cases)), "darkorange")
        self.create_card(summary_row, "✓ Erledigt", str(len(completed_cases)), "forestgreen")
        self.create_card(summary_row, "📦 Archiviert", str(len(archived_cases)), "gray40")

        # 2. Urgency Breakdown Card
        urg_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        urg_frame.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(urg_frame, text="🚨 Dringlichkeits-Verteilung (Scoring)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))

        red_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)
        yellow_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW)
        green_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN)

        urg_row = ctk.CTkFrame(urg_frame, fg_color="transparent")
        urg_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(urg_row, text=f"🔴 Rot (Kritisch): {red_count}", font=ctk.CTkFont(weight="bold"), text_color="red").pack(side="left", padx=15)
        ctk.CTkLabel(urg_row, text=f"🟡 Gelb (Mittel): {yellow_count}", font=ctk.CTkFont(weight="bold"), text_color="gold").pack(side="left", padx=15)
        ctk.CTkLabel(urg_row, text=f"🟢 Grün (Normal): {green_count}", font=ctk.CTkFont(weight="bold"), text_color="limegreen").pack(side="left", padx=15)

        # 3. Top Practices Ranking Card
        prac_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        prac_frame.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(prac_frame, text="🏆 Top 5 Praxen nach Fallaufkommen", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))

        counts: dict[str, int] = {}
        for c in self.cases:
            p_name = c.customer.practice_name
            counts[p_name] = counts.get(p_name, 0) + 1

        sorted_prac = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
        for idx, (p_name, count) in enumerate(sorted_prac, start=1):
            ctk.CTkLabel(prac_frame, text=f"{idx}. {p_name} — {count} Vorgänge", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

        # 4. Department / Actor Breakdown Card
        dept_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        dept_frame.pack(fill="x", pady=8, padx=4)

        ctk.CTkLabel(dept_frame, text="👥 Offene Fälle nach Abteilung / Zuständigkeit", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))

        actor_counts: dict[str, int] = {}
        for c in open_cases:
            act_str = get_actor_display(c.workflow_status.current_actor)
            actor_counts[act_str] = actor_counts.get(act_str, 0) + 1

        for act_str, count in actor_counts.items():
            ctk.CTkLabel(dept_frame, text=f"• {act_str}: {count} Fälle", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

    def create_card(self, parent, title: str, value: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=8, width=150)
        card.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=("gray40", "gray70")).pack(pady=(8, 2))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color).pack(pady=(0, 8))
