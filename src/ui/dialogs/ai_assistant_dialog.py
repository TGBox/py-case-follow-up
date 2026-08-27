import threading
import customtkinter as ctk
from typing import Callable, Any
from models.case import Case, TimelineEntry
from models.profile import UserProfile
from services.ai_service import AiService
from utils.datetime_utils import now_iso
from utils.ui_utils import center_window, enable_auto_hiding_scrollbar


from constants import (
    DIALOG_TITLES,
    DIALOG_DIMENSIONS,
    UI_BUTTON_TEXTS,
    STATUS_MESSAGES,
    DEFAULT_OLLAMA_URL,
    DEFAULT_OLLAMA_MODEL,
    AI_BADGE_ACTIVE,
    AI_BADGE_STANDBY,
    AI_BADGE_DISABLED,
    AI_BADGE_NLP_FALLBACK,
    AI_STATUS_UNLOADING,
    AI_STATUS_UNLOADED,
    AI_STATUS_ACTIVATED,
    AI_BTN_GLOBAL_TOGGLE_HEADER,
    AI_LABEL_CUSTOM_INSTRUCTION,
    AI_HINT_CUSTOM_INSTRUCTION,
    AI_STATUS_DISABLED_HINT,
    COLOR_BADGE_GREEN,
    COLOR_BADGE_BLUE,
    COLOR_BADGE_GRAY,
    COLOR_TEXT_BLUE,
    COLOR_TEXT_ORANGE,
    COLOR_TEXT_GRAY,
    COLOR_TEXT_GREEN,
    COLOR_TEXT_RED,
    COLOR_MUTED_GRAY,
    COLOR_MUTED_HOVER,
)


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

        self.title(f"{DIALOG_TITLES['ai_assistant']} — Fall [{case.case_id}]")
        w, h = DIALOG_DIMENSIONS["ai_assistant"]
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

        # Global AI Toggle Switch
        self.ai_toggle_switch = ctk.CTkSwitch(
            hdr_frame,
            text=AI_BTN_GLOBAL_TOGGLE_HEADER,
            command=self.on_toggle_global_ai,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        if self.profile and self.profile.ai_settings.enable_ai:
            self.ai_toggle_switch.select()
        else:
            self.ai_toggle_switch.deselect()
        self.ai_toggle_switch.pack(side="right", padx=(0, 10))

        self.status_badge = ctk.CTkLabel(
            hdr_frame,
            text="Prüfe Status...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_GRAY,
        )
        self.status_badge.pack(side="right", padx=(0, 10))

        # Priority Custom Instruction Bar
        ci_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"), corner_radius=6)
        ci_frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            ci_frame,
            text=AI_LABEL_CUSTOM_INSTRUCTION,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_BLUE,
        ).pack(side="left", padx=(10, 4), pady=4)

        self.custom_instruction_entry = ctk.CTkEntry(
            ci_frame,
            placeholder_text=AI_HINT_CUSTOM_INSTRUCTION,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self.custom_instruction_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)

        # Tabview for Features
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, 8))

        self.tab_summary = self.tabview.add("📋 Zusammenfassung")
        self.tab_solutions = self.tabview.add("💡 Lösungsvorschläge")
        self.tab_response = self.tabview.add("✉ Antwort-Entwurf")

        self.setup_summary_tab()
        self.setup_solutions_tab()
        self.setup_response_tab()

        self.update_ai_buttons_state()

        # Footer Close Button
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x", pady=(4, 0))

        self.status_lbl = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_BLUE)
        self.status_lbl.pack(side="left")

        ctk.CTkButton(
            footer,
            text="Schließen",
            width=100,
            height=30,
            fg_color=COLOR_MUTED_GRAY,
            hover_color=COLOR_MUTED_HOVER,
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
                running_models = self.ai_service.get_running_models() if is_online else []
            except Exception:
                is_online, models, running_models = False, [], []

            def ui_callback():
                if not self.winfo_exists():
                    return

                ai_enabled = self.profile.ai_settings.enable_ai if (self.profile and hasattr(self.profile, "ai_settings")) else True

                if not ai_enabled:
                    self.status_badge.configure(
                        text=AI_BADGE_DISABLED,
                        text_color=COLOR_BADGE_GRAY,
                    )
                elif is_online and running_models:
                    self.status_badge.configure(
                        text=AI_BADGE_ACTIVE.format(model=self.ai_service.model_name),
                        text_color=COLOR_BADGE_GREEN,
                    )
                elif is_online:
                    self.status_badge.configure(
                        text=AI_BADGE_STANDBY.format(model=self.ai_service.model_name),
                        text_color=COLOR_BADGE_BLUE,
                    )
                else:
                    self.status_badge.configure(
                        text=AI_BADGE_NLP_FALLBACK,
                        text_color=COLOR_BADGE_BLUE,
                    )

            try:
                self.after(0, ui_callback)
            except Exception:
                pass

        threading.Thread(target=thread_target, daemon=True).start()

    def on_toggle_global_ai(self):
        enabled = bool(self.ai_toggle_switch.get())
        if self.profile and hasattr(self.profile, "ai_settings"):
            self.profile.ai_settings.enable_ai = enabled

        if not enabled:
            self.status_lbl.configure(text=AI_STATUS_UNLOADING, text_color="orange")
            def worker():
                try:
                    self.ai_service.unload_model()
                except Exception:
                    pass

                def done():
                    if not self.winfo_exists():
                        return
                    self.status_lbl.configure(text=AI_STATUS_UNLOADED, text_color="gray")
                    self.update_ai_buttons_state()
                    self.update_status_header_async()
                    from ui.widgets.toast_notification import ToastNotification
                    ToastNotification(self, "KI-Status", "KI global deaktiviert & Modelle entladen")

                self.after(0, done)

            import threading
            threading.Thread(target=worker, daemon=True).start()
        else:
            self.status_lbl.configure(text=AI_STATUS_ACTIVATED, text_color="green")
            self.update_ai_buttons_state()
            self.update_status_header_async()
            from ui.widgets.toast_notification import ToastNotification
            ToastNotification(self, "KI-Status", "KI global aktiviert")

    def update_ai_buttons_state(self):
        is_enabled = self.profile.ai_settings.enable_ai if (self.profile and hasattr(self.profile, "ai_settings")) else True

        state = "normal" if is_enabled else "disabled"
        if hasattr(self, "btn_gen_summary") and self.btn_gen_summary:
            self.btn_gen_summary.configure(state=state)
        if hasattr(self, "btn_gen_solutions") and self.btn_gen_solutions:
            self.btn_gen_solutions.configure(state=state)
        if hasattr(self, "btn_gen_draft") and self.btn_gen_draft:
            self.btn_gen_draft.configure(state=state)

        if not is_enabled:
            self.status_lbl.configure(text="⚠ KI global deaktiviert (Schalter oben rechts auf OFF). Buttons deaktiviert.", text_color="orange")

    # --- TAB 1: SUMMARY ---
    def setup_summary_tab(self):
        btn_bar = ctk.CTkFrame(self.tab_summary, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(4, 6))

        self.btn_gen_summary = ctk.CTkButton(
            btn_bar,
            text="🔄 Zusammenfassung neu generieren",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.generate_summary,
        )
        self.btn_gen_summary.pack(side="left", padx=(0, 8))

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

    def get_custom_instruction(self) -> str:
        if hasattr(self, "custom_instruction_entry") and self.custom_instruction_entry:
            return self.custom_instruction_entry.get().strip()
        return ""

    def get_active_rules(self) -> tuple[list[str], list[str]]:
        base_rules = self.profile.ai_settings.base_rules if (self.profile and self.profile.ai_settings) else []
        practice_rules = getattr(self.case.customer, "custom_ai_rules", []) or []
        return base_rules, practice_rules

    def generate_summary(self):
        def worker():
            base_rules, practice_rules = self.get_active_rules()
            custom_instruction = self.get_custom_instruction()
            return self.ai_service.summarize_case(
                self.case,
                base_rules=base_rules,
                practice_rules=practice_rules,
                custom_instruction=custom_instruction,
            )

        def on_success(summary_text: str):
            self.summary_textbox.delete("1.0", "end")
            self.summary_textbox.insert("1.0", summary_text)
            b_cnt, p_cnt = len(self.get_active_rules()[0]), len(self.get_active_rules()[1])
            has_ci = bool(self.get_custom_instruction())
            ci_info = " + ⚡ Sonderanweisung" if has_ci else ""
            info = f" ({b_cnt} Basis-Regeln, {p_cnt} Praxis-Regeln{ci_info})" if (b_cnt or p_cnt or has_ci) else ""
            self.status_lbl.configure(text=f"✓ Zusammenfassung erfolgreich generiert{info}.", text_color="dodgerblue")

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

        self.btn_gen_solutions = ctk.CTkButton(
            hdr_bar,
            text="🔄 Lösungssuche erneut ausführen",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.load_solutions,
        )
        self.btn_gen_solutions.pack(side="right")

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

        self.btn_gen_draft = ctk.CTkButton(
            hdr_bar,
            text="🔄 Antwort-Entwurf generieren",
            width=210,
            height=28,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.generate_draft,
        )
        self.btn_gen_draft.pack(side="left", padx=(0, 8))

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
            base_rules, practice_rules = self.get_active_rules()
            custom_instruction = self.get_custom_instruction()
            return self.ai_service.generate_customer_response(
                self.case,
                user_name=user_name,
                base_rules=base_rules,
                practice_rules=practice_rules,
                custom_instruction=custom_instruction,
            )

        def on_success(draft_text: str):
            self.draft_textbox.delete("1.0", "end")
            self.draft_textbox.insert("1.0", draft_text)
            b_cnt, p_cnt = len(self.get_active_rules()[0]), len(self.get_active_rules()[1])
            has_ci = bool(self.get_custom_instruction())
            ci_info = " + ⚡ Sonderanweisung" if has_ci else ""
            info = f" ({b_cnt} Basis-Regeln, {p_cnt} Praxis-Regeln{ci_info})" if (b_cnt or p_cnt or has_ci) else ""
            self.status_lbl.configure(text=f"✓ E-Mail-Antwort-Entwurf generiert{info}.", text_color="dodgerblue")

        self._run_async(worker, on_success, "✉ KI generiert E-Mail-Antwort... Bitte warten")

    def open_in_email_draft(self):
        if self.on_open_email_draft:
            self.destroy()
            self.on_open_email_draft(self.case)
