import threading
import customtkinter as ctk
from typing import Callable, Any
from models.case import Case, TimelineEntry
from models.profile import UserProfile
from services.ai_service import AiService
from utils.datetime_utils import now_iso
from utils.ui_utils import center_window, enable_auto_hiding_scrollbar


class AiAssistantDialog(ctk.CTkToplevel):
    """Dialog providing AI & NLP Support capabilities (Case Summaries, Solution Cards, and Email Reply Drafting)."""

    def __init__(
        self,
        parent,
        case: Case,
        profile: UserProfile | None = None,
        on_case_updated: Callable[[Case], None] | None = None,
        on_open_email_draft: Callable[[Case], None] | None = None,
        wiki_articles: list[dict] | None = None,
    ):
        super().__init__(parent)
        self.case = case
        self.profile = profile
        self.on_case_updated = on_case_updated
        self.on_open_email_draft = on_open_email_draft
        self.wiki_articles = wiki_articles or []
        self._is_loading = False

        ollama_url = profile.ai_settings.ollama_url if profile else "http://localhost:11434"
        model_name = profile.ai_settings.model_name if profile else "llama3"
        self.ai_service = AiService(ollama_url=ollama_url, model_name=model_name)

        self.title(f"🤖 KI- & Support-Assistent — Fall [{case.case_id}]")
        w, h = 820, 580
        self.geometry(f"{w}x{h}")
        self.minsize(720, 480)
        center_window(self, w, h)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        self.create_widgets()
        self.create_loading_overlay()
        self.update_status_header_async()
        self.generate_summary()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # Status & Header Bar
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            hdr_frame,
            text=f"🤖 KI-Assistent für Fall [{self.case.case_id}]",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            hdr_frame,
            text="Prüfe Status...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray",
        )
        self.status_badge.pack(side="right")

        # Tabview for Features
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, 8))

        self.tab_summary = self.tabview.add("📋 Zusammenfassung")
        self.tab_solutions = self.tabview.add("💡 Lösungsvorschläge")
        self.tab_response = self.tabview.add("✉ Antwort-Entwurf")

        self.setup_summary_tab()
        self.setup_solutions_tab()
        self.setup_response_tab()

        # Footer Close Button
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x", pady=(4, 0))

        self.status_lbl = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=11), text_color="dodgerblue")
        self.status_lbl.pack(side="left")

        ctk.CTkButton(
            footer,
            text="Schließen",
            width=100,
            height=30,
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
        ).pack(side="right")

    def create_loading_overlay(self):
        """Creates a smooth, semi-transparent loading spinner overlay frame."""
        self.overlay_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))

        card = ctk.CTkFrame(self.overlay_frame, fg_color=("gray85", "gray25"), corner_radius=12, width=380, height=140)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self.overlay_msg_lbl = ctk.CTkLabel(
            card,
            text="🤖 KI verarbeitet Anfrage...",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.overlay_msg_lbl.pack(pady=(20, 10))

        self.overlay_progress = ctk.CTkProgressBar(card, width=280, mode="indeterminate", progress_color="dodgerblue")
        self.overlay_progress.pack(pady=(0, 10))

        ctk.CTkLabel(
            card,
            text="Bitte einen Moment gedulden — Modell generiert Antwort",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        ).pack(pady=(0, 15))

    def _show_overlay(self, message: str = "🤖 KI verarbeitet Anfrage..."):
        self.overlay_msg_lbl.configure(text=message)
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay_progress.start()
        self.update_idletasks()

    def _hide_overlay(self):
        try:
            self.overlay_progress.stop()
            self.overlay_frame.place_forget()
        except Exception:
            pass

    def _run_async(self, worker_fn: Callable[[], Any], on_success: Callable[[Any], None], loading_msg: str):
        """Executes worker_fn in a background daemon thread while displaying the loading overlay UI."""
        self._show_overlay(loading_msg)

        def thread_target():
            res = None
            try:
                res = worker_fn()
            except Exception as e:
                res = e

            def ui_callback():
                if not self.winfo_exists():
                    return
                self._hide_overlay()
                if not isinstance(res, Exception):
                    on_success(res)
                else:
                    self.status_lbl.configure(text=f"⚠ Fehler bei KI-Generierung: {res}", text_color="red")

            try:
                self.after(0, ui_callback)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    def update_status_header_async(self):
        def thread_target():
            try:
                is_online, models = self.ai_service.check_ollama_status()
            except Exception:
                is_online, models = False, []

            def ui_callback():
                if not self.winfo_exists():
                    return
                if is_online:
                    m_str = f" ({self.ai_service.model_name})" if self.ai_service.model_name in models else ""
                    self.status_badge.configure(
                        text=f"🟢 Ollama Local LLM aktiv{m_str}",
                        text_color="forestgreen",
                    )
                else:
                    self.status_badge.configure(
                        text="⚡ Regelbasierter NLP-Modus (Ollama offline)",
                        text_color="dodgerblue",
                    )

            try:
                self.after(0, ui_callback)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    # --- TAB 1: SUMMARY ---
    def setup_summary_tab(self):
        btn_bar = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(4, 6))

        ctk.CTkButton(
            btn_bar,
            text="🔄 Zusammenfassung neu generieren",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.generate_summary,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar,
            text="📋 In Zwischenablage kopieren",
            width=190,
            height=28,
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.copy_summary,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_bar,
            text="📌 In Fall-Zeitleiste einfügen",
            width=190,
            height=28,
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.append_summary_to_timeline,
        ).pack(side="left")

        self.summary_textbox = ctk.CTkTextbox(self.tab_summary)
        self.summary_textbox.pack(fill="both", expand=True, pady=(4, 0))

    def generate_summary(self):
        def worker():
            return self.ai_service.summarize_case(self.case)

        def on_success(summary_text: str):
            self.summary_textbox.delete("1.0", "end")
            self.summary_textbox.insert("1.0", summary_text)
            self.status_lbl.configure(text="✓ Zusammenfassung erfolgreich generiert.", text_color="dodgerblue")

        self._run_async(worker, on_success, "🤖 KI generiert Zusammenfassung... Bitte warten")

    def copy_summary(self):
        txt = self.summary_textbox.get("1.0", "end-1c").strip()
        if txt:
            self.clipboard_clear()
            self.clipboard_append(txt)
            self.status_lbl.configure(text="✓ Zusammenfassung in Zwischenablage kopiert.", text_color="dodgerblue")

    def append_summary_to_timeline(self):
        txt = self.summary_textbox.get("1.0", "end-1c").strip()
        if txt and self.on_case_updated:
            author_name = self.profile.user.name if self.profile else "KI-Assistent"
            entry = TimelineEntry(
                timestamp=now_iso(),
                author=author_name,
                channel="INTERNAL_NOTE",
                note=f"🤖 KI-Zusammefassung:\n\n{txt}",
            )
            self.case.timeline.append(entry)
            self.on_case_updated(self.case)
            self.status_lbl.configure(text="✓ KI-Zusammenfassung als Zeitleisten-Eintrag gespeichert.", text_color="dodgerblue")

    # --- TAB 2: SOLUTIONS ---
    def setup_solutions_tab(self):
        hdr_bar = ctk.CTkFrame(self.tab_solutions, fg_color="transparent")
        hdr_bar.pack(fill="x", pady=(4, 6))

        ctk.CTkLabel(
            hdr_bar,
            text="💡 Automatisch ermittelte Lösungsschritte & Wiki-Referenzen:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            hdr_bar,
            text="🔄 Lösungssuche erneut ausführen",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.load_solutions,
        ).pack(side="right")

        self.solutions_scroll = ctk.CTkScrollableFrame(self.tab_solutions, fg_color="transparent")
        self.solutions_scroll.pack(fill="both", expand=True, pady=(4, 0))
        enable_auto_hiding_scrollbar(self.solutions_scroll)

    def load_solutions(self):
        def worker():
            return self.ai_service.suggest_solutions(self.case, self.wiki_articles)

        def on_success(solutions: list[dict]):
            for w in self.solutions_scroll.winfo_children():
                w.destroy()

            for sol in solutions:
                card = ctk.CTkFrame(self.solutions_scroll, fg_color=("gray85", "gray22"), corner_radius=8)
                card.pack(fill="x", pady=4, padx=2)

                top_r = ctk.CTkFrame(card, fg_color="transparent")
                top_r.pack(fill="x", padx=10, pady=(6, 2))

                ctk.CTkLabel(
                    top_r,
                    text=sol.get("title", "Lösung"),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w",
                ).pack(side="left")

                ctk.CTkLabel(
                    top_r,
                    text=f"Relevanz: {sol.get('confidence', '80%')} ({sol.get('source', '')})",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="dodgerblue",
                ).pack(side="right")

                ctk.CTkLabel(
                    card,
                    text=sol.get("snippet", ""),
                    font=ctk.CTkFont(size=11),
                    text_color=("gray30", "gray80"),
                    anchor="w",
                    justify="left",
                ).pack(fill="x", padx=10, pady=(2, 6))

        self._run_async(worker, on_success, "💡 Analyse von Wiki & Fehlercodes... Bitte warten")

    # --- TAB 3: RESPONSE DRAFT ---
    def setup_response_tab(self):
        hdr_bar = ctk.CTkFrame(self.tab_response, fg_color="transparent")
        hdr_bar.pack(fill="x", pady=(4, 6))

        ctk.CTkButton(
            hdr_bar,
            text="🔄 Antwort-Entwurf generieren",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.generate_draft,
        ).pack(side="left", padx=(0, 8))

        if self.on_open_email_draft:
            ctk.CTkButton(
                hdr_bar,
                text="✉ In E-Mail-Entwurf öffnen",
                width=190,
                height=28,
                fg_color="royalblue",
                hover_color="blue",
                command=self.open_in_email_draft,
            ).pack(side="left")

        self.draft_textbox = ctk.CTkTextbox(self.tab_response)
        self.draft_textbox.pack(fill="both", expand=True, pady=(4, 0))

    def generate_draft(self):
        def worker():
            user_name = self.profile.user.name if self.profile else "Ihr Support-Team"
            return self.ai_service.generate_customer_response(self.case, user_name=user_name)

        def on_success(draft_text: str):
            self.draft_textbox.delete("1.0", "end")
            self.draft_textbox.insert("1.0", draft_text)
            self.status_lbl.configure(text="✓ E-Mail-Antwort-Entwurf generiert.", text_color="dodgerblue")

        self._run_async(worker, on_success, "✉ KI generiert E-Mail-Antwort... Bitte warten")

    def open_in_email_draft(self):
        if self.on_open_email_draft:
            self.destroy()
            self.on_open_email_draft(self.case)
