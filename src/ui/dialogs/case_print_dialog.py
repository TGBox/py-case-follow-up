import base64
import tempfile
import webbrowser
import customtkinter as ctk
from pathlib import Path
from typing import Any
from enums import get_actor_display, get_board_column_display
from models.case import Case
from utils.datetime_utils import format_german_datetime


class CasePrintDialog(ctk.CTkToplevel):
    """Print preview and HTML report generator dialog allowing selective unchecking of timeline entries and fields."""

    def __init__(self, parent, case: Case, attachment_service: Any | None = None):
        super().__init__(parent)
        self.case = case
        self.attachment_service = attachment_service

        self.title(f"🖨 Fall-Akte Druck- & HTML Export: {case.case_id}")
        self.geometry("680x600")
        self.minsize(620, 500)

        from utils.ui_utils import center_window
        center_window(self, 680, 600)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        self.timeline_vars: list[tuple[ctk.BooleanVar, int]] = []
        self.include_customer_var = ctk.BooleanVar(value=True)
        self.include_fields_var = ctk.BooleanVar(value=True)
        self.include_attachments_var = ctk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(main_frame, text=f"🖨 Druckansicht für Fall {self.case.case_id} anpassen", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:").pack(anchor="w", pady=(0, 8))

        # Main options
        opts_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkCheckBox(opts_frame, text="Praxis & Kundendaten", variable=self.include_customer_var).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(opts_frame, text="Formularfelder", variable=self.include_fields_var).pack(side="left", padx=(0, 12))
        ctk.CTkCheckBox(opts_frame, text="Bilder & Anhänge am Ende", variable=self.include_attachments_var).pack(side="left")

        ctk.CTkLabel(main_frame, text="Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 4))

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

        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), command=self.safe_destroy, width=90).pack(side="left")
        ctk.CTkButton(btn_frame, text="💾 Als HTML/PDF-Bericht speichern...", fg_color="royalblue", hover_color="blue", command=self.generate_and_save_file, width=220).pack(side="right", padx=(6, 0))
        ctk.CTkButton(btn_frame, text="🖨 Im Browser öffnen & Drucken", fg_color="forestgreen", hover_color="darkgreen", command=self.generate_and_open_html, width=210).pack(side="right")

    def safe_destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if hasattr(self, "tk"):
            self.after(1, self._do_destroy)
        else:
            self._do_destroy()

    def _do_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

    def build_html_content(self, auto_print: bool = True) -> str:
        selected_entries = [self.case.timeline[idx] for var, idx in self.timeline_vars if var.get()]

        status_disp = get_board_column_display(self.case.workflow_status.board_column)
        actor_disp = get_actor_display(self.case.workflow_status.current_actor)
        created_str = self.case.formatted_created_at or format_german_datetime(self.case.created_at)
        deadline_str = self.case.formatted_deadline or "Keine Frist gesetzt"
        followup_str = self.case.formatted_followup or "Keine Wiedervorlage gesetzt"

        print_script = """<script>
window.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() { window.print(); }, 400);
});
</script>""" if auto_print else ""

        html_lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            f"<title>Fall-Akte {self.case.case_id} — {self.case.classification.title}</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Arial, sans-serif; margin: 35px; color: #222; background: #fff; line-height: 1.5; }",
            "h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; margin-bottom: 12px; }",
            "h2 { color: #2e4053; margin-top: 25px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; }",
            "th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 13px; }",
            "th { background-color: #f4f6f7; width: 25%; font-weight: bold; color: #333; }",
            ".entry { background: #f8f9f9; border-left: 4px solid #3498db; margin: 10px 0; padding: 10px 14px; border-radius: 0 4px 4px 0; }",
            ".no-print { margin-bottom: 20px; background: #ebf5fb; padding: 15px; border-radius: 6px; border: 1px solid #aed6f1; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }",
            ".print-btn { background: #27ae60; color: white; border: none; padding: 10px 20px; font-size: 14px; font-weight: bold; border-radius: 4px; cursor: pointer; }",
            ".print-btn:hover { background: #219150; }",
            ".img-container { margin: 18px 0; page-break-inside: avoid; text-align: center; }",
            ".img-container img { max-width: 95%; max-height: 800px; border: 1px solid #ccc; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }",
            ".img-caption { font-size: 12px; color: #666; margin-top: 6px; font-weight: bold; }",
            "@media print { .no-print { display: none !important; } body { margin: 0; } }",
            "</style>",
            print_script,
            "</head><body>",
            "<div class='no-print'>",
            "  <div><strong>Druckansicht Fall-Akte</strong> — Klicken Sie auf Drucken oder speichern Sie die Datei als PDF.</div>",
            "  <button class='print-btn' onclick='window.print()'>🖨 Als PDF speichern / Drucken</button>",
            "</div>",
            f"<h1>Fall-Akte: {self.case.case_id} — {self.case.classification.title}</h1>",
            "<table>",
            f"<tr><th>Fall-ID</th><td><strong>{self.case.case_id}</strong></td><th>Priorität / Score</th><td>{self.case.classification.calculated_score:.0f} Pkt. ({self.case.classification.urgency_level})</td></tr>",
            f"<tr><th>Aktueller Status</th><td>{status_disp}</td><th>Zuständigkeit</th><td>{actor_disp}</td></tr>",
            f"<tr><th>Erstellt am</th><td>{created_str} ({self.case.created_by})</td><th>Rückruf-Deadline</th><td>{deadline_str}</td></tr>",
            f"<tr><th>Wiedervorlage</th><td colspan='3'>{followup_str}</td></tr>",
            "</table>",
        ]

        if self.include_customer_var.get() and self.case.customer:
            cust = self.case.customer
            vip_str = " (VIP-Kunde)" if cust.is_vip else ""
            html_lines.extend([
                "<h2>Kunden- & Praxisdaten</h2>",
                "<table>",
                f"<tr><th>Praxisname</th><td>{cust.practice_name}{vip_str}</td></tr>",
                f"<tr><th>Kunden-ID</th><td>{cust.customer_id}</td></tr>",
                f"<tr><th>Ansprechpartner</th><td>{cust.contact_person or '-'}</td></tr>",
                f"<tr><th>Telefon</th><td>{cust.phone or '-'}</td></tr>",
                f"<tr><th>E-Mail</th><td>{cust.email or '-'}</td></tr>",
                "</table>",
            ])

        if self.include_fields_var.get() and self.case.form_data:
            html_lines.extend(["<h2>Formularfelder & Details</h2><table>", "<tr><th>Feld</th><th>Wert</th></tr>"])
            for k, v in self.case.form_data.items():
                val_disp = "<br>".join(str(v).splitlines()) if "\n" in str(v) else str(v)
                html_lines.append(f"<tr><th>{k}</th><td>{val_disp}</td></tr>")
            html_lines.append("</table>")

        if selected_entries:
            html_lines.append("<h2>Verlauf & Zeitleiste</h2>")
            for entry in selected_entries:
                ts_str = format_german_datetime(entry.timestamp)
                note_html = "<br>".join(entry.note.splitlines())
                html_lines.append(
                    f"<div class='entry'><strong>[{ts_str}] {entry.author} ({entry.channel}):</strong><br>{note_html}</div>"
                )

        if self.include_attachments_var.get() and self.attachment_service:
            try:
                att_files = self.attachment_service.list_attachments(self.case)
                if att_files:
                    html_lines.append("<h2>Anhänge & Bilder</h2>")
                    img_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
                    img_files = [f for f in att_files if f.suffix.lower() in img_exts]
                    other_files = [f for f in att_files if f.suffix.lower() not in img_exts]

                    if other_files:
                        html_lines.append("<table><tr><th>Dateiname</th><th>Dateigröße</th></tr>")
                        for f in other_files:
                            size_kb = f.stat().st_size / 1024.0 if f.exists() else 0
                            html_lines.append(f"<tr><td>📄 {f.name}</td><td>{size_kb:.1f} KB</td></tr>")
                        html_lines.append("</table>")

                    for img_path in img_files:
                        try:
                            data = img_path.read_bytes()
                            ext = img_path.suffix.lower().replace(".", "")
                            if ext == "jpg":
                                ext = "jpeg"
                            b64 = base64.b64encode(data).decode("utf-8")
                            html_lines.append(
                                f"<div class='img-container'><img src='data:image/{ext};base64,{b64}' alt='{img_path.name}' /><div class='img-caption'>📷 {img_path.name}</div></div>"
                            )
                        except Exception:
                            pass
            except Exception:
                pass

        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    def generate_and_open_html(self):
        html_content = self.build_html_content(auto_print=True)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Case_{self.case.case_id}_Print.html"
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.safe_destroy()

    def generate_and_save_file(self):
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Fallbericht speichern",
            defaultextension=".html",
            initialfile=f"Fallbericht_{self.case.case_id}.html",
            filetypes=[("HTML-Bericht (für PDF-Druck)", "*.html"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return

        html_content = self.build_html_content(auto_print=False)
        Path(file_path).write_text(html_content, encoding="utf-8")
        self.safe_destroy()


