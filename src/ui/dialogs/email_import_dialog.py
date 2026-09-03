import customtkinter as ctk
from typing import Callable, Any
from models.case import Case
from services.outlook_integration_service import OutlookIntegrationService
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES, DIALOG_HEADERS
from utils.ui_utils import center_window, enable_auto_hiding_scrollbar


class EmailImportDialog(ctk.CTkToplevel):
    """Dialog for inspecting incoming Outlook / IMAP emails and converting them into cases or timeline entries."""

    def __init__(
        self,
        parent,
        cases: list[Case],
        on_case_created: Callable[[Case], None],
        on_case_updated: Callable[[Case], None],
        author_name: str = "E-Mail Import",
    ):
        super().__init__(parent)
        self.cases = cases
        self.on_case_created = on_case_created
        self.on_case_updated = on_case_updated
        self.author_name = author_name

        self.title(DIALOG_TITLES["email_import"])
        w, h = DIALOG_DIMENSIONS["email_import"]
        self.geometry(f"{w}x{h}")
        self.minsize(750, 500)
        center_window(self, w, h)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        self.emails: list[dict[str, Any]] = []
        self.create_widgets()
        self.refresh_emails()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # Header bar
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            hdr_frame,
            text=DIALOG_HEADERS["email_import_hub"],
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        from services.i18n_service import tr

        ctk.CTkButton(
            hdr_frame,
            text=tr("email_import.refresh_btn", "🔄 Posteingang aktualisieren"),
            width=170,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.refresh_emails,
        ).pack(side="right")

        # Info label
        self.info_lbl = ctk.CTkLabel(
            main_frame,
            text=tr("email_import.info_msg", "Eingehende E-Mails aus Microsoft Outlook / Posteingang werden automatisch mit bestehenden Fällen abgeglichen."),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        )
        self.info_lbl.pack(fill="x", pady=(0, 6))

        # Status alert label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="dodgerblue")
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        # Scrollable email list container
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 8))
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Footer close button
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            footer_frame,
            text=tr("common.close", "Schließen"),
            width=100,
            height=30,
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
        ).pack(side="right")

    def refresh_emails(self):
        from services.i18n_service import tr
        self.status_lbl.configure(text=tr("email_import.fetching", "⏳ Rufe Posteingang ab..."))
        self.update_idletasks()

        self.emails = OutlookIntegrationService.fetch_recent_emails(max_count=15)
        self.render_email_list()
        self.status_lbl.configure(text=f"✓ {len(self.emails)} E-Mails aus Posteingang geladen.")

    def render_email_list(self):
        from services.i18n_service import tr
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.emails:
            ctk.CTkLabel(
                self.scroll_frame,
                text=tr("email_import.no_emails", "Keine neuen E-Mails im Posteingang gefunden."),
                font=ctk.CTkFont(size=13),
                text_color="gray",
            ).pack(pady=40)
            return

        for idx, mail in enumerate(self.emails):
            subj = mail.get("subject", "Ohne Betreff")
            sender_n = mail.get("sender_name", "")
            sender_e = mail.get("sender_email", "")
            body = mail.get("body", "")
            recv = mail.get("received_time", "")

            # Check for case auto-match
            matched_case = OutlookIntegrationService.find_matching_case(subj, body, self.cases)

            card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray22"), corner_radius=8)
            card.pack(fill="x", pady=5, padx=4)

            # Top header row of card
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))

            sender_disp = f"{sender_n} <{sender_e}>" if sender_n else sender_e
            ctk.CTkLabel(
                top_row,
                text=f"✉ {sender_disp}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(side="left")

            if recv:
                ctk.CTkLabel(
                    top_row,
                    text=str(recv)[:16],
                    font=ctk.CTkFont(size=10),
                    text_color="gray",
                ).pack(side="right")

            # Subject line
            ctk.CTkLabel(
                card,
                text=tr("email_import.subject_prefix", "Betreff: {subj}", subj=subj),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray20", "gray90"),
                anchor="w",
            ).pack(fill="x", padx=10, pady=(2, 2))

            # Auto-Match badge
            match_row = ctk.CTkFrame(card, fg_color="transparent")
            match_row.pack(fill="x", padx=10, pady=(2, 4))

            if matched_case:
                badge_txt = tr(
                    "email_import.auto_matched",
                    "🎯 Automatisch zugeordnet: Fall [{case_id}] — {practice_name}",
                    case_id=matched_case.case_id,
                    practice_name=matched_case.customer.practice_name,
                )
                badge_clr = "forestgreen"
            else:
                badge_txt = tr("email_import.no_match", "💡 Kein bestehender Fall zugeordnet (Neuer Fall empfohlen)")
                badge_clr = ("gray50", "gray60")

            ctk.CTkLabel(
                match_row,
                text=badge_txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=badge_clr,
                anchor="w",
            ).pack(side="left")

            # Snippet body text
            body_preview = body.strip().replace("\r", "")[:180] + ("..." if len(body) > 180 else "")
            ctk.CTkLabel(
                card,
                text=body_preview,
                font=ctk.CTkFont(size=10),
                text_color=("gray40", "gray70"),
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=10, pady=(0, 6))

            # Actions row
            act_row = ctk.CTkFrame(card, fg_color="transparent")
            act_row.pack(fill="x", padx=10, pady=(2, 8))

            if matched_case:
                ctk.CTkButton(
                    act_row,
                    text=tr("email_import.append_btn", "📌 An Fall [{case_id}] anhängen", case_id=matched_case.case_id),
                    fg_color="darkgreen",
                    hover_color="forestgreen",
                    height=28,
                    command=lambda m=mail, c=matched_case, i=idx: self.append_to_case(m, c, i),
                ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                act_row,
                text=tr("email_import.create_new_case", "➕ Als neuen Fall anlegen"),
                fg_color="dodgerblue",
                hover_color="deepskyblue",
                height=28,
                command=lambda m=mail, i=idx: self.create_new_case_from_mail(m, i),
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                act_row,
                text=tr("email_import.ignore", "🗑 Ignorieren"),
                fg_color=("gray75", "gray35"),
                hover_color=("gray65", "gray45"),
                width=80,
                height=28,
                command=lambda i=idx: self.ignore_mail(i),
            ).pack(side="right")

    def append_to_case(self, mail: dict[str, Any], case: Case, index: int):
        OutlookIntegrationService.append_outlook_email_to_case_timeline(
            case=case,
            sender_name=mail.get("sender_name", ""),
            sender_email=mail.get("sender_email", ""),
            subject=mail.get("subject", ""),
            body=mail.get("body", ""),
            author=self.author_name,
        )
        self.on_case_updated(case)
        self.status_lbl.configure(text=f"✓ E-Mail erfolgreich an Fall [{case.case_id}] angehängt.")
        self.ignore_mail(index)

    def create_new_case_from_mail(self, mail: dict[str, Any], index: int):
        new_case = OutlookIntegrationService.parse_outlook_email_to_case(
            subject=mail.get("subject", ""),
            sender_email=mail.get("sender_email", ""),
            sender_name=mail.get("sender_name", ""),
            body=mail.get("body", ""),
            received_time=mail.get("received_time"),
            default_author=self.author_name,
        )
        self.on_case_created(new_case)
        self.status_lbl.configure(text=f"✓ Neuer Fall [{new_case.case_id}] aus E-Mail erstellt.")
        self.ignore_mail(index)

    def ignore_mail(self, index: int):
        if 0 <= index < len(self.emails):
            self.emails.pop(index)
            self.render_email_list()
