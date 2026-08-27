import customtkinter as ctk
from typing import Any
from models.case import Case
from enums import UrgencyLevel, Actor, get_actor_display
from utils.datetime_utils import parse_iso, get_local_now


class AnalyticsView(ctk.CTkFrame):
    """Analytics and KPI dashboard view for case statistics, urgency breakdown, practice rankings, and workload metrics."""

    def __init__(self, parent):
        super().__init__(parent)
        self.cases: list[Case] = []
        self.schemas: list[Any] = []
        self.create_widgets()

    def set_schemas(self, schemas: list[Any]):
        self.schemas = schemas

    def set_cases(self, cases: list[Case]):
        self.cases = cases
        self.render_dashboard()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            top_bar,
            text="Auswertungen & Support Cockpit KPIs",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            top_bar,
            text="📋 Statistik-Bericht kopieren",
            width=190,
            fg_color="gray30",
            hover_color="gray40",
            command=self.copy_analytics_report,
        ).pack(side="right")

        # Scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

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
        vip_cases = [c for c in self.cases if getattr(c.customer, "is_vip", False)]

        # Calculate overdue cases
        now = get_local_now()
        overdue_cases = []
        for c in open_cases:
            due_str = getattr(c.workflow_status, "followup_at", "") or getattr(c.classification, "deadline_callback", "") or getattr(c, "due_date", "")
            if due_str:
                try:
                    if parse_iso(due_str) < now:
                        overdue_cases.append(c)
                except Exception:
                    pass

        # Calculate avg resolution time
        res_seconds = []
        for c in completed_cases:
            try:
                c_dt = parse_iso(c.created_at) if c.created_at else None
                u_dt = parse_iso(c.updated_at) if c.updated_at else None
                if c_dt and u_dt and u_dt >= c_dt:
                    res_seconds.append((u_dt - c_dt).total_seconds())
            except Exception:
                pass

        if res_seconds:
            avg_sec = sum(res_seconds) / len(res_seconds)
            avg_days = avg_sec / 86400.0
            if avg_days >= 1.0:
                avg_res_str = f"{avg_days:.1f} Tage"
            else:
                avg_hrs = max(0.1, avg_sec / 3600.0)
                avg_res_str = f"{avg_hrs:.1f} Std"
        else:
            avg_res_str = "n/a"

        completed_pct = (len(completed_cases) / total_count * 100.0) if total_count > 0 else 0.0
        vip_pct = (len(vip_cases) / total_count * 100.0) if total_count > 0 else 0.0

        # 1. Top Summary KPI Cards Row (6 Cards)
        summary_row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        summary_row.pack(fill="x", pady=(0, 12))

        self.create_card(summary_row, "📋 Fälle Gesamt", str(total_count), "dodgerblue")
        self.create_card(summary_row, "⏳ Offene Fälle", str(len(open_cases)), "darkorange")
        self.create_card(summary_row, "✓ Erledigt", f"{len(completed_cases)} ({completed_pct:.0f}%)", "forestgreen")
        self.create_card(summary_row, "⚠ Überfällig", str(len(overdue_cases)), "firebrick" if overdue_cases else "forestgreen")
        self.create_card(summary_row, "⏱ Ø Bearbeitung", avg_res_str, "darkviolet")
        self.create_card(summary_row, "⭐ VIP-Quote", f"{vip_pct:.1f}%", "gold")

        # 2. Grid Container (2 Columns for balanced layout)
        grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, pady=4)
        grid_frame.columnconfigure(0, weight=1, uniform="col")
        grid_frame.columnconfigure(1, weight=1, uniform="col")

        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # --- LEFT COLUMN: Urgency Breakdown & Schema/Form breakdown ---
        # Card L1: Urgency Breakdown
        urg_frame = ctk.CTkFrame(left_col, fg_color=("gray85", "gray20"), corner_radius=8)
        urg_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(urg_frame, text="🚨 Dringlichkeits-Verteilung (Scoring)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        red_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)
        yellow_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW)
        green_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN)
        open_total = max(1, len(open_cases))

        urg_row = ctk.CTkFrame(urg_frame, fg_color="transparent")
        urg_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(urg_row, text=f"🔴 Rot (Kritisch): {red_count} ({red_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="red").pack(anchor="w", pady=2)
        ctk.CTkLabel(urg_row, text=f"🟡 Gelb (Mittel): {yellow_count} ({yellow_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="gold").pack(anchor="w", pady=2)
        ctk.CTkLabel(urg_row, text=f"🟢 Grün (Normal): {green_count} ({green_count/open_total*100:.0f}%)", font=ctk.CTkFont(size=12, weight="bold"), text_color="limegreen").pack(anchor="w", pady=2)

        # Card L2: Schema / Form Distribution
        schema_frame = ctk.CTkFrame(left_col, fg_color=("gray85", "gray20"), corner_radius=8)
        schema_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(schema_frame, text="📄 Verteilung nach Formular / Schema", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        schema_map = {getattr(s, "schema_id", ""): getattr(s, "display_name", "") for s in self.schemas}
        schema_counts: dict[str, int] = {}
        for c in self.cases:
            sid = c.classification.schema_id or "Allgemein"
            sname = schema_map.get(sid, sid.replace("schema_", "").replace("_", " ").title())
            schema_counts[sname] = schema_counts.get(sname, 0) + 1

        sorted_schemas = sorted(schema_counts.items(), key=lambda item: item[1], reverse=True)
        for sname, scount in sorted_schemas:
            pct = scount / total_count * 100.0
            ctk.CTkLabel(schema_frame, text=f"• {sname}: {scount} Fälle ({pct:.0f}%)", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

        # --- RIGHT COLUMN: Top Practices, Assignee Workload, Department breakdown ---
        # Card R1: Top Practices Ranking
        prac_frame = ctk.CTkFrame(right_col, fg_color=("gray85", "gray20"), corner_radius=8)
        prac_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(prac_frame, text="🏆 Top 5 Praxen nach Fallaufkommen", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        prac_counts: dict[str, tuple[int, bool]] = {}
        for c in self.cases:
            p_name = c.customer.practice_name
            is_vip = getattr(c.customer, "is_vip", False)
            curr_cnt, _ = prac_counts.get(p_name, (0, is_vip))
            prac_counts[p_name] = (curr_cnt + 1, is_vip)

        sorted_prac = sorted(prac_counts.items(), key=lambda item: item[1][0], reverse=True)[:5]
        for idx, (p_name, (count, is_vip)) in enumerate(sorted_prac, start=1):
            vip_str = " ★ VIP" if is_vip else ""
            ctk.CTkLabel(prac_frame, text=f"{idx}. {p_name}{vip_str} — {count} Vorgänge", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

        # Card R2: Assignee Workload (Bearbeiter)
        staff_frame = ctk.CTkFrame(right_col, fg_color=("gray85", "gray20"), corner_radius=8)
        staff_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(staff_frame, text="👤 Bearbeiter-Auslastung", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        assignee_stats: dict[str, dict[str, int]] = {}
        for c in self.cases:
            assignee = c.assigned_to.strip() if getattr(c, "assigned_to", "") and c.assigned_to.strip() else "Nicht zugewiesen"
            if assignee not in assignee_stats:
                assignee_stats[assignee] = {"open": 0, "done": 0}
            if c.workflow_status.is_completed:
                assignee_stats[assignee]["done"] += 1
            elif not c.workflow_status.is_archived:
                assignee_stats[assignee]["open"] += 1

        for assignee, st in sorted(assignee_stats.items(), key=lambda item: item[1]["open"], reverse=True):
            ctk.CTkLabel(staff_frame, text=f"• {assignee}: {st['open']} offen, {st['done']} erledigt", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

        # Card R3: Department / Actor Breakdown
        dept_frame = ctk.CTkFrame(right_col, fg_color=("gray85", "gray20"), corner_radius=8)
        dept_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(dept_frame, text="👥 Offene Fälle nach Abteilung / Zuständigkeit", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        actor_counts: dict[str, int] = {}
        for c in open_cases:
            act_str = get_actor_display(c.workflow_status.current_actor)
            actor_counts[act_str] = actor_counts.get(act_str, 0) + 1

        for act_str, count in actor_counts.items():
            ctk.CTkLabel(dept_frame, text=f"• {act_str}: {count} Fälle", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=16, pady=2)

    def create_card(self, parent, title: str, value: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=8, width=130)
        card.pack(side="left", fill="x", expand=True, padx=3, pady=2)

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=("gray40", "gray70")).pack(pady=(6, 1))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(pady=(0, 6))

    def generate_report_markdown(self) -> str:
        total_count = len(self.cases)
        open_cases = [c for c in self.cases if not c.workflow_status.is_completed and not c.workflow_status.is_archived]
        completed_cases = [c for c in self.cases if c.workflow_status.is_completed]
        vip_cases = [c for c in self.cases if getattr(c.customer, "is_vip", False)]

        now = get_local_now()
        overdue_cases = []
        for c in open_cases:
            due_str = getattr(c.workflow_status, "followup_at", "") or getattr(c.classification, "deadline_callback", "") or getattr(c, "due_date", "")
            if due_str:
                try:
                    if parse_iso(due_str) < now:
                        overdue_cases.append(c)
                except Exception:
                    pass

        lines = [
            "# Support Cockpit — Statistik & Kennzahlen Bericht",
            f"**Fälle Gesamt:** {total_count}",
            f"**Offene Fälle:** {len(open_cases)}",
            f"**Erledigte Fälle:** {len(completed_cases)} ({(len(completed_cases)/total_count*100 if total_count else 0):.1f}%)",
            f"**Überfällige Wiedervorlagen:** {len(overdue_cases)}",
            f"**VIP-Kundenquote:** {(len(vip_cases)/total_count*100 if total_count else 0):.1f}%\n",
            "### Dringlichkeits-Verteilung (Scoring):",
            f"- Rot (Kritisch): {sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)}",
            f"- Gelb (Mittel): {sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW)}",
            f"- Grün (Normal): {sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN)}\n",
            "### Offene Fälle nach Abteilung:",
        ]
        actor_counts: dict[str, int] = {}
        for c in open_cases:
            act_str = get_actor_display(c.workflow_status.current_actor)
            actor_counts[act_str] = actor_counts.get(act_str, 0) + 1
        for act_str, count in actor_counts.items():
            lines.append(f"- {act_str}: {count} Fälle")

        return "\n".join(lines)

    def copy_analytics_report(self):
        report_text = self.generate_report_markdown()
        try:
            self.clipboard_clear()
            self.clipboard_append(report_text)
        except Exception:
            pass

        try:
            from ui.widgets.toast_notification import ToastNotification
            ToastNotification(self.winfo_toplevel(), title="📋 Statistik kopiert", message="Statistik-Bericht wurde in die Zwischenablage kopiert.")
        except Exception:
            pass
