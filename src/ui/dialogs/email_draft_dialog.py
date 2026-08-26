import os
import threading
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any, Callable
import customtkinter as ctk
from models.case import Case
from models.customer import Customer
from services.ai_service import AiService
from services.calendar_email_service import CalendarEmailService, format_german_salutation
from utils.ui_utils import center_window, enable_auto_hiding_scrollbar
from constants import (
    DIALOG_DIMENSIONS,
    DIALOG_TITLES,
    DEFAULT_OLLAMA_URL,
    DEFAULT_OLLAMA_MODEL,
)


class EmailDraftDialog(ctk.CTkToplevel):
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
        ollama_url = profile.ai_settings.ollama_url if (profile and hasattr(profile, 'ai_settings')) else DEFAULT_OLLAMA_URL
        model_name = profile.ai_settings.model_name if (profile and hasattr(profile, 'ai_settings')) else DEFAULT_OLLAMA_MODEL
        self.ai_service = AiService(ollama_url=ollama_url, model_name=model_name)
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
            if hasattr(c, "contacts") and c.contacts:
                for contact in c.contacts:
                    c_name = getattr(contact, "name", "")
                    c_email = getattr(contact, "email", "")
                    if c_email or c_name:
                        self.all_contacts.append({
                            "email": c_email,
                            "name": c_name,
                            "practice": p_name,
                            "cust_id": c_id,
                            "search_key": f"{c_name} {c_email} {p_name} {c_id}".lower(),
                        })
            elif hasattr(c, "email") and c.email:
                self.all_contacts.append({
                    "email": c.email,
                    "name": "",
                    "practice": p_name,
                    "cust_id": c_id,
                    "search_key": f"{p_name} {c.email} {c_id}".lower(),
                })

        dialog_title = f"{DIALOG_TITLES['email_draft']} - Fall {case.case_id}" if case else f"{DIALOG_TITLES['email_draft']} (Neuer Entwurf)"
        self.title(dialog_title)
        w, h = DIALOG_DIMENSIONS["email_draft"]
        self.geometry(f"{w}x{h}")
        self.minsize(700, 520)

        center_window(self, w, h)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        sig = self.profile.user.email_signature if (self.profile and hasattr(self.profile, "user") and hasattr(self.profile.user, "email_signature")) else ""
        self.draft_data = self.service.generate_email_draft(self.case, user_name=self.user_name, customers=self.customers, signature=sig)
        self.create_widgets()
        self._create_loading_overlay()
        self._update_ollama_status_async()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 8))

        hdr_top_row = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        hdr_top_row.pack(fill="x")

        if self.case:
            title_text = f"✉ E-Mail verfassen (Fall {self.case.case_id})"
            practice_name = self.case.customer.practice_name if self.case.customer else "Unbekannte Praxis"
            deadline_str = self.case.formatted_deadline or "Keine Deadline gesetzt"
            sub_text = f"Praxis: {practice_name} | Rückruf-Deadline: {deadline_str}"
        else:
            title_text = "✉ E-Mail verfassen (Freier Entwurf)"
            sub_text = "Freier Entwurf | Empfänger aus Praxiskartei wählen oder frei eingeben"

        ctk.CTkLabel(
            hdr_top_row,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        # Ollama Status Badge
        self.ollama_status_badge = ctk.CTkLabel(
            hdr_top_row,
            text="Prüfe KI-Status...",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray",
        )
        self.ollama_status_badge.pack(side="right")

        ctk.CTkLabel(
            hdr_frame,
            text=sub_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w")

        # Scrollable Content Box
        content_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        content_scroll.pack(fill="both", expand=True, pady=(0, 8))
        self.content_scroll = content_scroll
        enable_auto_hiding_scrollbar(content_scroll)

        # Recipient Email Header & Row
        ctk.CTkLabel(
            content_scroll,
            text="Empfänger (E-Mail):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(2, 1))

        self.to_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        self.to_row.pack(fill="x", pady=(0, 4))

        self.to_entry = ctk.CTkEntry(
            self.to_row,
            placeholder_text="praxis@beispiel.de oder Name / Praxis eingeben..."
        )
        if self.draft_data.get("to"):
            self.to_entry.insert(0, self.draft_data["to"])
        self.to_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.to_entry.bind("<KeyRelease>", self._on_to_keyrelease)
        self.to_entry.bind("<Escape>", lambda e: self.hide_suggestions())

        self.praxis_btn = ctk.CTkButton(
            self.to_row,
            text="📇 Praxiskartei ▾",
            width=135,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.toggle_praxiskartei_dropdown,
        )
        self.praxis_btn.pack(side="right")

        # Expandable Live Autocomplete / Suggestions Card
        self.suggestions_frame = ctk.CTkFrame(
            content_scroll,
            fg_color=("gray88", "gray22"),
            corner_radius=8,
            border_width=1,
            border_color=("gray75", "gray35"),
        )
        # Suggestions frame starts hidden
        self.suggestions_frame_visible = False

        sug_hdr = ctk.CTkFrame(self.suggestions_frame, fg_color="transparent")
        sug_hdr.pack(fill="x", padx=8, pady=(6, 2))

        self.suggestions_title = ctk.CTkLabel(
            sug_hdr,
            text="🔍 Kontakte aus Praxiskartei (Klicken zum Übernehmen):",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        )
        self.suggestions_title.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            sug_hdr,
            text="✕ Schließen",
            width=70,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color=("gray75", "gray35"),
            hover_color=("gray65", "gray45"),
            command=self.hide_suggestions,
        ).pack(side="right")

        self.suggestions_scroll = ctk.CTkScrollableFrame(
            self.suggestions_frame,
            height=130,
            fg_color="transparent"
        )
        self.suggestions_scroll.pack(fill="both", expand=True, padx=4, pady=(2, 6))
        enable_auto_hiding_scrollbar(self.suggestions_scroll)

        # Subject
        ctk.CTkLabel(content_scroll, text="Betreff:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(4, 1))
        self.subject_entry = ctk.CTkEntry(content_scroll, placeholder_text="Betreff eingeben...")
        if self.draft_data.get("subject"):
            self.subject_entry.insert(0, self.draft_data["subject"])
        self.subject_entry.pack(fill="x", pady=(0, 6))

        # Body Textbox Control Row
        body_hdr_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        body_hdr_row.pack(fill="x", pady=(4, 1))

        ctk.CTkLabel(body_hdr_row, text="E-Mail Nachrichtentext:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        if self.snippet_service:
            ctk.CTkButton(
                body_hdr_row,
                text="🧩 Textbaustein",
                width=110,
                height=26,
                fg_color="gray30",
                hover_color="darkmagenta",
                command=self.open_snippet_picker,
            ).pack(side="right")

        # KI Buttons Row
        ki_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        ki_row.pack(fill="x", pady=(2, 4))

        self.ki_generate_btn = ctk.CTkButton(
            ki_row,
            text="🤖 KI-Entwurf generieren",
            width=180,
            height=28,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self._on_generate_ai_draft,
        )
        self.ki_generate_btn.pack(side="left", padx=(0, 6))

        if self.case:
            ctk.CTkButton(
                ki_row,
                text="🤖 KI-Assistent öffnen",
                width=160,
                height=28,
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=self._open_ai_assistant_dialog,
            ).pack(side="left")

        self.body_textbox = ctk.CTkTextbox(content_scroll, height=210)
        if self.draft_data.get("body"):
            self.body_textbox.insert("1.0", self.draft_data["body"])
        self.body_textbox.pack(fill="x", expand=True, pady=(0, 6))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color="dodgerblue")
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        # Action Buttons
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_box,
            text="✉ In Standard-Mail-App öffnen",
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.on_open_mailto,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="📬 In Outlook übertragen",
            fg_color="royalblue",
            hover_color="blue",
            command=self.on_transfer_to_outlook,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="📋 In Zwischenablage kopieren",
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.on_copy_text,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="Schließen",
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
            width=90,
            height=32,
        ).pack(side="right")

    # --- Autocomplete & Praxiskartei Logic ---

    def _on_to_keyrelease(self, event=None):
        if event and event.keysym == "Escape":
            self.hide_suggestions()
            return

        query = self.to_entry.get().strip().lower()
        if not query:
            self.hide_suggestions()
            return

        matches = [c for c in self.all_contacts if query in c["search_key"]]
        if matches:
            self.show_suggestions(matches, query_hint=f"Treffer für '{query}':")
        else:
            self.hide_suggestions()

    def toggle_praxiskartei_dropdown(self):
        if self.suggestions_frame_visible:
            self.hide_suggestions()
        else:
            self.show_suggestions(self.all_contacts, query_hint="Alle Kontakte aus der Praxiskartei:")

    def show_suggestions(self, contacts: list[dict[str, str]], query_hint: str = ""):
        for w in self.suggestions_scroll.winfo_children():
            w.destroy()

        if query_hint:
            self.suggestions_title.configure(text=f"🔍 {query_hint} ({len(contacts)})")

        if not contacts:
            ctk.CTkLabel(
                self.suggestions_scroll,
                text="Keine passenden Praxiskontakte gefunden.",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=10)
        else:
            for item in contacts[:20]:
                card = ctk.CTkFrame(self.suggestions_scroll, fg_color=("gray80", "gray28"), corner_radius=6, cursor="hand2")
                card.pack(fill="x", pady=2, padx=2)

                contact_name = item.get("name", "")
                email = item.get("email", "")
                practice = item.get("practice", "")
                cust_id = item.get("cust_id", "")

                contact_disp = f"👤 {contact_name}" if contact_name else "🏥 Praxis"
                email_disp = f"<{email}>" if email else "(keine E-Mail)"
                top_text = f"{contact_disp} {email_disp}"
                sub_text = f"Praxis: {practice} ({cust_id})"

                top_lbl = ctk.CTkLabel(
                    card,
                    text=top_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    anchor="w"
                )
                top_lbl.pack(fill="x", padx=8, pady=(4, 0))

                sub_lbl = ctk.CTkLabel(
                    card,
                    text=sub_text,
                    font=ctk.CTkFont(size=10),
                    text_color=("gray40", "gray70"),
                    anchor="w"
                )
                sub_lbl.pack(fill="x", padx=8, pady=(0, 4))

                # Click binding
                for elem in (card, top_lbl, sub_lbl):
                    elem.bind("<Button-1>", lambda e, it=item: self.select_contact(it))

        if not self.suggestions_frame_visible:
            self.suggestions_frame.pack(fill="x", pady=(0, 8), after=self.to_row)
            self.suggestions_frame_visible = True

    def hide_suggestions(self):
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
        display_name = name or practice
        self.status_lbl.configure(text=f"✓ Empfänger gesetzt: {display_name} <{email}>")

    def update_salutation_in_body(self, contact_name: str, practice_name: str):
        new_salutation = format_german_salutation(contact_name, practice_name)
        curr_body = self.body_textbox.get("1.0", "end-1c")

        if not curr_body.strip():
            self.body_textbox.insert("1.0", f"{new_salutation}\n\n\n\nMit freundlichen Grüßen\n{self.user_name or 'Ihr Support-Team'}")
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
        self.body_textbox.insert("insert", text)
        self.status_lbl.configure(text="✓ Textbaustein eingefügt.")

    def on_open_mailto(self):
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
            self.status_lbl.configure(text="✓ Standard-Mail-Programm aufgerufen.")
        except Exception as e:
            self.status_lbl.configure(text=f"Fehler beim Öffnen: {e}")

    def on_transfer_to_outlook(self):
        """Transfers the drafted email directly into Microsoft Outlook."""
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
            self.status_lbl.configure(text="✓ E-Mail erfolgreich in Outlook geöffnet.")
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
                self.status_lbl.configure(text="✓ E-Mail-Entwurf an E-Mail-Client übergeben (.eml).")
            except Exception as e:
                self.status_lbl.configure(text=f"Fehler bei Outlook-Übergabe: {e}")

    def on_copy_text(self):
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        formatted = f"An: {to}\nBetreff: {subject}\n\n{body}"
        try:
            self.clipboard_clear()
            self.clipboard_append(formatted)
            self.status_lbl.configure(text="✓ E-Mail in Zwischenablage kopiert.")
        except Exception as e:
            self.status_lbl.configure(text=f"Kopieren fehlgeschlagen: {e}")

    # --- AI / KI Integration ---

    def _create_loading_overlay(self):
        """Creates a semi-transparent loading overlay for AI generation."""
        self._overlay_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))

        card = ctk.CTkFrame(self._overlay_frame, fg_color=("gray85", "gray25"), corner_radius=12, width=380, height=120)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self._overlay_msg_lbl = ctk.CTkLabel(
            card,
            text="🤖 KI generiert E-Mail-Entwurf...",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._overlay_msg_lbl.pack(pady=(20, 10))

        self._overlay_progress = ctk.CTkProgressBar(card, width=280, mode="indeterminate", progress_color="#6366f1")
        self._overlay_progress.pack(pady=(0, 10))

        ctk.CTkLabel(
            card,
            text="Bitte einen Moment gedulden — Modell generiert Antwort",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(pady=(0, 15))

    def _show_overlay(self, message: str = "🤖 KI generiert E-Mail-Entwurf..."):
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
        """Checks Ollama status in a background thread and updates the status badge."""
        def thread_target():
            try:
                is_online, models = self.ai_service.check_ollama_status()
            except Exception:
                is_online, models = False, []

            def ui_callback():
                if not self.winfo_exists():
                    return
                if is_online:
                    self.ollama_status_badge.configure(
                        text=f"🟢 Ollama aktiv ({self.ai_service.model_name})",
                        text_color="forestgreen",
                    )
                else:
                    self.ollama_status_badge.configure(
                        text="⚡ Regelbasierter Modus (Ollama offline)",
                        text_color="dodgerblue",
                    )

            try:
                self.after(0, ui_callback)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    def _on_generate_ai_draft(self):
        """Generates an AI-powered email draft and fills the body textbox."""
        if not self.case:
            self.status_lbl.configure(text="⚠ KI-Entwurf benötigt einen aktiven Fall.", text_color="darkorange")
            return

        self._show_overlay("🤖 KI generiert E-Mail-Entwurf... Bitte warten")

        def worker():
            user_name = self.profile.user.name if (self.profile and hasattr(self.profile, 'user')) else self.user_name or "Ihr Support-Team"
            base_rules = self.profile.ai_settings.base_rules if (self.profile and hasattr(self.profile, 'ai_settings') and self.profile.ai_settings) else []
            practice_rules = getattr(self.case.customer, "custom_ai_rules", []) or []
            return self.ai_service.generate_customer_response(
                self.case,
                user_name=user_name,
                base_rules=base_rules,
                practice_rules=practice_rules,
            )

        def on_done():
            if not self.winfo_exists():
                return
            self._hide_overlay()
            if isinstance(result_holder[0], Exception):
                self.status_lbl.configure(text=f"⚠ KI-Generierung fehlgeschlagen: {result_holder[0]}", text_color="red")
            else:
                draft_text = result_holder[0]
                self.body_textbox.delete("1.0", "end")
                self.body_textbox.insert("1.0", draft_text)
                self.status_lbl.configure(text=f"✓ KI-Entwurf generiert ({self.ai_service.model_name}).", text_color="dodgerblue")

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
