import os
import re
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from models.case import Case


def format_utc_ics_timestamp(dt: datetime) -> str:
    """Formats a datetime object to UTC iCalendar timestamp string (YYYYMMDDTHHMMSSZ)."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


class CalendarEmailService:
    """Service for generating iCalendar (.ics) files and structured E-mail drafts."""

    def __init__(self, workspace_dir: Path | str | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()

    def generate_ics_content(self, case: Case, user_name: str = "") -> str:
        """Generates RFC 5545 compliant iCalendar string for a case deadline/followup."""
        now = datetime.now()
        dt_stamp = format_utc_ics_timestamp(now)

        # Parse start time from followup_due_at or fallback to now + 1 hour
        start_dt = now + timedelta(hours=1)
        if case.followup_due_at:
            try:
                # Try common formats: TT.MM.JJJJ HH:MM or ISO
                clean_str = case.followup_due_at.replace("Uhr", "").strip()
                if " " in clean_str:
                    d_part, t_part = clean_str.split(" ", 1)
                    if "." in d_part:
                        day, month, year = map(int, d_part.split("."))
                        hour, minute = map(int, t_part.split(":")[:2])
                        start_dt = datetime(year, month, day, hour, minute)
                    else:
                        start_dt = datetime.fromisoformat(clean_str)
            except Exception:
                pass

        end_dt = start_dt + timedelta(minutes=30)

        dt_start_str = format_utc_ics_timestamp(start_dt)
        dt_end_str = format_utc_ics_timestamp(end_dt)

        practice_name = case.customer.practice_name if case.customer else "Unbekannte Praxis"
        phone = getattr(case.customer, "phone", "") if case.customer else ""
        cust_id = case.customer.customer_id if case.customer else ""
        status_val = case.workflow_status.board_column if (case.workflow_status and hasattr(case.workflow_status, "board_column")) else "Offen"
        priority_val = case.classification.urgency_level if (case.classification and hasattr(case.classification, "urgency_level")) else "GRÜN"

        summary = f"[Fall {case.case_id}] Rückruf: {practice_name}"
        if case.title:
            summary += f" - {case.title}"

        desc_lines = [
            f"Support-Fall ID: {case.case_id}",
            f"Kunde / Praxis: {practice_name} ({cust_id})",
            f"Telefon: {phone}",
            f"Titel: {case.title}",
            f"Status: {status_val}",
            f"Priorität: {priority_val}",
            "",
            "Initiale Notiz / Beschreibung:",
            case.initial_note or case.form_data.get("description", "Keine Notiz"),
            "",
            f"Erstellt von: {user_name or case.created_by}",
        ]
        
        # Escape special iCalendar characters
        desc_text = "\\n".join(desc_lines).replace(",", "\\,").replace(";", "\\;")
        summary_escaped = summary.replace(",", "\\,").replace(";", "\\;")
        location_escaped = practice_name.replace(",", "\\,").replace(";", "\\;")

        uid = f"case_{case.case_id}_{now.strftime('%Y%m%d%H%M%S')}@support"

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//py-case-follow-up//Support Cockpit v1.0//DE",
            "CALSCALE:GREGORIAN",
            "METHOD:REQUEST",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dt_stamp}",
            f"DTSTART:{dt_start_str}",
            f"DTEND:{dt_end_str}",
            f"SUMMARY:{summary_escaped}",
            f"DESCRIPTION:{desc_text}",
            f"LOCATION:{location_escaped}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT15M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Erinnerung: Rückruf-Deadline in 15 Minuten",
            "END:VALARM",
            "END:VEVENT",
            "END:VCALENDAR",
        ]

        return "\r\n".join(ics_lines)

    def generate_ics_file(self, case: Case, target_dir: Path | str | None = None, user_name: str = "") -> Path:
        """Saves generated iCalendar content to a .ics file in target_dir or scratch dir."""
        content = self.generate_ics_content(case, user_name=user_name)
        out_dir = Path(target_dir) if target_dir else self.workspace_dir / "scratch"
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = f"Rueckruf_{case.case_id}.ics"
        file_path = out_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def generate_email_draft(self, case: Case, user_name: str = "") -> dict[str, str]:
        """Generates structured email draft components (to, subject, body)."""
        to_email = getattr(case.customer, "email", "") if case.customer else ""
        practice_name = case.customer.practice_name if case.customer else "Damen und Herren"
        from enums import get_board_column_display
        raw_status = case.workflow_status.board_column if (case.workflow_status and hasattr(case.workflow_status, "board_column")) else "Offen"
        status_val = get_board_column_display(raw_status)
        contact_person = getattr(case.customer, "contact_person", "") if case.customer else ""

        greeting = f"Hallo Frau/Herr {contact_person}," if contact_person else f"Sehr geehrte Damen und Herren ({practice_name}),"

        subject = f"[Fall {case.case_id}] Rückmeldung zu Ihrem Support-Anliegen"
        if case.title:
            subject += f": {case.title}"

        body_lines = [
            greeting,
            "",
            f"vielen Dank für Ihre Nachricht bezüglich Ihres Support-Anliegens (Fall-ID: {case.case_id}).",
            "",
            "--- ZUSAMMENFASSUNG / STATUS ---",
            f"Titel: {case.title}",
            f"Aktueller Status: {status_val}",
        ]

        if case.followup_due_at:
            body_lines.append(f"Geplante Rückruf-Deadline: {case.formatted_deadline}")


        body_lines.extend([
            "",
            "Geben Sie uns gerne Bescheid, wenn Sie hierzu Rückfragen haben oder uns weitere Informationen zur Verfügung stellen möchten.",
            "",
            "Mit freundlichen Grüßen",
            user_name or case.created_by or "Ihr Support-Team",
        ])

        return {
            "to": to_email,
            "subject": subject,
            "body": "\n".join(body_lines),
        }

    def open_mailto_link(self, to: str, subject: str, body: str) -> None:
        """Opens default email client with populated to, subject, and body."""
        encoded_subject = urllib.parse.quote(subject)
        encoded_body = urllib.parse.quote(body)
        mailto_url = f"mailto:{to}?subject={encoded_subject}&body={encoded_body}"

        try:
            webbrowser.open(mailto_url)
        except Exception:
            pass

    def open_ics_file(self, file_path: Path | str) -> None:
        """Opens .ics file using standard system default calendar application."""
        p_str = str(Path(file_path).resolve())
        try:
            if hasattr(os, "startfile"):
                os.startfile(p_str)
            else:
                webbrowser.open(f"file:///{p_str}")
        except Exception:
            pass
