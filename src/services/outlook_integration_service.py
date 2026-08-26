import os
import re
import urllib.parse
import webbrowser
from typing import Any
from models.case import Case, CaseCustomer, Classification, TimelineEntry
from utils.datetime_utils import get_local_now, now_iso


class OutlookIntegrationService:
    """Service for bidirectional integration between Support-Cockpit and Microsoft Outlook.

    1. Direct Mail Transfer: Opens drafted emails directly in Microsoft Outlook.
    2. Mail Import Bridge: Ingests Outlook emails to create new cases or attach events to active cases.
    3. Outlook Add-in / Macro specification.
    """

    @staticmethod
    def transfer_to_outlook(to_email: str, subject: str, body_text: str) -> bool:
        """Transfers email parameters directly to Microsoft Outlook using COM automation or mailto fallback."""
        try:
            import win32com.client  # type: ignore
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            if to_email:
                mail.To = to_email
            if subject:
                mail.Subject = subject
            if body_text:
                mail.Body = body_text
            mail.Display(True)
            return True
        except Exception:
            # Fallback to mailto protocol
            params = {}
            if subject:
                params["subject"] = subject
            if body_text:
                params["body"] = body_text
            query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            url = f"mailto:{to_email}?{query}" if to_email else f"mailto:?{query}"
            try:
                webbrowser.open(url)
                return True
            except Exception:
                return False

    @staticmethod
    def parse_outlook_email_to_case(
        subject: str,
        sender_email: str,
        sender_name: str,
        body: str,
        received_time: str | None = None,
        default_author: str = "Outlook-Import",
    ) -> Case:
        """Parses an Outlook email payload into a new Case object."""
        clean_subject = subject.strip() if subject else "E-Mail ohne Betreff"

        # Check for customer ID in subject/body (e.g. K-10482 or BSNR)
        cust_match = re.search(r"\b(K-\d{4,6})\b", f"{clean_subject} {body}")
        cust_id = cust_match.group(1) if cust_match else "K-OUTLOOK"

        practice_name = sender_name.strip() if sender_name else "Praxis " + (sender_email.split("@")[0] if "@" in sender_email else "Unbekannt")
        if not practice_name.startswith("Praxis ") and not practice_name.startswith("Dr."):
            practice_name = f"Praxis {practice_name}"

        timestamp = received_time or now_iso()

        case = Case(
            case_id=f"MAIL-{get_local_now().strftime('%Y%m%d%H%M%S')}",
            customer=CaseCustomer(
                customer_id=cust_id,
                practice_name=practice_name,
                contact_person=sender_name or sender_email,
                email=sender_email,
            ),
            classification=Classification(
                title=clean_subject[:80],
                schema_id="schema_quick",
            ),
            created_by=default_author,
            created_at=timestamp,
            form_data={
                "unformatted_description": body,
                "short_description": clean_subject,
            },
            timeline=[
                TimelineEntry(
                    timestamp=timestamp,
                    author=default_author,
                    channel="E-Mail",
                    note=f"E-Mail empfangen von {sender_name} <{sender_email}>:\n\n{body[:800]}...",
                )
            ],
        )
        return case

    @staticmethod
    def append_outlook_email_to_case_timeline(
        case: Case,
        sender_name: str,
        sender_email: str,
        subject: str,
        body: str,
        author: str = "Outlook-Import",
    ) -> TimelineEntry:
        """Attaches an incoming Outlook email as an event note to an existing case's timeline."""
        entry = TimelineEntry(
            timestamp=now_iso(),
            author=author,
            channel="E-Mail",
            note=f"E-Mail von {sender_name} <{sender_email}> (Betreff: {subject}):\n\n{body}",
        )
        case.timeline.append(entry)
        return entry

    @staticmethod
    def find_matching_case(subject: str, body: str, cases: list[Case]) -> Case | None:
        """Finds a matching case by scanning subject and body for case IDs (e.g. FALL-2026-0042, MAIL-123)."""
        search_text = f"{subject} {body}"
        # Try finding explicit case ID match in search text
        for case in cases:
            if case.case_id and case.case_id.lower() in search_text.lower():
                return case

        # Regex fallback for patterns like FALL-\d+ or MAIL-\d+
        match = re.search(r"\b((?:FALL|MAIL|TICKET)-\d+(?:-\d+)?)\b", search_text, re.IGNORECASE)
        if match:
            target_id = match.group(1).upper()
            for case in cases:
                if case.case_id.upper() == target_id:
                    return case

        return None

    @staticmethod
    def fetch_recent_emails(max_count: int = 15) -> list[dict[str, Any]]:
        """Fetches recent incoming emails from Microsoft Outlook via COM automation or provides demo emails."""
        emails = []
        try:
            import win32com.client  # type: ignore
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)  # Sort descending

            count = 0
            for item in messages:
                if count >= max_count:
                    break
                try:
                    # Verify item is mail
                    if hasattr(item, "Subject") and hasattr(item, "SenderEmailAddress"):
                        recv_time = str(item.ReceivedTime) if hasattr(item, "ReceivedTime") else now_iso()
                        emails.append({
                            "subject": str(item.Subject or "E-Mail ohne Betreff"),
                            "sender_name": str(getattr(item, "SenderName", "")),
                            "sender_email": str(getattr(item, "SenderEmailAddress", "")),
                            "body": str(getattr(item, "Body", "")),
                            "received_time": recv_time,
                        })
                        count += 1
                except Exception:
                    pass
        except Exception:
            # Fallback mock emails for demonstration/non-Windows environments
            emails = [
                {
                    "subject": "Dringend: Schnittstelle meldet Fehler (Ref: FALL-2026-0001)",
                    "sender_name": "Dr. Weber",
                    "sender_email": "praxis.weber@beispiel-med.de",
                    "body": "Hallo Support-Team,\n\nunsere COBRA-Schnittstelle bricht beim Datenimport ab. Bitte prüfen Sie den Vorfall.\n\nViele Grüße,\nDr. Weber",
                    "received_time": now_iso(),
                },
                {
                    "subject": "Neue Anfrage zu Abrechnung & Quartalsupdate",
                    "sender_name": "Praxis Dr. Müller",
                    "sender_email": "empfang@mueller-praxis.de",
                    "body": "Guten Tag,\n\nwir benötigen Hilfe bei der Konfiguration des neuen Abrechnungsmoduls.\n\nMit freundlichen Grüßen,\nFr. Schmidt",
                    "received_time": now_iso(),
                },
            ]
        return emails

    @staticmethod
    def get_outlook_vba_macro_code() -> str:
        """Returns VBA Macro code for Outlook Ribbon toolbar button to transfer emails into Support-Cockpit."""
        return (
            "' ==========================================================\n"
            "' Support-Cockpit Outlook Integration Macro\n"
            "' Fügen Sie dieses Makro in Outlook (Alt+F11 -> ThisOutlookSession) ein\n"
            "' und weisen Sie es einem Button im Menüband zu.\n"
            "' ==========================================================\n"
            "Sub TransferSelectedMailToSupportCockpit()\n"
            "    Dim objItem As Object\n"
            "    Dim objMail As Outlook.MailItem\n"
            "    Dim strTempJson As String\n"
            "    Dim strJsonData As String\n"
            "    Dim intFile As Integer\n"
            "    \n"
            "    If Application.ActiveExplorer.Selection.Count = 0 Then\n"
            "        MsgBox \"Bitte wählen Sie eine E-Mail aus.\", vbExclamation, \"Support-Cockpit\"\n"
            "        Exit Sub\n"
            "    End If\n"
            "    \n"
            "    Set objItem = Application.ActiveExplorer.Selection.Item(1)\n"
            "    If TypeOf objItem Is Outlook.MailItem Then\n"
            "        Set objMail = objItem\n"
            "        \n"
            "        strJsonData = \"{\" & _\n"
            "            \"\"\"sender_name\"\": \"\"\" & Replace(objMail.SenderName, \"\"\"\", \"\\\"\"\") & \"\"\",\"\"\" & _\n"
            "            \"\"\"sender_email\"\": \"\"\" & Replace(objMail.SenderEmailAddress, \"\"\"\", \"\\\"\"\") & \"\"\",\"\"\" & _\n"
            "            \"\"\"subject\"\": \"\"\" & Replace(objMail.Subject, \"\"\"\", \"\\\"\"\") & \"\"\",\"\"\" & _\n"
            "            \"\"\"body\"\": \"\"\" & Replace(Replace(objMail.Body, \"\"\"\", \"\\\"\"\"), vbCrLf, \"\\n\") & \"\"\"\" & _\n"
            "            \"}\"\n"
            "        \n"
            "        strTempJson = Environ(\"TEMP\") & \"\\support_cockpit_import.json\"\n"
            "        intFile = FreeFile\n"
            "        Open strTempJson For Output As #intFile\n"
            "        Print #intFile, strJsonData\n"
            "        Close #intFile\n"
            "        \n"
            "        Shell \"python -m ui.app --import-mail \"\"\" & strTempJson & \"\"\"\", vbNormalFocus\n"
            "    Else\n"
            "        MsgBox \"Das ausgewählte Element ist keine Standard-E-Mail.\", vbInformation, \"Support-Cockpit\"\n"
            "    End If\n"
            "End Sub\n"
        )
