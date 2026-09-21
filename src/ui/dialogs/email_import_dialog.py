import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from typing import Any
from collections.abc import Callable
from models.case import Case
from services.outlook_integration_service import OutlookIntegrationService
from constants import (
    BTN_HEIGHT_ACTION,
    BTN_HEIGHT_MD,
    BTN_WIDTH_CLOSE_SM,
    BTN_WIDTH_REFRESH_INBOX,
    BTN_WIDTH_SM,
    COLOR_BTN_CANCEL,
    COLOR_BTN_CANCEL_HOVER,
    COLOR_CARD_BG_SUBTLE,
    COLOR_DEEPSKYBLUE_HOVER,
    COLOR_EMAIL_SUBJECT_FG,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_PRIMARY_BLUE,
    COLOR_SNIPPET_PREVIEW_TEXT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_TAG_PILL_ADD_BG,
    COLOR_TAG_PILL_ADD_HOVER,
    COLOR_TEXT_BLUE,
    COLOR_TEXT_GRAY,
    CORNER_RADIUS_CARD,
    DEFAULT_AUTHOR_EMAIL_IMPORT,
    DIALOG_DIMENSIONS,
    DIALOG_HEADERS,
    DIALOG_MIN_SIZE_EMAIL_IMPORT,
    DIALOG_TITLES,
    EMAIL_BODY_PREVIEW_LEN,
    EMAIL_IMPORT_MAX_FETCH_COUNT,
    EMAIL_RECEIVED_TIME_PREVIEW_LEN,
    FONT_SIZE_BODY,
    FONT_SIZE_CONFIRM,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    PAD_10,
    PAD_15,
    PAD_4XL,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
)
from utils.ui_utils import enable_auto_hiding_scrollbar


class EmailImportDialog(BaseDialog):
    """Dialog for inspecting incoming Outlook / IMAP emails and converting them into cases or timeline entries."""

    def __init__(
        self,
        parent,
        cases: list[Case],
        on_case_created: Callable[[Case], None],
        on_case_updated: Callable[[Case], None],
        author_name: str = DEFAULT_AUTHOR_EMAIL_IMPORT,
    ):
        super().__init__(parent)
        self.cases = cases
        self.on_case_created = on_case_created
        self.on_case_updated = on_case_updated
        self.author_name = author_name

        w, h = DIALOG_DIMENSIONS["email_import"]
        self.setup_window(
            parent,
            DIALOG_TITLES["email_import"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_EMAIL_IMPORT,

            title_factory=lambda: DIALOG_TITLES["email_import"],
        )

        self.emails: list[dict[str, Any]] = []
        self.create_widgets()
        self.refresh_emails()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_LG)

        # Header bar
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        ctk.CTkLabel(
            hdr_frame,
            text=DIALOG_HEADERS["email_import_hub"],
            font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight=FONT_WEIGHT_BOLD),
        ).pack(side="left")

        from services.i18n_service import tr

        self.register_i18n(ctk.CTkButton(
            hdr_frame,
            text=tr("email_import.refresh_btn", "🔄 Posteingang aktualisieren"),
            width=BTN_WIDTH_REFRESH_INBOX,
            height=BTN_HEIGHT_MD,
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_MUTED_GRAY_HOVER,
            command=self.refresh_emails,
        ), "email_import.refresh_btn", "🔄 Posteingang aktualisieren").pack(side="right")

        # Info label
        self.info_lbl = self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("email_import.info_msg", "Eingehende E-Mails aus Microsoft Outlook / Posteingang werden automatisch mit bestehenden Fällen abgeglichen."),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_TEXT_GRAY,
            anchor="w",
        ), "email_import.info_msg", "Eingehende E-Mails aus Microsoft Outlook / Posteingang werden automatisch mit bestehenden Fällen abgeglichen.")
        self.info_lbl.pack(fill="x", pady=(PAD_NONE, PAD_GAP))

        # Status alert label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD), text_color=COLOR_TEXT_BLUE)
        self.status_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        # Scrollable email list container
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD))
        enable_auto_hiding_scrollbar(self.scroll_frame)

        # Footer close button
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(PAD_SM, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            footer_frame,
            text=tr("common.close", "Schließen"),
            width=BTN_WIDTH_CLOSE_SM,
            height=BTN_HEIGHT_ACTION,
            fg_color=COLOR_BTN_CANCEL,
            hover_color=COLOR_BTN_CANCEL_HOVER,
            command=self.destroy,
        ), "common.close", "Schließen").pack(side="right")

    def refresh_emails(self):
        from services.i18n_service import tr
        self.status_lbl.configure(text=tr("email_import.fetching", "⏳ Rufe Posteingang ab..."))
        self.update_idletasks()

        self.emails = OutlookIntegrationService.fetch_recent_emails(max_count=EMAIL_IMPORT_MAX_FETCH_COUNT)
        self.render_email_list()
        from services.i18n_service import tr
        self.status_lbl.configure(text=tr("email_import.loaded_count", "✓ {count} E-Mails aus Posteingang geladen.", count=len(self.emails)))

    def render_email_list(self):
        from services.i18n_service import tr
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.emails:
            self.register_i18n(ctk.CTkLabel(
                self.scroll_frame,
                text=tr("email_import.no_emails", "Keine neuen E-Mails im Posteingang gefunden."),
                font=ctk.CTkFont(size=FONT_SIZE_CONFIRM),
                text_color=COLOR_TEXT_GRAY,
            ), "email_import.no_emails", "Keine neuen E-Mails im Posteingang gefunden.").pack(pady=PAD_4XL)
            return

        for idx, mail in enumerate(self.emails):
            subj = mail.get("subject") or tr("email_import.no_subject", "Ohne Betreff")
            sender_n = mail.get("sender_name", "")
            sender_e = mail.get("sender_email", "")
            body = mail.get("body", "")
            recv = mail.get("received_time", "")

            # Check for case auto-match
            matched_case = OutlookIntegrationService.find_matching_case(subj, body, self.cases)

            card = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD_BG_SUBTLE, corner_radius=CORNER_RADIUS_CARD)
            card.pack(fill="x", pady=PAD_CONTAINER, padx=PAD_SM)

            # Top header row of card
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=PAD_10, pady=(PAD_MD, PAD_XS))

            sender_disp = f"{sender_n} <{sender_e}>" if sender_n else sender_e
            ctk.CTkLabel(
                top_row,
                text=f"✉ {sender_disp}",
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
                anchor="w",
            ).pack(side="left")

            if recv:
                ctk.CTkLabel(
                    top_row,
                    text=str(recv)[:EMAIL_RECEIVED_TIME_PREVIEW_LEN],
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_TEXT_GRAY,
                ).pack(side="right")

            # Subject line
            self.register_i18n(ctk.CTkLabel(
                card,
                text=tr("email_import.subject_prefix", "Betreff: {subj}", subj=subj),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
                text_color=COLOR_EMAIL_SUBJECT_FG,
                anchor="w",
            ), "email_import.subject_prefix", "Betreff: {subj}", subj=subj).pack(fill="x", padx=PAD_10, pady=(PAD_XS, PAD_XS))

            # Auto-Match badge
            match_row = ctk.CTkFrame(card, fg_color="transparent")
            match_row.pack(fill="x", padx=PAD_10, pady=(PAD_XS, PAD_SM))

            if matched_case:
                badge_txt = tr(
                    "email_import.auto_matched",
                    "🎯 Automatisch zugeordnet: Fall [{case_id}] — {practice_name}",
                    case_id=matched_case.case_id,
                    practice_name=matched_case.customer.practice_name,
                )
                badge_clr = COLOR_SUCCESS
            else:
                badge_txt = tr("email_import.no_match", "💡 Kein bestehender Fall zugeordnet (Neuer Fall empfohlen)")
                badge_clr = COLOR_MUTED_LABEL

            ctk.CTkLabel(
                match_row,
                text=badge_txt,
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                text_color=badge_clr,
                anchor="w",
            ).pack(side="left")

            # Snippet body text
            body_preview = body.strip().replace("\r", "")[:EMAIL_BODY_PREVIEW_LEN] + ("..." if len(body) > EMAIL_BODY_PREVIEW_LEN else "")
            ctk.CTkLabel(
                card,
                text=body_preview,
                font=ctk.CTkFont(size=FONT_SIZE_XS),
                text_color=COLOR_SNIPPET_PREVIEW_TEXT,
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_GAP))

            # Actions row
            act_row = ctk.CTkFrame(card, fg_color="transparent")
            act_row.pack(fill="x", padx=PAD_10, pady=(PAD_XS, PAD_MD))

            if matched_case:
                self.register_i18n(ctk.CTkButton(
                    act_row,
                    text=tr("email_import.append_btn", "📌 An Fall [{case_id}] anhängen", case_id=matched_case.case_id),
                    fg_color=COLOR_SUCCESS_HOVER,
                    hover_color=COLOR_SUCCESS,
                    height=BTN_HEIGHT_MD,
                    command=lambda m=mail, c=matched_case, i=idx: self.append_to_case(m, c, i),
                ), "email_import.append_btn", "📌 An Fall [{case_id}] anhängen", case_id=matched_case.case_id).pack(side="left", padx=(PAD_NONE, PAD_GAP))

            self.register_i18n(ctk.CTkButton(
                act_row,
                text=tr("email_import.create_new_case", "➕ Als neuen Fall anlegen"),
                fg_color=COLOR_PRIMARY_BLUE,
                hover_color=COLOR_DEEPSKYBLUE_HOVER,
                height=BTN_HEIGHT_MD,
                command=lambda m=mail, i=idx: self.create_new_case_from_mail(m, i),
            ), "email_import.create_new_case", "➕ Als neuen Fall anlegen").pack(side="left", padx=(PAD_NONE, PAD_GAP))

            self.register_i18n(ctk.CTkButton(
                act_row,
                text=tr("email_import.ignore", "🗑 Ignorieren"),
                fg_color=COLOR_TAG_PILL_ADD_BG,
                hover_color=COLOR_TAG_PILL_ADD_HOVER,
                width=BTN_WIDTH_SM,
                height=BTN_HEIGHT_MD,
                command=lambda i=idx: self.ignore_mail(i),
            ), "email_import.ignore", "🗑 Ignorieren").pack(side="right")

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
        from services.i18n_service import tr
        self.status_lbl.configure(text=tr("email_import.appended", "✓ E-Mail erfolgreich an Fall [{case_id}] angehängt.", case_id=case.case_id))
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
        from services.i18n_service import tr
        self.status_lbl.configure(text=tr("email_import.created_new_case", "✓ Neuer Fall [{case_id}] aus E-Mail erstellt.", case_id=new_case.case_id))
        self.ignore_mail(index)

    def ignore_mail(self, index: int):
        if 0 <= index < len(self.emails):
            self.emails.pop(index)
            self.render_email_list()
