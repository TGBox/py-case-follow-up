import os
import threading
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any
from collections.abc import Callable
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from models.case import Case
from models.customer import Customer
from services.ai_service import AiService
from services.calendar_email_service import CalendarEmailService, format_german_salutation
from utils.ui_utils import cancel_debounce, debounce, enable_auto_hiding_scrollbar
from constants import (
    AI_BTN_GENERATE_DRAFT,
    AI_BTN_GENERATE_DRAFT_DISABLED,
    AI_BTN_OPEN_ASSISTANT,
    AI_HINT_EMAIL_CUSTOM_INSTRUCTION,
    AI_LABEL_EMAIL_CUSTOM_INSTRUCTION,
    BORDER_WIDTH_CARD,
    BTN_HEIGHT_LG,
    BTN_HEIGHT_MD,
    BTN_HEIGHT_PILL,
    BTN_HEIGHT_SUGGESTION_CLOSE,
    BTN_WIDTH_CANCEL,
    BTN_WIDTH_CHOOSE_FILE,
    BTN_WIDTH_GENERATE_AI,
    BTN_WIDTH_PRAXISKARTEI,
    BTN_WIDTH_SUGGESTION_CLOSE,
    BTN_WIDTH_TAG_APPLY,
    COLOR_AI_PURPLE,
    COLOR_AI_PURPLE_HOVER,
    COLOR_BTN_CANCEL,
    COLOR_BTN_CANCEL_HOVER,
    COLOR_BTN_GRAY,
    COLOR_BTN_GRAY_HOVER,
    COLOR_BTN_MANAGE_TAGS,
    COLOR_BTN_MANAGE_TAGS_HOVER,
    COLOR_BTN_SECONDARY,
    COLOR_CARD_ALT_BG,
    COLOR_CARD_BG_SUGGESTION,
    COLOR_CARD_BORDER_DEFAULT,
    COLOR_DANGER,
    COLOR_DANGER_ALT,
    COLOR_MAGENTA_HOVER,
    COLOR_MUTED_GRAY,
    COLOR_MUTED_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_OUTLOOK_BLUE,
    COLOR_OUTLOOK_HOVER,
    COLOR_OVERLAY_BG,
    COLOR_PROGRESS_INDETERMINATE,
    COLOR_SUCCESS_ALT,
    COLOR_SUGGESTIONS_BG,
    COLOR_TAG_PICKER_BTN_BG,
    COLOR_TEXT_BLUE,
    COLOR_TOAST_BORDER,
    COLOR_TOAST_BTN_HOVER,
    COLOR_WARNING_ALT,
    COLOR_WIKI_LINK,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_LG,
    CORNER_RADIUS_MD,
    CURSOR_HAND,
    DEBOUNCE_KEY_RECIPIENT_SEARCH,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_EMAIL_DRAFT,
    DIALOG_TITLES,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    HEIGHT_SUGGESTIONS_SCROLL,
    MAX_SUGGESTIONS_COUNT,
    OVERLAY_CARD_HEIGHT,
    OVERLAY_CARD_WIDTH,
    PAD_2XL,
    PAD_LG,
    PAD_MD,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    PROGRESS_BAR_WIDTH_MD,
    SEARCH_DEBOUNCE_MS,
    TEXTBOX_HEIGHT_EMAIL_BODY,
)


class EmailDraftDialog(BaseDialog):
    """Standalone dialog for preparing and dispatching support emails with integrated AI text generation."""

    def __init__(
        self,
        parent,
        case: Case | None = None,
        calendar_email_service: CalendarEmailService | None = None,
        user_name: str = "",
        snippet_service: Any | None = None,
        customers: list[Customer] | None = None,
        storage_service: Any | None = None,
        profile: Any | None = None,
        on_case_updated: Callable[[Case], None] | None = None,
    ):
        super().__init__(parent)
        self.case = case
        self.service = calendar_email_service or CalendarEmailService()
        self.on_case_updated = on_case_updated

        # Initialize AI service
        ai_set = getattr(profile, 'ai_settings', None)
        provider = getattr(ai_set, 'provider', 'OLLAMA') if ai_set else 'OLLAMA'
        ollama_url = getattr(ai_set, 'ollama_url', DEFAULT_OLLAMA_URL) if ai_set else DEFAULT_OLLAMA_URL
        model_name = getattr(ai_set, 'model_name', DEFAULT_OLLAMA_MODEL) if ai_set else DEFAULT_OLLAMA_MODEL
        gemini_key = getattr(ai_set, 'gemini_api_key', '') if ai_set else ''
        gemini_mod = getattr(ai_set, 'gemini_model', 'gemini-1.5-flash') if ai_set else 'gemini-1.5-flash'
        enable_anon = getattr(ai_set, 'enable_anonymization', True) if ai_set else True

        self.ai_service = AiService(
            provider=provider,
            ollama_url=ollama_url,
            model_name=model_name,
            gemini_api_key=gemini_key,
            gemini_model=gemini_mod,
            enable_anonymization=enable_anon,
        )
        self.user_name = user_name
        self.snippet_service = snippet_service
        self.storage_service = storage_service
        self.profile = profile

        # Load customers for Praxiskartei autocomplete if not passed
        if customers is not None:
            self.customers = list(customers)
        elif self.storage_service and hasattr(self.storage_service, "load_customers"):
            try:
                self.customers = self.storage_service.load_customers()
            except Exception:
                self.customers = []
        else:
            self.customers = []

        # Pre-build list of searchable contacts
        self.all_contacts: list[dict[str, str]] = []
        for c in self.customers:
            p_name = c.practice_name
            c_id = c.customer_id
            emails = getattr(c, "all_emails", [getattr(c, "email", "")]) if hasattr(c, "all_emails") else [getattr(c, "email", "")]
            c_person = getattr(c, "contact_person", "")
            for em in emails:
                if em:
                    self.all_contacts.append({
                        "email": em,
                        "name": c_person,
                        "practice": p_name,
                        "cust_id": c_id,
                        "search_key": f"{c_person} {em} {p_name} {c_id}".lower(),
                    })

        from services.i18n_service import tr

        def _window_title() -> str:
            if case:
                return tr("email_draft.window_title_case", "{base_title} - Fall {case_id}", base_title=DIALOG_TITLES["email_draft"], case_id=case.case_id)
            return tr("email_draft.window_title_new", "{base_title} (Neuer Entwurf)", base_title=DIALOG_TITLES["email_draft"])

        dialog_title = _window_title()
        w, h = DIALOG_DIMENSIONS["email_draft"]
        self.setup_window(
            parent,
            dialog_title,
            (w, h),
            min_size=DIALOG_MIN_SIZE_EMAIL_DRAFT,
            title_factory=_window_title,
        )

        sig = self.profile.user.email_signature if (self.profile and hasattr(self.profile, "user") and hasattr(self.profile.user, "email_signature")) else ""
        self.draft_data = self.service.generate_email_draft(self.case, user_name=self.user_name, customers=self.customers, signature=sig)
        self.create_widgets()
        self._create_loading_overlay()
        self._update_ollama_status_async()
        # A written draft is the most painful thing to lose, so Escape and the
        # X button ask before discarding it.
        self.enable_unsaved_guard()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_LG + 3, pady=PAD_LG)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, PAD_MD))

        hdr_top_row = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        hdr_top_row.pack(fill="x")

        from services.i18n_service import tr

        if self.case:
            title_text = tr("email_draft.header_title_case", "✉ E-Mail verfassen (Fall {case_id})", case_id=self.case.case_id)
            practice_name = self.case.customer.practice_name if self.case.customer else tr("common.unknown_practice", "Unbekannte Praxis")
            deadline_str = self.case.formatted_deadline or tr("common.no_deadline_set", "Keine Deadline gesetzt")
            sub_text = tr("email_draft.sub_header_case", "Praxis: {practice} | Rückruf-Deadline: {deadline}", practice=practice_name, deadline=deadline_str)
        else:
            title_text = tr("email_draft.header_title_new", "✉ E-Mail verfassen (Freier Entwurf)")
            sub_text = tr("email_draft.sub_header_free", "Freier Entwurf | Empfänger aus Praxiskartei wählen oder frei eingeben")

        ctk.CTkLabel(
            hdr_top_row,
            text=title_text,
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD),
        ).pack(side="left")

        # Ollama Status Badge
        self.ollama_status_badge = self.register_i18n(ctk.CTkLabel(
            hdr_top_row,
            text=tr("email_draft.checking_ai", "Prüfe KI-Status..."),
            font=ctk.CTkFont(size=FONT_SIZE_XS, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_MUTED_LABEL,
        ), "email_draft.checking_ai", "Prüfe KI-Status...")
        self.ollama_status_badge.pack(side="right")

        ctk.CTkLabel(
            hdr_frame,
            text=sub_text,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
        ).pack(anchor="w")

        # Scrollable Content Box
        content_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        content_scroll.pack(fill="both", expand=True, pady=(0, PAD_MD))
        self.content_scroll = content_scroll
        enable_auto_hiding_scrollbar(content_scroll)

        # Recipient Email Header & Row
        self.register_i18n(ctk.CTkLabel(
            content_scroll,
            text=tr("email_draft.recipient_lbl", "Empfänger (E-Mail):"),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        ), "email_draft.recipient_lbl", "Empfänger (E-Mail):").pack(anchor="w", pady=(PAD_XS, PAD_TINY))

        self.to_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        self.to_row.pack(fill="x", pady=(0, PAD_SM))

        self.to_entry = self.register_i18n(ctk.CTkEntry(
            self.to_row,
            placeholder_text=tr("email_draft.to_placeholder", "praxis@beispiel.de oder Name / Praxis eingeben..."),
        ), "email_draft.to_placeholder", "praxis@beispiel.de oder Name / Praxis eingeben...", attr="placeholder_text")
        if self.draft_data.get("to"):
            self.to_entry.insert(0, self.draft_data["to"])
        self.to_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_MD - PAD_XS))
        self.to_entry.bind("<KeyRelease>", self._on_to_keyrelease)
        # "break" keeps Escape from bubbling up to the dialog's close binding:
        # in the To field Escape only closes the autocomplete list, never the draft.
        self.to_entry.bind("<Escape>", self._on_to_escape)

        self.praxis_btn = self.register_i18n(ctk.CTkButton(
            self.to_row,
            text=tr("email_draft.practice_card_btn", "Praxiskartei ▾"),
            width=BTN_WIDTH_PRAXISKARTEI,
            height=BTN_HEIGHT_MD,
            fg_color=COLOR_BTN_MANAGE_TAGS,
            hover_color=COLOR_BTN_MANAGE_TAGS_HOVER,
            command=self.toggle_praxiskartei_dropdown,
        ), "email_draft.practice_card_btn", "Praxiskartei ▾")
        self.praxis_btn.pack(side="right")

        # Expandable Live Autocomplete / Suggestions Card
        self.suggestions_frame = ctk.CTkFrame(
            content_scroll,
            fg_color=COLOR_SUGGESTIONS_BG,
            corner_radius=CORNER_RADIUS_CARD,
            border_width=BORDER_WIDTH_CARD,
            border_color=COLOR_CARD_BORDER_DEFAULT,
        )
        # Suggestions frame starts hidden
        self.suggestions_frame_visible = False

        sug_hdr = ctk.CTkFrame(self.suggestions_frame, fg_color="transparent")
        sug_hdr.pack(fill="x", padx=PAD_MD, pady=(PAD_MD - PAD_XS, PAD_XS))

        self.suggestions_title = self.register_i18n(ctk.CTkLabel(
            sug_hdr,
            text=tr("email_draft.suggestions_title", "Kontakte aus Praxiskartei (Klicken zum Übernehmen):"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        ), "email_draft.suggestions_title", "Kontakte aus Praxiskartei (Klicken zum Übernehmen):")
        self.suggestions_title.pack(side="left", fill="x", expand=True)

        self.register_i18n(ctk.CTkButton(
            sug_hdr,
            text=tr("email_draft.close_btn", "Schließen"),
            width=BTN_WIDTH_SUGGESTION_CLOSE,
            height=BTN_HEIGHT_SUGGESTION_CLOSE,
            font=ctk.CTkFont(size=FONT_SIZE_XS),
            fg_color=COLOR_BTN_GRAY,
            hover_color=COLOR_BTN_GRAY_HOVER,
            command=self.hide_suggestions,
        ), "email_draft.close_btn", "Schließen").pack(side="right")

        self.suggestions_scroll = ctk.CTkScrollableFrame(
            self.suggestions_frame,
            height=HEIGHT_SUGGESTIONS_SCROLL,
            fg_color="transparent",
        )
        self.suggestions_scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=(PAD_XS, PAD_MD - PAD_XS))

        # Subject
        self.register_i18n(ctk.CTkLabel(content_scroll, text=tr("email_draft.subject_lbl", "Betreff:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "email_draft.subject_lbl", "Betreff:").pack(anchor="w", pady=(PAD_SM, PAD_TINY))
        self.subject_entry = self.register_i18n(ctk.CTkEntry(content_scroll, placeholder_text=tr("email_draft.subject_placeholder", "Betreff eingeben...")), "email_draft.subject_placeholder", "Betreff eingeben...", attr="placeholder_text")
        if self.draft_data.get("subject"):
            self.subject_entry.insert(0, self.draft_data["subject"])
        self.subject_entry.pack(fill="x", pady=(0, PAD_MD - PAD_XS))

        # Body Textbox Control Row
        body_hdr_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        body_hdr_row.pack(fill="x", pady=(PAD_SM, PAD_TINY))

        self.register_i18n(ctk.CTkLabel(body_hdr_row, text=tr("email_draft.body_lbl", "E-Mail Nachrichtentext:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "email_draft.body_lbl", "E-Mail Nachrichtentext:").pack(side="left")

        if self.snippet_service:
            self.register_i18n(ctk.CTkButton(
                body_hdr_row,
                text=tr("email_draft.snippet_btn", "Textbaustein"),
                width=BTN_WIDTH_CHOOSE_FILE,
                height=BTN_HEIGHT_PILL,
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_MAGENTA_HOVER,
                command=self.open_snippet_picker,
            ), "email_draft.snippet_btn", "🧩 Textbaustein").pack(side="right")

        # Priority Custom Instruction Bar for Email KI
        ci_frame = ctk.CTkFrame(content_scroll, fg_color=COLOR_CARD_ALT_BG, corner_radius=CORNER_RADIUS_MD)
        ci_frame.pack(fill="x", pady=(PAD_XS, PAD_SM))

        self.register_i18n(ctk.CTkLabel(
            ci_frame,
            text=tr("email_draft.custom_instruction", AI_LABEL_EMAIL_CUSTOM_INSTRUCTION),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_BLUE,
        ), "email_draft.custom_instruction", AI_LABEL_EMAIL_CUSTOM_INSTRUCTION).pack(side="left", padx=(PAD_MD + PAD_XS, PAD_SM), pady=PAD_SM)

        self.custom_instruction_entry = self.register_i18n(ctk.CTkEntry(
            ci_frame,
            placeholder_text=tr("email_draft.custom_hint", AI_HINT_EMAIL_CUSTOM_INSTRUCTION),
            height=BTN_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        ), "email_draft.custom_hint", AI_HINT_EMAIL_CUSTOM_INSTRUCTION, attr="placeholder_text")
        self.custom_instruction_entry.pack(side="left", fill="x", expand=True, padx=(0, PAD_MD), pady=PAD_SM)

        # KI Buttons Row
        ki_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        ki_row.pack(fill="x", pady=(PAD_XS, PAD_SM))

        ai_enabled = bool(self.profile.ai_settings.enable_ai) if (self.profile and hasattr(self.profile, "ai_settings")) else True

        self.ki_generate_btn = ctk.CTkButton(
            ki_row,
            text=AI_BTN_GENERATE_DRAFT if ai_enabled else tr("email_draft.draft_btn_disabled", AI_BTN_GENERATE_DRAFT_DISABLED),
            width=BTN_WIDTH_GENERATE_AI,
            height=BTN_HEIGHT_MD,
            fg_color=COLOR_AI_PURPLE if ai_enabled else COLOR_BTN_GRAY,
            hover_color=COLOR_AI_PURPLE_HOVER if ai_enabled else COLOR_BTN_GRAY,
            state="normal" if ai_enabled else "disabled",
            command=self._on_generate_ai_draft,
        )
        self.ki_generate_btn.pack(side="left", padx=(0, PAD_MD - PAD_XS))

        if self.case:
            self.register_i18n(ctk.CTkButton(
                ki_row,
                text=tr("email_draft.open_assistant_btn", AI_BTN_OPEN_ASSISTANT),
                width=BTN_WIDTH_TAG_APPLY,
                height=BTN_HEIGHT_MD,
                fg_color=COLOR_MUTED_GRAY,
                hover_color=COLOR_MUTED_HOVER,
                command=self._open_ai_assistant_dialog,
            ), "email_draft.open_assistant_btn", AI_BTN_OPEN_ASSISTANT).pack(side="left")

        self.body_textbox = ctk.CTkTextbox(content_scroll, height=TEXTBOX_HEIGHT_EMAIL_BODY)
        if self.draft_data.get("body"):
            self.body_textbox.insert("1.0", self.draft_data["body"])
        self.body_textbox.pack(fill="x", expand=True, pady=(0, PAD_MD - PAD_XS))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_WIKI_LINK)
        self.status_lbl.pack(anchor="w", pady=(0, PAD_SM))

        from services.i18n_service import tr

        # Action Buttons
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(PAD_SM, 0))

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("email_draft.open_mailto", "In Standard-Mail-App öffnen"),
            fg_color=COLOR_TOAST_BORDER,
            hover_color=COLOR_TOAST_BTN_HOVER,
            command=self.on_open_mailto,
            height=BTN_HEIGHT_LG,
        ), "email_draft.open_mailto", "In Standard-Mail-App öffnen").pack(side="left", padx=(0, PAD_MD))

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("email_draft.transfer_outlook", "In Outlook übertragen"),
            fg_color=COLOR_OUTLOOK_BLUE,
            hover_color=COLOR_OUTLOOK_HOVER,
            command=self.on_transfer_to_outlook,
            height=BTN_HEIGHT_LG,
        ), "email_draft.transfer_outlook", "In Outlook übertragen").pack(side="left", padx=(0, PAD_MD))

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("ui_buttons.copy_clipboard", "In Zwischenablage kopieren"),
            fg_color=COLOR_BTN_MANAGE_TAGS,
            hover_color=COLOR_BTN_MANAGE_TAGS_HOVER,
            command=self.on_copy_text,
            height=BTN_HEIGHT_LG,
        ), "ui_buttons.copy_clipboard", "In Zwischenablage kopieren").pack(side="left")

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=COLOR_BTN_CANCEL,
            hover_color=COLOR_BTN_CANCEL_HOVER,
            command=self.destroy,
            width=BTN_WIDTH_CANCEL,
            height=BTN_HEIGHT_LG,
        ), "common.cancel", "Abbrechen").pack(side="right")

    # --- Autocomplete & Praxiskartei Logic ---

    def _on_to_escape(self, event=None):
        self.hide_suggestions()
        return "break"

    def _on_to_keyrelease(self, event=None):
        # Escape und ein geleertes Feld wirken sofort - wer die Vorschlagsliste
        # wegdrueckt, will nicht erst auf einen Timer warten. hide_suggestions
        # bricht dabei auch eine schon wartende Suche ab.
        if event and event.keysym == "Escape":
            self.hide_suggestions()
            return

        if not self.to_entry.get().strip():
            self.hide_suggestions()
            return

        debounce(self, DEBOUNCE_KEY_RECIPIENT_SEARCH, SEARCH_DEBOUNCE_MS, self._render_recipient_suggestions)

    def _render_recipient_suggestions(self):
        query = self.to_entry.get().strip().lower()
        if not query:
            self.hide_suggestions()
            return

        from services.i18n_service import tr
        matches = [c for c in self.all_contacts if query in c["search_key"]]
        if matches:
            self.show_suggestions(matches, query_hint=tr("email_draft.search_hint", "Treffer für '{query}':", query=query))
        else:
            self.hide_suggestions()

    def toggle_praxiskartei_dropdown(self):
        if self.suggestions_frame_visible:
            self.hide_suggestions()
        else:
            from services.i18n_service import tr
            self.show_suggestions(self.all_contacts, query_hint=tr("email_draft.all_contacts_hint", "Alle Kontakte aus der Praxiskartei:"))

    def show_suggestions(self, contacts: list[dict[str, str]], query_hint: str = ""):
        from services.i18n_service import tr
        for w in self.suggestions_scroll.winfo_children():
            w.destroy()

        if query_hint:
            self.suggestions_title.configure(text=tr("email_draft.suggestions_count", "🔍 {hint} ({count})", hint=query_hint, count=len(contacts)))

        if not contacts:
            self.register_i18n(ctk.CTkLabel(
                self.suggestions_scroll,
                text=tr("email_draft.no_contacts_found", "Keine passenden Praxiskontakte gefunden."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_MUTED_LABEL,
            ), "email_draft.no_contacts_found", "Keine passenden Praxiskontakte gefunden.").pack(pady=PAD_MD + PAD_XS)
        else:
            for item in contacts[:MAX_SUGGESTIONS_COUNT]:
                card = ctk.CTkFrame(self.suggestions_scroll, fg_color=COLOR_CARD_BG_SUGGESTION, corner_radius=CORNER_RADIUS_MD, cursor=CURSOR_HAND)
                card.pack(fill="x", pady=PAD_XS, padx=PAD_XS)

                contact_name = item.get("name", "")
                email = item.get("email", "")
                practice = item.get("practice", "")
                cust_id = item.get("cust_id", "")

                contact_disp = f"👤 {contact_name}" if contact_name else tr("email_draft.generic_practice", "🏥 Praxis")
                email_disp = f"<{email}>" if email else tr("email_draft.no_email", "(keine E-Mail)")
                top_text = f"{contact_disp} {email_disp}"
                sub_text = tr("email_draft.practice_id_line", "Praxis: {practice} ({id})", practice=practice, id=cust_id)

                top_lbl = ctk.CTkLabel(
                    card,
                    text=top_text,
                    font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
                    anchor="w"
                )
                top_lbl.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, 0))

                sub_lbl = ctk.CTkLabel(
                    card,
                    text=sub_text,
                    font=ctk.CTkFont(size=FONT_SIZE_XS),
                    text_color=COLOR_MUTED_LABEL,
                    anchor="w"
                )
                sub_lbl.pack(fill="x", padx=PAD_MD, pady=(0, PAD_SM))

                # Click binding
                for elem in (card, top_lbl, sub_lbl):
                    elem.bind("<Button-1>", lambda e, it=item: self.select_contact(it))

        if not self.suggestions_frame_visible:
            self.suggestions_frame.pack(fill="x", pady=(0, PAD_MD), after=self.to_row)
            self.suggestions_frame_visible = True

    def hide_suggestions(self):
        # Jeder Weg, der die Liste schliesst, laeuft hier durch: Escape, der
        # Schliessen-Knopf, die Auswahl eines Kontakts. Eine noch wartende
        # Suche wuerde die Liste sonst kurz darauf wieder aufklappen.
        cancel_debounce(self, DEBOUNCE_KEY_RECIPIENT_SEARCH)

        if self.suggestions_frame_visible:
            self.suggestions_frame.pack_forget()
            self.suggestions_frame_visible = False

    def select_contact(self, contact: dict[str, str]):
        email = contact.get("email", "")
        name = contact.get("name", "")
        practice = contact.get("practice", "")

        self.to_entry.delete(0, "end")
        self.to_entry.insert(0, email)

        # Automatically update salutation in email body
        self.update_salutation_in_body(name, practice)

        self.hide_suggestions()
        from services.i18n_service import tr
        display_name = name or practice
        self.status_lbl.configure(text=tr("email_draft.recipient_set", "✓ Empfänger gesetzt: {name} <{email}>", name=display_name, email=email))

    def update_salutation_in_body(self, contact_name: str, practice_name: str):
        from services.i18n_service import tr
        new_salutation = format_german_salutation(contact_name, practice_name)
        curr_body = self.body_textbox.get("1.0", "end-1c")

        if not curr_body.strip():
            signoff = tr("email_draft.default_signoff", "Mit freundlichen Grüßen")
            sender = self.user_name or tr("email_draft.default_sender", "Ihr Support-Team")
            self.body_textbox.insert("1.0", f"{new_salutation}\n\n\n\n{signoff}\n{sender}")
            return

        lines = curr_body.split("\n")
        # Replace the first greeting line
        lines[0] = new_salutation
        self.body_textbox.delete("1.0", "end")
        self.body_textbox.insert("1.0", "\n".join(lines))

    # --- Actions ---

    def open_snippet_picker(self):
        if not self.snippet_service:
            return
        from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
        SnippetPickerDialog(
            self,
            self.snippet_service,
            on_snippet_selected=self.insert_snippet_text,
        )

    def insert_snippet_text(self, text: str):
        from services.i18n_service import tr
        self.body_textbox.insert("insert", text)
        self.status_lbl.configure(text=tr("email_draft.snippet_inserted", "✓ Textbaustein eingefügt."))

    def on_open_mailto(self):
        from services.i18n_service import tr
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        params = {}
        if subject:
            params["subject"] = subject
        if body:
            params["body"] = body

        query_str = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        mailto_url = f"mailto:{to}?{query_str}" if to else f"mailto:?{query_str}"

        try:
            webbrowser.open(mailto_url)
            self.status_lbl.configure(text=tr("email_draft.mailto_opened", "✓ Standard-Mail-Programm aufgerufen."))
        except Exception as e:
            self.status_lbl.configure(text=tr("email_draft.error_open", "Fehler beim Öffnen: {error}", error=e))

    def on_transfer_to_outlook(self):
        """Transfers the drafted email directly into Microsoft Outlook."""
        from services.i18n_service import tr
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        # First attempt: Windows COM automation for Outlook if available
        success = False
        try:
            import win32com.client  # type: ignore
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            if to:
                mail.To = to
            if subject:
                mail.Subject = subject
            if body:
                mail.Body = body
            mail.Display(True)  # Display the Outlook Inspector window
            success = True
            self.status_lbl.configure(text=tr("email_draft.outlook_opened", "✓ E-Mail erfolgreich in Outlook geöffnet."))
        except Exception:
            success = False

        if not success:
            # Fallback: Generate an .eml draft file and launch system default handler
            try:
                import tempfile
                import email.message

                msg = email.message.EmailMessage()
                if to:
                    msg["To"] = to
                if subject:
                    msg["Subject"] = subject
                msg.set_content(body)

                temp_dir = Path(tempfile.gettempdir())
                eml_path = temp_dir / "Support_Entwurf.eml"
                with open(eml_path, "wb") as f:
                    f.write(msg.as_bytes())

                if hasattr(os, "startfile"):
                    os.startfile(str(eml_path))
                else:
                    webbrowser.open(f"file:///{eml_path.resolve()}")
                self.status_lbl.configure(text=tr("email_draft.eml_handed_over", "✓ E-Mail-Entwurf an E-Mail-Client übergeben (.eml)."))
            except Exception as e:
                self.status_lbl.configure(text=tr("email_draft.error_outlook_transfer", "Fehler bei Outlook-Übergabe: {error}", error=e))

    def on_copy_text(self):
        from services.i18n_service import tr
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        formatted = tr("email_draft.clipboard_format", "An: {to}\nBetreff: {subject}\n\n{body}", to=to, subject=subject, body=body)
        try:
            self.clipboard_clear()
            self.clipboard_append(formatted)
            self.status_lbl.configure(text=tr("email_draft.copied_to_clipboard", "✓ E-Mail in Zwischenablage kopiert."))
        except Exception as e:
            self.status_lbl.configure(text=tr("email_draft.error_copy", "Kopieren fehlgeschlagen: {error}", error=e))

    # --- AI / KI Integration ---

    def _create_loading_overlay(self):
        """Creates a semi-transparent loading overlay for AI generation."""
        from services.i18n_service import tr
        self._overlay_frame = ctk.CTkFrame(self, fg_color=COLOR_OVERLAY_BG)

        card = ctk.CTkFrame(self._overlay_frame, fg_color=COLOR_TAG_PICKER_BTN_BG, corner_radius=CORNER_RADIUS_LG, width=OVERLAY_CARD_WIDTH, height=OVERLAY_CARD_HEIGHT)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self._overlay_msg_lbl = self.register_i18n(ctk.CTkLabel(
            card,
            text=tr("email_draft.ai_generating", "🤖 KI generiert E-Mail-Entwurf..."),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
        ), "email_draft.ai_generating", "🤖 KI generiert E-Mail-Entwurf...")
        self._overlay_msg_lbl.pack(pady=(PAD_2XL, PAD_MD + PAD_XS))

        self._overlay_progress = ctk.CTkProgressBar(card, width=PROGRESS_BAR_WIDTH_MD, mode="indeterminate", progress_color=COLOR_PROGRESS_INDETERMINATE)
        self._overlay_progress.pack(pady=(0, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(
            card,
            text=tr("email_draft.ai_please_wait", "Bitte einen Moment gedulden — Modell generiert Antwort"),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
        ), "email_draft.ai_please_wait", "Bitte einen Moment gedulden — Modell generiert Antwort").pack(pady=(0, PAD_LG + 3))

    def _show_overlay(self, message: str | None = None):
        from services.i18n_service import tr
        if message is None:
            message = tr("email_draft.ai_generating", "🤖 KI generiert E-Mail-Entwurf...")
        self._overlay_msg_lbl.configure(text=message)
        self._overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay_progress.start()
        self.update_idletasks()

    def _hide_overlay(self):
        try:
            self._overlay_progress.stop()
            self._overlay_frame.place_forget()
        except Exception:
            pass

    def _update_ollama_status_async(self):
        """Checks AI provider status in a background thread and updates the status badge."""
        def thread_target():
            from services.i18n_service import tr
            is_online = False
            badge_text = tr("email_draft.ai_status_rule_based", "⚡ Regelbasierter Modus (KI Offline/Ohne Key)")
            badge_color = COLOR_WIKI_LINK

            try:
                if self.ai_service.provider == "GEMINI":
                    is_online, msg = self.ai_service.check_gemini_status()
                    if is_online:
                        badge_text = tr("email_draft.ai_status_gemini_active", "🟢 Gemini aktiv ({model} | Anonymisiert)", model=self.ai_service.gemini_model)
                        badge_color = COLOR_SUCCESS_ALT
                    else:
                        badge_text = tr("email_draft.ai_status_gemini_invalid", "🔴 Gemini API Key ungültig / offline")
                        badge_color = COLOR_DANGER_ALT
                else:
                    is_online, models = self.ai_service.check_ollama_status()
                    if is_online:
                        badge_text = tr("email_draft.ai_status_ollama_active", "🟢 Ollama aktiv ({model})", model=self.ai_service.model_name)
                        badge_color = COLOR_SUCCESS_ALT
            except Exception:
                pass

            def ui_callback():
                try:
                    if getattr(self, "_destroyed", False) or not self.winfo_exists():
                        return
                    self.ollama_status_badge.configure(
                        text=badge_text,
                        text_color=badge_color,
                    )
                except Exception:
                    pass

            try:
                if not getattr(self, "_destroyed", False):
                    self.after(0, ui_callback)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_generate_ai_draft(self):
        """Generates an AI-powered email draft and fills the body textbox."""
        from services.i18n_service import tr
        if not self.case:
            self.status_lbl.configure(text=tr("email_draft.case_required_for_ai", "⚠ KI-Entwurf benötigt einen aktiven Fall."), text_color=COLOR_WARNING_ALT)
            return

        # Bind the None-checked case to a local now: self.case is a plain
        # attribute, so the "if not self.case: return" guard above doesn't
        # narrow it inside worker(), a nested function that could run after
        # self.case has changed - capturing it here keeps both the type
        # checker and the actual value stable for the closure below.
        case = self.case
        self._show_overlay(tr("email_draft.ai_generating_wait", "🤖 KI generiert E-Mail-Entwurf... Bitte warten"))

        def worker():
            user_name = self.profile.user.name if (self.profile and hasattr(self.profile, 'user')) else self.user_name or "Ihr Support-Team"
            base_rules = self.profile.ai_settings.base_rules if (self.profile and hasattr(self.profile, 'ai_settings') and self.profile.ai_settings) else []
            practice_rules = getattr(case.customer, "custom_ai_rules", []) or []
            custom_instruction = self.custom_instruction_entry.get().strip() if (hasattr(self, "custom_instruction_entry") and self.custom_instruction_entry) else ""
            return self.ai_service.generate_customer_response(
                case,
                user_name=user_name,
                base_rules=base_rules,
                practice_rules=practice_rules,
                custom_instruction=custom_instruction,
            )

        def on_done():
            if not self.winfo_exists():
                return
            self._hide_overlay()
            from services.i18n_service import tr
            if isinstance(result_holder[0], Exception):
                self.status_lbl.configure(text=tr("email_draft.ai_generation_failed", "⚠ KI-Generierung fehlgeschlagen: {error}", error=result_holder[0]), text_color=COLOR_DANGER)
            else:
                draft_text = result_holder[0]
                self.body_textbox.delete("1.0", "end")
                self.body_textbox.insert("1.0", draft_text)
                self.status_lbl.configure(text=tr("email_draft.ai_draft_generated", "✓ KI-Entwurf generiert ({model}).", model=self.ai_service.active_model_name), text_color=COLOR_WIKI_LINK)

        result_holder: list[Any] = [None]

        def thread_target():
            try:
                result_holder[0] = worker()
            except Exception as e:
                result_holder[0] = e
            try:
                self.after(0, on_done)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    def _open_ai_assistant_dialog(self):
        """Opens the full AI Assistant dialog for advanced features (summaries, solutions)."""
        if not self.case:
            return
        from ui.dialogs.ai_assistant_dialog import AiAssistantDialog

        wiki_articles: list[dict] = []
        if self.storage_service:
            try:
                from services.wiki_sync_service import WikiSyncService
                wiki_svc = WikiSyncService(self.storage_service.config)
                wiki_articles = wiki_svc.get_all_pages()
            except Exception:
                pass

        AiAssistantDialog(
            self,
            case=self.case,
            profile=self.profile,
            on_case_updated=self.on_case_updated,
            wiki_articles=wiki_articles,
        )

    def destroy(self):
        self._destroyed = True
        super().destroy()

