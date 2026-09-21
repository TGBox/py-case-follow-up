import base64
from collections.abc import Sequence

from constants import (
    IMAGE_FILE_EXTENSIONS,
    PRINT_AUTO_DELAY_MS,
    REPORT_FIELD_LONG_TEXT_THRESHOLD,
)
from enums import get_actor_display, get_board_column_display
from models.case import Case, TimelineEntry
from services.attachment_service import AttachmentService
from services.i18n_service import tr
from utils.datetime_utils import format_german_datetime


def generate_case_report_html(
    case: Case,
    include_customer: bool = True,
    include_fields: bool = True,
    include_attachments: bool = True,
    selected_entries: Sequence[TimelineEntry] | None = None,
    attachment_service: AttachmentService | None = None,
    auto_print: bool = False,
) -> str:
    """Generates a compact HTML report for a case.

    Layout is optimized to fit typical cases on a single A4 page when exported to PDF
    or printed, while remaining clean and modern on screen.
    """
    status_disp = get_board_column_display(case.workflow_status.board_column)
    actor_disp = get_actor_display(case.workflow_status.current_actor)
    created_str = case.formatted_created_at or format_german_datetime(case.created_at)
    deadline_str = case.formatted_deadline or tr("case_print.no_deadline", "Keine Frist gesetzt")
    followup_str = case.formatted_followup or tr("case_print.no_followup", "Keine Wiedervorlage gesetzt")

    print_script = (
        f"""<script>
window.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{ window.print(); }}, {PRINT_AUTO_DELAY_MS});
}});
</script>"""
        if auto_print
        else ""
    )

    banner_text = (
        tr(
            "case_print.banner_print",
            "<strong>Druckansicht Fall-Akte</strong> — Druckdialog wird geöffnet. Wählen Sie Ihren Drucker oder „Als PDF speichern“.",
        )
        if auto_print
        else tr("case_print.banner_view", "<strong>Fall-Akte Ansicht</strong> — Übersicht für Fall {case_id}.", case_id=case.case_id)
    )

    btn_print_pdf_txt = tr("case_print.btn_print_pdf", "Drucken / Als PDF speichern")
    hdr_meta = tr("case_print.header_case_metadata", "Fall-Metadaten")
    hdr_customer = tr("case_print.header_customer_data", "Kunden- & Praxisdaten")
    hdr_fields = tr("case_print.header_form_fields", "Formularfelder & Details")
    hdr_timeline = tr("case_print.header_timeline", "Verlauf & Zeitleiste")
    hdr_attachments = tr("case_print.header_attachments", "Anhänge & Bilder")

    lbl_case_id = tr("case_print.col_case_id", "Fall-ID")
    lbl_score = tr("case_print.col_score", "Priorität / Score")
    lbl_status = tr("case_print.col_status", "Aktueller Status")
    lbl_actor = tr("case_print.col_actor", "Zuständigkeit")
    lbl_created = tr("case_print.col_created", "Erstellt am")
    lbl_deadline = tr("case_print.col_deadline", "Rückruf-Deadline")
    lbl_followup = tr("case_print.col_followup", "Wiedervorlage")

    lbl_practice = tr("case_print.col_practice", "Praxisname")
    lbl_cust_id = tr("case_print.col_cust_id", "Kunden-ID")
    lbl_contact = tr("case_print.col_contact", "Ansprechpartner")
    lbl_phone = tr("case_print.col_phone", "Telefon")
    lbl_email = tr("case_print.col_email", "E-Mail")

    lbl_filename = tr("case_print.col_filename", "Dateiname")
    lbl_filesize = tr("case_print.col_filesize", "Dateigröße")

    html_lines = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>Fall-Akte {case.case_id} — {case.classification.title}</title>",
        "<style>",
        "@page { size: A4 portrait; margin: 8mm 10mm; }",
        "* { box-sizing: border-box; }",
        "body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; margin: 15px 20px; color: #222; background: #fff; line-height: 1.35; font-size: 11px; }",
        "h1 { font-size: 15px; color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px; margin: 0 0 8px 0; }",
        "h2 { font-size: 12px; color: #2e4053; margin: 8px 0 4px 0; border-bottom: 1px solid #ddd; padding-bottom: 2px; page-break-after: avoid; }",
        "table { width: 100%; border-collapse: collapse; margin-top: 3px; margin-bottom: 6px; page-break-inside: avoid; }",
        "th, td { border: 1px solid #ddd; padding: 3px 6px; text-align: left; font-size: 10.5px; vertical-align: top; }",
        "th { background-color: #f4f6f7; width: 34%; font-weight: bold; color: #333; }",
        ".top-grid { display: flex; gap: 12px; margin-bottom: 6px; page-break-inside: avoid; }",
        ".top-col { flex: 1; min-width: 0; }",
        ".top-col table { margin-bottom: 0; }",
        ".fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 8px; margin-top: 4px; margin-bottom: 8px; }",
        ".field-card { border: 1px solid #ddd; background: #fdfefe; padding: 3px 6px; border-radius: 3px; font-size: 10.5px; page-break-inside: avoid; }",
        ".field-card.full-width { grid-column: 1 / -1; }",
        ".field-label { font-weight: bold; color: #34495e; margin-bottom: 1px; }",
        ".field-value { color: #222; word-break: break-word; }",
        ".timeline-list { margin-top: 4px; margin-bottom: 8px; }",
        ".entry { background: #f8f9fa; border-left: 3px solid #3498db; margin: 3px 0; padding: 3px 8px; border-radius: 0 3px 3px 0; font-size: 10.5px; line-height: 1.3; page-break-inside: avoid; }",
        ".entry-header { font-weight: bold; color: #1a5276; }",
        ".entry-note { color: #222; margin-top: 1px; }",
        ".no-print { margin-bottom: 12px; background: #ebf5fb; padding: 8px 12px; border-radius: 6px; border: 1px solid #aed6f1; font-size: 12px; display: flex; align-items: center; justify-content: space-between; }",
        ".print-btn { background: #27ae60; color: white; border: none; padding: 6px 14px; font-size: 12px; font-weight: bold; border-radius: 4px; cursor: pointer; }",
        ".print-btn:hover { background: #219150; }",
        ".img-container { margin: 8px 0; page-break-inside: avoid; text-align: center; }",
        ".img-container img { max-width: 95%; max-height: 450px; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }",
        ".img-caption { font-size: 10.5px; color: #666; margin-top: 3px; font-weight: bold; }",
        "@media print {",
        "  .no-print { display: none !important; }",
        "  body { margin: 0; padding: 0; font-size: 9.5pt; }",
        "  h1 { font-size: 12.5pt; margin-bottom: 4px; }",
        "  h2 { font-size: 10pt; margin-top: 5px; margin-bottom: 2px; }",
        "  .top-grid { display: flex !important; gap: 8px; }",
        "  .fields-grid { display: grid !important; gap: 3px 6px; }",
        "  th, td { padding: 2.5px 5px; font-size: 8.5pt; }",
        "  .field-card { padding: 2.5px 5px; font-size: 8.5pt; }",
        "  .entry { margin: 2.5px 0; padding: 2.5px 6px; font-size: 8.5pt; }",
        "  .img-container img { max-height: 380px; }",
        "}",
        "</style>",
        print_script,
        "</head><body>",
        "<div class='no-print'>",
        f"  <div>{banner_text}</div>",
        f"  <button class='print-btn' onclick='window.print()'>{btn_print_pdf_txt}</button>",
        "</div>",
        f"<h1>Fall-Akte: {case.case_id} — {case.classification.title}</h1>",
    ]

    has_customer = include_customer and case.customer is not None
    if has_customer and case.customer:
        cust = case.customer
        vip_str = tr("case_print.vip_suffix", " (VIP-Kunde)") if cust.is_vip else ""
        html_lines.extend([
            "<div class='top-grid'>",
            "  <div class='top-col'>",
            f"    <h2>{hdr_meta}</h2>",
            "    <table>",
            f"      <tr><th>{lbl_case_id}</th><td><strong>{case.case_id}</strong></td></tr>",
            f"      <tr><th>{lbl_score}</th><td>{case.classification.calculated_score:.0f} Pkt. ({case.classification.urgency_level})</td></tr>",
            f"      <tr><th>{lbl_status}</th><td>{status_disp}</td></tr>",
            f"      <tr><th>{lbl_actor}</th><td>{actor_disp}</td></tr>",
            f"      <tr><th>{lbl_created}</th><td>{created_str} ({case.created_by})</td></tr>",
            f"      <tr><th>{lbl_deadline}</th><td>{deadline_str}</td></tr>",
            f"      <tr><th>{lbl_followup}</th><td>{followup_str}</td></tr>",
            "    </table>",
            "  </div>",
            "  <div class='top-col'>",
            f"    <h2>{hdr_customer}</h2>",
            "    <table>",
            f"      <tr><th>{lbl_practice}</th><td><strong>{cust.practice_name}</strong>{vip_str}</td></tr>",
            f"      <tr><th>{lbl_cust_id}</th><td>{cust.customer_id}</td></tr>",
            f"      <tr><th>{lbl_contact}</th><td>{cust.contact_person or '-'}</td></tr>",
            f"      <tr><th>{lbl_phone}</th><td>{cust.phone or '-'}</td></tr>",
            f"      <tr><th>{lbl_email}</th><td>{cust.email or '-'}</td></tr>",
            "    </table>",
            "  </div>",
            "</div>",
        ])
    else:
        html_lines.extend([
            f"<h2>{hdr_meta}</h2>",
            "<table>",
            f"<tr><th>{lbl_case_id}</th><td><strong>{case.case_id}</strong></td><th>{lbl_score}</th><td>{case.classification.calculated_score:.0f} Pkt. ({case.classification.urgency_level})</td></tr>",
            f"<tr><th>{lbl_status}</th><td>{status_disp}</td><th>{lbl_actor}</th><td>{actor_disp}</td></tr>",
            f"<tr><th>{lbl_created}</th><td>{created_str} ({case.created_by})</td><th>{lbl_deadline}</th><td>{deadline_str}</td></tr>",
            f"<tr><th>{lbl_followup}</th><td colspan='3'>{followup_str}</td></tr>",
            "</table>",
        ])

    if include_fields and case.form_data:
        html_lines.append(f"<h2>{hdr_fields}</h2>")
        html_lines.append("<div class='fields-grid'>")
        for k, v in case.form_data.items():
            v_str = str(v)
            val_disp = "<br>".join(v_str.splitlines()) if "\n" in v_str else v_str
            is_long = len(v_str) > REPORT_FIELD_LONG_TEXT_THRESHOLD or "\n" in v_str
            full_cls = " full-width" if is_long else ""
            html_lines.append(
                f"<div class='field-card{full_cls}'><div class='field-label'>{k}</div><div class='field-value'>{val_disp}</div></div>"
            )
        html_lines.append("</div>")

    entries_to_show = case.timeline if selected_entries is None else selected_entries
    if entries_to_show:
        html_lines.append(f"<h2>{hdr_timeline}</h2>")
        html_lines.append("<div class='timeline-list'>")
        for entry in entries_to_show:
            ts_str = format_german_datetime(entry.timestamp)
            note_html = "<br>".join(entry.note.splitlines())
            html_lines.append(
                f"<div class='entry'><div class='entry-header'>[{ts_str}] {entry.author} ({entry.channel}):</div><div class='entry-note'>{note_html}</div></div>"
            )
        html_lines.append("</div>")

    if include_attachments and attachment_service:
        try:
            att_files = attachment_service.list_attachments(case)
            if att_files:
                html_lines.append(f"<h2>{hdr_attachments}</h2>")
                img_exts = IMAGE_FILE_EXTENSIONS
                img_files = [f for f in att_files if f.suffix.lower() in img_exts]
                other_files = [f for f in att_files if f.suffix.lower() not in img_exts]

                if other_files:
                    html_lines.append(f"<table><tr><th>{lbl_filename}</th><th>{lbl_filesize}</th></tr>")
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
