import tempfile
import webbrowser
import customtkinter as ctk
from pathlib import Path
from models.case import Case
from utils.datetime_utils import format_german_datetime


class CasePrintDialog(ctk.CTkToplevel):
    """Print preview and HTML report generator dialog allowing selective unchecking of timeline entries and fields."""

    def __init__(self, parent, case: Case):
        super().__init__(parent)
        self.case = case

        self.title(f"🖨️ Fall-Akte Druck- & HTML Export: {case.case_id}")
        self.geometry("640x560")
        self.minsize(580, 480)

        from utils.ui_utils import center_window
        center_window(self, 640, 560)

        self.transient(parent)
        self.grab_set()

        self.timeline_vars: list[tuple[ctk.BooleanVar, int]] = []
        self.include_customer_var = ctk.BooleanVar(value=True)
        self.include_fields_var = ctk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(main_frame, text=f"🖨️ Druckansicht für Fall {self.case.case_id} anpassen", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:").pack(anchor="w", pady=(0, 8))

        # Main options
        ctk.CTkCheckBox(main_frame, text="Praxis & Kundendaten einschließen", variable=self.include_customer_var).pack(anchor="w", pady=3)
        ctk.CTkCheckBox(main_frame, text="Ausgefüllte Formularfelder einschließen", variable=self.include_fields_var).pack(anchor="w", pady=3)

        ctk.CTkLabel(main_frame, text="Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(12, 4))

        scroll = ctk.CTkScrollableFrame(main_frame, height=220)
        scroll.pack(fill="both", expand=True, pady=(0, 10))

        if not self.case.timeline:
            ctk.CTkLabel(scroll, text="Keine Notizen in der Zeitleiste.").pack(pady=10)
        else:
            for idx, entry in enumerate(self.case.timeline):
                var = ctk.BooleanVar(value=True)
                self.timeline_vars.append((var, idx))

                formatted_ts = format_german_datetime(entry.timestamp)
                lbl_text = f"[{formatted_ts}] {entry.author}: {entry.note[:60]}..."
                ctk.CTkCheckBox(scroll, text=lbl_text, variable=var).pack(anchor="w", pady=3, padx=5)

        # Action bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray40", command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_frame, text="🖨️ Im Browser öffnen & Drucken", fg_color="forestgreen", command=self.generate_and_open_html, width=220).pack(side="right")

    def generate_and_open_html(self):
        selected_entries = [self.case.timeline[idx] for var, idx in self.timeline_vars if var.get()]

        html_lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            f"<title>Fall-Akte {self.case.case_id}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 30px; color: #222; }",
            "h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 6px; }",
            "h2 { color: #2e4053; margin-top: 20px; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 10px; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".entry { background: #f8f9f9; border-left: 4px solid #3498db; margin: 10px 0; padding: 10px; }",
            "</style></head><body>",
            f"<h1>Fall-Akte: {self.case.case_id} — {self.case.classification.title}</h1>",
            f"<p><strong>Erstellt am:</strong> {format_german_datetime(self.case.created_at)} | <strong>Erstellt von:</strong> {self.case.created_by}</p>",
        ]

        if self.include_customer_var.get():
            cust = self.case.customer
            html_lines.extend([
                "<h2>Kunden- & Praxisdaten</h2>",
                "<table>",
                f"<tr><th>Praxisname</th><td>{cust.practice_name}</td></tr>",
                f"<tr><th>Kunden-ID</th><td>{cust.customer_id}</td></tr>",
                f"<tr><th>Ansprechpartner</th><td>{cust.contact_person}</td></tr>",
                f"<tr><th>Telefon</th><td>{cust.phone}</td></tr>",
                "</table>",
            ])

        if self.include_fields_var.get() and self.case.form_data:
            html_lines.extend(["<h2>Formularfelder</h2><table>", "<tr><th>Feld</th><th>Wert</th></tr>"])
            for k, v in self.case.form_data.items():
                html_lines.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
            html_lines.append("</table>")

        if selected_entries:
            html_lines.append("<h2>Verlauf & Zeitleiste</h2>")
            for entry in selected_entries:
                ts_str = format_german_datetime(entry.timestamp)
                html_lines.append(
                    f"<div class='entry'><strong>[{ts_str}] {entry.author} ({entry.channel}):</strong><br>{entry.note}</div>"
                )

        html_lines.append("</body></html>")

        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Case_{self.case.case_id}_Print.html"
        html_file.write_text("\n".join(html_lines), encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.destroy()
