"""KI-/NLP-Einstellungen (Ollama & Google Gemini) fuer den ProfileSettingsDialog.

Ausgelagert aus profile_settings_dialog.py (Refactoring): dieser eine Tab machte
zuvor knapp 45% der Datei aus. AiSettingsTabMixin wird per Mixin-Vererbung in
ProfileSettingsDialog eingemischt, sodass `self` weiterhin dieselbe Dialog-Instanz
ist und alle hier gesetzten Widget-Attribute (self.ai_*, self.gemini_*, self.ollama_*)
unveraendert von save_settings() & Co. in profile_settings_dialog.py gelesen werden
koennen. Reines Verschieben von Code, keine Verhaltensaenderung.
"""
import customtkinter as ctk
from constants import (
    AI_BTN_CREATE_PVS_MODEL,
    AI_BTN_DOWNLOAD_LLAMA,
    AI_BTN_DOWNLOAD_OLLAMA,
    AI_BTN_DOWNLOAD_QWEN,
    AI_BTN_GLOBAL_TOGGLE,
    AI_BTN_PRELOAD_MODEL,
    AI_BTN_START_SERVER,
    AI_BTN_STOP_SERVER,
    AI_BTN_TEST_GEMINI_KEY,
    AI_BTN_UNLOAD_MODEL,
    AI_LABEL_BASE_RULES_HINT,
    AI_LABEL_BASE_RULES_TITLE,
    AI_LABEL_OLLAMA_URL,
    AI_LABEL_SELECT_MODEL,
    AI_NO_MODELS_DESC,
    AI_NO_MODELS_TITLE,
    AI_OFFLINE_DESC,
    AI_STATUS_ACTIVATED,
    AI_STATUS_CHECKING,
    AI_STATUS_OFFLINE_LABEL,
    AI_STATUS_ONLINE_DISABLED,
    AI_STATUS_ONLINE_LOADED,
    AI_STATUS_ONLINE_STANDBY,
    AI_STATUS_STARTING,
    AI_STATUS_STOPPING,
    AI_STATUS_UNLOADED,
    AI_STATUS_UNLOADING,
    AVAILABLE_GEMINI_MODELS,
    BTN_WIDTH_ACTION,
    BTN_WIDTH_CREATE_PVS,
    BTN_WIDTH_DOWNLOAD_MODEL,
    BTN_WIDTH_DOWNLOAD_OLLAMA,
    BTN_WIDTH_ICON_SM,
    BTN_WIDTH_PRELOAD,
    BTN_WIDTH_SCAN_OLLAMA,
    BTN_WIDTH_START_OLLAMA,
    COLOR_BTN_GRAY,
    COLOR_BTN_GRAY30,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_MUTED_BODY,
    COLOR_MUTED_DISABLED,
    COLOR_MUTED_LABEL,
    COLOR_PANEL_MUTED_BG,
    COLOR_PRIMARY_BLUE,
    COLOR_PURPLE_DARK,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_TEXT_BLUE,
    COLOR_TEXT_GRAY,
    COLOR_TEXT_GREEN,
    COLOR_TEXT_ORANGE,
    COLOR_TEXT_RED,
    COMBO_WIDTH_GEMINI_MODEL,
    COMBO_WIDTH_OLLAMA_MODEL,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_MODELFILE_PATH,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_PVS_MODEL_NAME,
    DELAY_OLLAMA_STATUS_SCAN_MS,
    ENTRY_WIDTH_GEMINI_KEY,
    ENTRY_WIDTH_OLLAMA_MODEL,
    ENTRY_WIDTH_OLLAMA_URL,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_WEIGHT_BOLD,
    ICON_PASSWORD_HIDE,
    ICON_PASSWORD_SHOW,
    ICON_STATUS_ERROR,
    ICON_STATUS_FLASH,
    ICON_STATUS_SUCCESS,
    ICON_STATUS_WARNING,
    MODELFILE_SYSTEM_PREFIX,
    MODELFILE_SYSTEM_RULES_MARKER,
    MODELFILE_SYSTEM_SUFFIX,
    OLLAMA_DOWNLOAD_URL,
    OLLAMA_LIBRARY_LLAMA_URL,
    OLLAMA_LIBRARY_QWEN_URL,
    PAD_10,
    PAD_15,
    PAD_CARD_INSET,
    PAD_CONTAINER,
    PAD_GAP,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    PASSWORD_CHAR_MASK,
    PASSWORD_CHAR_SHOW,
    TEXTBOX_SPACING1_PARAGRAPH,
    TEXTBOX_SPACING2_PARAGRAPH,
    TEXTBOX_SPACING3_PARAGRAPH,
)
from typing import TYPE_CHECKING, Any
from collections.abc import Callable


#: Key/default pairs for the AI provider selector, see POPUP_TARGET_CHOICES.
AI_PROVIDER_CHOICES = [
    ("profile.provider_ollama", "OLLAMA (Lokal)"),
    ("profile.provider_gemini", "GOOGLE GEMINI (Cloud)"),
]
#: Program values in the same order as the labels above. The selector shows
#: translated captions, so its position - not its text - identifies the provider.
AI_PROVIDER_KEYS = ("OLLAMA", "GEMINI")


class AiSettingsTabMixin:
    """Baut den Tab "KI & NLP" auf und enthaelt dessen komplette Event-Logik
    (Ollama-Server-Steuerung, Modell-Management, Gemini-Key-Test, Provider-Wechsel).
    Nur zusammen mit ProfileSettingsDialog (bzw. einer Klasse mit denselben
    self.tab_ai / self.profile / self.storage_service Attributen) nutzbar.
    """

    if TYPE_CHECKING:
        tab_ai: ctk.CTkFrame
        profile: Any
        storage_service: Any
        # Provided by BaseDialog once mixed into ProfileSettingsDialog.
        register_i18n: Callable[..., Any]
        retranslate_choices: Callable[..., Any]
        selected_choice_index: Callable[..., int]
        winfo_exists: Callable[[], bool]
        after: Callable[..., Any]
        update_idletasks: Callable[[], None]



    def setup_ai_tab(self):
        import webbrowser

        from services.i18n_service import tr

        self.register_i18n(ctk.CTkLabel(
            self.tab_ai,
            text=tr("profile.ai_header", "🤖 KI- & NLP-Einstellungen (Ollama Local LLM & Google Gemini API)"),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
        ), "profile.ai_header", "🤖 KI- & NLP-Einstellungen (Ollama Local LLM & Google Gemini API)").pack(anchor="w", pady=(PAD_10, PAD_CONTAINER))

        # --- Provider Selection Row ---
        provider_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        provider_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(ctk.CTkLabel(provider_frame, text=tr("profile.ai_provider_label", "KI-Anbieter wählen:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "profile.ai_provider_label", "KI-Anbieter wählen:").pack(side="left", padx=(PAD_NONE, PAD_10))

        current_provider = getattr(self.profile.ai_settings, "provider", "OLLAMA").upper()
        self.ai_provider_seg = ctk.CTkSegmentedButton(  # type: ignore[attr-defined]
            provider_frame,
            values=[tr(key, default) for key, default in AI_PROVIDER_CHOICES],
            command=self.on_change_ai_provider,
        )
        self.ai_provider_seg.set(tr("profile.provider_gemini", "GOOGLE GEMINI (Cloud)") if current_provider == "GEMINI" else tr("profile.provider_ollama", "OLLAMA (Lokal)"))
        self.ai_provider_seg.pack(side="left", padx=(PAD_NONE, PAD_15))

        self.anonymize_chk_var = ctk.BooleanVar(value=getattr(self.profile.ai_settings, "enable_anonymization", True))
        self.anonymize_chk = self.register_i18n(ctk.CTkCheckBox(
            provider_frame,
            text=tr("profile.anonymize_toggle", "🔒 Lokale PII-Anonymisierung aktivieren (DSGVO / § 203 StGB)"),
            variable=self.anonymize_chk_var,
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
        ), "profile.anonymize_toggle", "🔒 Lokale PII-Anonymisierung aktivieren (DSGVO / § 203 StGB)")
        self.anonymize_chk.pack(side="left")

        # --- Gemini Card (Shown when Gemini selected) ---
        self.gemini_card = ctk.CTkFrame(self.tab_ai, corner_radius=CORNER_RADIUS_CARD)

        gemini_top_row = ctk.CTkFrame(self.gemini_card, fg_color="transparent")
        gemini_top_row.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_10, PAD_CONTAINER))

        self.register_i18n(ctk.CTkLabel(gemini_top_row, text=tr("profile.gemini_key_lbl", "🔑 Google Gemini API Key:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "profile.gemini_key_lbl", "🔑 Google Gemini API Key:").pack(side="left", padx=(PAD_NONE, PAD_MD))
        self.gemini_key_entry = self.register_i18n(ctk.CTkEntry(
            gemini_top_row,
            placeholder_text=tr("profile.gemini_key_placeholder", "AIzaSy..."),
            show=PASSWORD_CHAR_MASK,
            width=ENTRY_WIDTH_GEMINI_KEY,
        ), "profile.gemini_key_placeholder", "AIzaSy...", attr="placeholder_text")
        self.gemini_key_entry.insert(0, getattr(self.profile.ai_settings, "gemini_api_key", ""))
        self.gemini_key_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.btn_toggle_key_show = ctk.CTkButton(
            gemini_top_row,
            text=ICON_PASSWORD_SHOW,
            width=BTN_WIDTH_ICON_SM,
            fg_color=COLOR_BTN_GRAY30,
            command=self.on_toggle_show_gemini_key
        )
        self.btn_toggle_key_show.pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.btn_test_gemini = ctk.CTkButton(
            gemini_top_row,
            text=AI_BTN_TEST_GEMINI_KEY,
            command=self.on_test_gemini_key,
            fg_color=COLOR_PRIMARY_BLUE,
            width=BTN_WIDTH_ACTION,
        )
        self.btn_test_gemini.pack(side="left")

        gemini_model_row = ctk.CTkFrame(self.gemini_card, fg_color="transparent")
        gemini_model_row.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_NONE, PAD_10))

        self.register_i18n(ctk.CTkLabel(gemini_model_row, text=tr("profile.gemini_select_model", "Gemini Modell wählen:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)), "profile.gemini_select_model", "Gemini Modell wählen:").pack(side="left", padx=(PAD_NONE, PAD_MD))
        self.gemini_model_combo = ctk.CTkOptionMenu(
            gemini_model_row,
            values=AVAILABLE_GEMINI_MODELS,
            width=COMBO_WIDTH_GEMINI_MODEL,
        )
        saved_g_model = getattr(self.profile.ai_settings, "gemini_model", DEFAULT_GEMINI_MODEL)
        self.gemini_model_combo.set(saved_g_model if saved_g_model in AVAILABLE_GEMINI_MODELS else DEFAULT_GEMINI_MODEL)
        self.gemini_model_combo.pack(side="left", padx=(PAD_NONE, PAD_15))

        self.gemini_status_lbl = ctk.CTkLabel(
            gemini_model_row,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
        )
        self.gemini_status_lbl.pack(side="left")

        gemini_rules_row = ctk.CTkFrame(self.gemini_card, fg_color="transparent")
        gemini_rules_row.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_NONE, PAD_10))

        import tkinter as tk
        self.gemini_modelfile_chk_var = tk.BooleanVar(value=getattr(self.profile.ai_settings, "use_modelfile_rules_for_gemini", False))
        self.gemini_modelfile_chk = self.register_i18n(ctk.CTkCheckBox(
            gemini_rules_row,
            text=tr("profile.gemini_modelfile_rules", "📄 Modelfile-Systemregeln für Gemini in Basis-Regeln übernehmen (aus ollama/Modelfile)"),
            variable=self.gemini_modelfile_chk_var,
            command=self.on_toggle_gemini_modelfile_rules,
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
        ), "profile.gemini_modelfile_rules", "📄 Modelfile-Systemregeln für Gemini in Basis-Regeln übernehmen (aus ollama/Modelfile)")
        self.gemini_modelfile_chk.pack(side="left")

        # Top Ollama Management Card
        self.ollama_card = ctk.CTkFrame(self.tab_ai, corner_radius=CORNER_RADIUS_CARD)
        self.ollama_card.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)

        # Status row
        status_row = ctk.CTkFrame(self.ollama_card, fg_color="transparent")
        status_row.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_10, PAD_CONTAINER))

        self.ollama_status_lbl = self.register_i18n(ctk.CTkLabel(
            status_row,
            text=tr("profile.checking_ollama", "Prüfe Ollama-Status..."),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        ), "profile.checking_ollama", "Prüfe Ollama-Status...")
        self.ollama_status_lbl.pack(side="left")

        self.btn_refresh_ollama = self.register_i18n(ctk.CTkButton(
            status_row,
            text=tr("profile.scan_ollama_btn", "Status & Modelle scannen"),
            command=self.scan_ollama_status,
            width=BTN_WIDTH_SCAN_OLLAMA,
            fg_color=COLOR_BTN_GRAY30,
        ), "profile.scan_ollama_btn", "Status & Modelle scannen")
        self.btn_refresh_ollama.pack(side="right")

        # Download / Offline Frame (shown if offline)
        self.ollama_offline_frame = ctk.CTkFrame(self.ollama_card, fg_color="transparent")

        off_desc = AI_OFFLINE_DESC
        ctk.CTkLabel(
            self.ollama_offline_frame,
            text=off_desc,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        off_btns_row = ctk.CTkFrame(self.ollama_offline_frame, fg_color="transparent")
        off_btns_row.pack(anchor="w", pady=(PAD_NONE, PAD_CONTAINER))

        btn_start_ollama = ctk.CTkButton(
            off_btns_row,
            text=AI_BTN_START_SERVER,
            command=self.on_start_ollama_server,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=BTN_WIDTH_START_OLLAMA,
        )
        btn_start_ollama.pack(side="left", padx=(PAD_NONE, PAD_MD))

        btn_download_ollama = ctk.CTkButton(
            off_btns_row,
            text=AI_BTN_DOWNLOAD_OLLAMA,
            command=lambda: webbrowser.open(OLLAMA_DOWNLOAD_URL),
            fg_color=COLOR_PRIMARY_BLUE,
            width=BTN_WIDTH_DOWNLOAD_OLLAMA,
        )
        btn_download_ollama.pack(side="left")

        # Online Controls Frame (shown if online)
        self.ollama_online_frame = ctk.CTkFrame(self.ollama_card, fg_color="transparent")

        # Frame shown if no models are installed locally
        self.ollama_no_models_frame = ctk.CTkFrame(self.ollama_online_frame, fg_color=COLOR_PANEL_MUTED_BG, corner_radius=CORNER_RADIUS_MD)

        ctk.CTkLabel(
            self.ollama_no_models_frame,
            text=AI_NO_MODELS_TITLE,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_ORANGE,
        ).pack(anchor="w", padx=PAD_10, pady=(PAD_MD, PAD_XS))

        ctk.CTkLabel(
            self.ollama_no_models_frame,
            text=AI_NO_MODELS_DESC,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_BODY,
        ).pack(anchor="w", padx=PAD_10, pady=(PAD_NONE, PAD_GAP))

        no_models_btn_row = ctk.CTkFrame(self.ollama_no_models_frame, fg_color="transparent")
        no_models_btn_row.pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_MD))

        ctk.CTkButton(
            no_models_btn_row,
            text=AI_BTN_DOWNLOAD_QWEN,
            command=lambda: webbrowser.open(OLLAMA_LIBRARY_QWEN_URL),
            fg_color=COLOR_PRIMARY_BLUE,
            width=BTN_WIDTH_DOWNLOAD_MODEL,
        ).pack(side="left", padx=(PAD_NONE, PAD_MD))

        ctk.CTkButton(
            no_models_btn_row,
            text=AI_BTN_DOWNLOAD_LLAMA,
            command=lambda: webbrowser.open(OLLAMA_LIBRARY_LLAMA_URL),
            fg_color=COLOR_PRIMARY_BLUE,
            width=BTN_WIDTH_DOWNLOAD_MODEL,
        ).pack(side="left")

        # Model selection dropdown row
        model_row = ctk.CTkFrame(self.ollama_online_frame, fg_color="transparent")
        model_row.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        ctk.CTkLabel(model_row, text=AI_LABEL_SELECT_MODEL, font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD)).pack(side="left", padx=(PAD_NONE, PAD_10))

        self.ai_model_combo = ctk.CTkOptionMenu(
            model_row,
            values=[self.profile.ai_settings.model_name or DEFAULT_OLLAMA_MODEL],
            command=self.on_select_ai_model,
            width=COMBO_WIDTH_OLLAMA_MODEL,
        )
        self.ai_model_combo.set(self.profile.ai_settings.model_name or DEFAULT_OLLAMA_MODEL)
        self.ai_model_combo.pack(side="left", padx=(PAD_NONE, PAD_10))

        self.ai_model_entry = ctk.CTkEntry(model_row, placeholder_text=DEFAULT_OLLAMA_MODEL, width=ENTRY_WIDTH_OLLAMA_MODEL)
        self.ai_model_entry.insert(0, self.profile.ai_settings.model_name)
        self.ai_model_entry.pack(side="left")

        # Buttons row: Create PVS-Support, Preload, Unload, Stop Server
        btns_row = ctk.CTkFrame(self.ollama_online_frame, fg_color="transparent")
        btns_row.pack(fill="x", pady=(PAD_NONE, PAD_CONTAINER))

        btn_create_pvs = ctk.CTkButton(
            btns_row,
            text=AI_BTN_CREATE_PVS_MODEL,
            command=self.on_create_pvs_model,
            fg_color=COLOR_PURPLE_DARK,
            width=BTN_WIDTH_CREATE_PVS,
        )
        btn_create_pvs.pack(side="left", padx=(PAD_NONE, PAD_MD))

        btn_preload = ctk.CTkButton(
            btns_row,
            text=AI_BTN_PRELOAD_MODEL,
            command=self.on_preload_model,
            fg_color=COLOR_SUCCESS,
            width=BTN_WIDTH_PRELOAD,
        )
        btn_preload.pack(side="left", padx=(PAD_NONE, PAD_MD))

        btn_unload = ctk.CTkButton(
            btns_row,
            text=AI_BTN_UNLOAD_MODEL,
            command=self.on_unload_model,
            fg_color=COLOR_BTN_GRAY,
            width=BTN_WIDTH_ACTION,
        )
        btn_unload.pack(side="left", padx=(PAD_NONE, PAD_MD))

        btn_stop_server = ctk.CTkButton(
            btns_row,
            text=AI_BTN_STOP_SERVER,
            command=self.on_stop_ollama_server,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            width=BTN_WIDTH_ACTION,
        )
        btn_stop_server.pack(side="left")

        self.ollama_action_lbl = ctk.CTkLabel(
            self.ollama_card,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w",
        )
        self.ollama_action_lbl.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_NONE, PAD_GAP))

        # URL Entry & Checkbox row
        url_chk_row = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        url_chk_row.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        ctk.CTkLabel(url_chk_row, text=AI_LABEL_OLLAMA_URL).pack(side="left", padx=(PAD_NONE, PAD_CONTAINER))
        self.ai_url_entry = ctk.CTkEntry(url_chk_row, placeholder_text=DEFAULT_OLLAMA_URL, width=ENTRY_WIDTH_OLLAMA_URL)
        self.ai_url_entry.insert(0, self.profile.ai_settings.ollama_url)
        self.ai_url_entry.pack(side="left", padx=(PAD_NONE, PAD_15))

        self.ai_enable_chk = ctk.CTkSwitch(
            url_chk_row,
            text=AI_BTN_GLOBAL_TOGGLE,
            command=self.on_toggle_global_ai,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        )
        if self.profile.ai_settings.enable_ai:
            self.ai_enable_chk.select()
        else:
            self.ai_enable_chk.deselect()
        self.ai_enable_chk.pack(side="left")

        # Bottom Section: Base Rules Textbox (Expanding to fill remaining height)
        ctk.CTkLabel(
            self.tab_ai,
            text=AI_LABEL_BASE_RULES_TITLE,
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD),
        ).pack(anchor="w", pady=(PAD_CONTAINER, PAD_XS))

        ctk.CTkLabel(
            self.tab_ai,
            text=AI_LABEL_BASE_RULES_HINT,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_LABEL,
        ).pack(anchor="w", pady=(PAD_NONE, PAD_SM))

        self.ai_base_rules_txt = ctk.CTkTextbox(self.tab_ai)
        if self.profile.ai_settings.base_rules:
            self.ai_base_rules_txt.insert("1.0", "\n".join(self.profile.ai_settings.base_rules))
        self.ai_base_rules_txt.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_10))

        # Set paragraph line spacing for clear visual distinction between hard line breaks
        try:
            text_widget = getattr(self.ai_base_rules_txt, "_textbox", getattr(self.ai_base_rules_txt, "_textbox_widget", None))
            if text_widget:
                text_widget.config(spacing1=TEXTBOX_SPACING1_PARAGRAPH, spacing3=TEXTBOX_SPACING3_PARAGRAPH, spacing2=TEXTBOX_SPACING2_PARAGRAPH)
        except Exception:
            pass

        self.on_change_ai_provider(self.ai_provider_seg.get())
        self.scan_ollama_status()

    def get_modelfile_prompt_text(self) -> str:
        """Reads system rules text from ollama/Modelfile or DEFAULT_MODELFILE_PATH."""
        from pathlib import Path
        p = Path(DEFAULT_MODELFILE_PATH)
        if not p.exists():
            p = Path("ollama/Modelfile")
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8")
                if MODELFILE_SYSTEM_PREFIX in content:
                    start = content.index(MODELFILE_SYSTEM_PREFIX) + len(MODELFILE_SYSTEM_PREFIX)
                    end = content.find(MODELFILE_SYSTEM_SUFFIX, start)
                    if end != -1:
                        return content[start:end].strip()
            except Exception:
                pass
        return ""

    def on_toggle_gemini_modelfile_rules(self):
        use_mf = self.gemini_modelfile_chk_var.get()
        mf_text = self.get_modelfile_prompt_text()
        if not mf_text:
            return

        current_txt = self.ai_base_rules_txt.get("1.0", "end-1c").strip()
        marker = MODELFILE_SYSTEM_RULES_MARKER

        if use_mf:
            if mf_text not in current_txt:
                if current_txt:
                    new_txt = f"{current_txt}\n\n{marker}\n{mf_text}"
                else:
                    new_txt = f"{marker}\n{mf_text}"
                self.ai_base_rules_txt.delete("1.0", "end")
                self.ai_base_rules_txt.insert("1.0", new_txt)
        else:
            if mf_text in current_txt:
                cleaned = current_txt.replace(f"\n\n{marker}\n{mf_text}", "").replace(f"{marker}\n{mf_text}", "").replace(mf_text, "").strip()
                self.ai_base_rules_txt.delete("1.0", "end")
                self.ai_base_rules_txt.insert("1.0", cleaned)

    def on_change_ai_provider(self, value: str):
        # value is the translated caption the selector just switched to. Its
        # *position* among the current captions identifies the provider, so this
        # keeps working in every language - unlike the substring match on
        # "GEMINI" that used to stand here and only held because the brand name
        # survives translation.
        index = self.selected_choice_index(self.ai_provider_seg, value=value)
        is_gemini = AI_PROVIDER_KEYS[min(index, len(AI_PROVIDER_KEYS) - 1)] == "GEMINI"
        if is_gemini:
            self.gemini_card.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)
            self.ollama_card.pack_forget()
            if hasattr(self, "gemini_modelfile_chk_var") and self.gemini_modelfile_chk_var.get():
                self.on_toggle_gemini_modelfile_rules()
        else:
            self.gemini_card.pack_forget()
            self.ollama_card.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)
            mf_text = self.get_modelfile_prompt_text()
            if hasattr(self, "ai_base_rules_txt"):
                current_txt = self.ai_base_rules_txt.get("1.0", "end-1c").strip()
                marker = MODELFILE_SYSTEM_RULES_MARKER
                if mf_text and mf_text in current_txt:
                    cleaned = current_txt.replace(f"\n\n{marker}\n{mf_text}", "").replace(f"{marker}\n{mf_text}", "").replace(mf_text, "").strip()
                    self.ai_base_rules_txt.delete("1.0", "end")
                    self.ai_base_rules_txt.insert("1.0", cleaned)

    def on_toggle_show_gemini_key(self):
        current = self.gemini_key_entry.cget("show")
        if current == PASSWORD_CHAR_MASK:
            self.gemini_key_entry.configure(show=PASSWORD_CHAR_SHOW)
            self.btn_toggle_key_show.configure(text=ICON_PASSWORD_HIDE)
        else:
            self.gemini_key_entry.configure(show=PASSWORD_CHAR_MASK)
            self.btn_toggle_key_show.configure(text=ICON_PASSWORD_SHOW)

    def on_test_gemini_key(self):
        from services.i18n_service import tr
        key = self.gemini_key_entry.get().strip()
        model = self.gemini_model_combo.get()
        if not key:
            self.gemini_status_lbl.configure(text=tr("profile.enter_api_key", "⚠ Bitte API Key eingeben"), text_color=COLOR_TEXT_RED)
            return

        self.gemini_status_lbl.configure(text=tr("profile.checking_key", "🔍 Prüfe Key..."), text_color=COLOR_MUTED_LABEL)

        def worker():
            from services.ai_service import AiService
            svc = AiService(provider="GEMINI", gemini_api_key=key, gemini_model=model)
            ok, msg = svc.check_gemini_status(api_key=key, model=model)
            if self.winfo_exists():
                self.after(0, lambda: self.gemini_status_lbl.configure(
                    text=f"{ICON_STATUS_SUCCESS} {msg}" if ok else f"{ICON_STATUS_ERROR} {msg}",
                    text_color=COLOR_TEXT_GREEN if ok else COLOR_TEXT_RED
                ))

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def scan_ollama_status(self):
        if not hasattr(self, "ollama_status_lbl"):
            return

        self.ollama_status_lbl.configure(
            text=AI_STATUS_CHECKING,
            text_color=COLOR_MUTED_LABEL,
        )

        url = self.ai_url_entry.get().strip() if hasattr(self, "ai_url_entry") else self.profile.ai_settings.ollama_url
        current_model = self.ai_model_entry.get().strip() if hasattr(self, "ai_model_entry") else self.profile.ai_settings.model_name

        def worker():
            from services.ai_service import AiService
            svc = AiService(ollama_url=url, model_name=current_model)
            is_online, models = svc.check_ollama_status()
            running_models = svc.get_running_models() if is_online else []

            def done():
                try:
                    if not self.winfo_exists():
                        return
                    if not is_online:
                        self.ollama_status_lbl.configure(
                            text=AI_STATUS_OFFLINE_LABEL.format(url=url),
                            text_color=COLOR_TEXT_RED,
                        )
                        self.ollama_online_frame.pack_forget()
                        self.ollama_offline_frame.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_NONE, PAD_10))
                        if hasattr(self, "ai_model_combo"):
                            self.ai_model_combo.configure(values=[current_model or DEFAULT_OLLAMA_MODEL])
                    else:
                        self.ollama_offline_frame.pack_forget()
                        self.ollama_online_frame.pack(fill="x", padx=PAD_CARD_INSET, pady=(PAD_NONE, PAD_10))

                        if not self.profile.ai_settings.enable_ai:
                            self.ollama_status_lbl.configure(
                                text=AI_STATUS_ONLINE_DISABLED.format(count=len(models)),
                                text_color=COLOR_MUTED_DISABLED,
                            )
                        elif not running_models:
                            self.ollama_status_lbl.configure(
                                text=AI_STATUS_ONLINE_STANDBY.format(count=len(models)),
                                text_color=COLOR_TEXT_BLUE,
                            )
                        else:
                            self.ollama_status_lbl.configure(
                                text=AI_STATUS_ONLINE_LOADED.format(count=len(models), models=", ".join(running_models)),
                                text_color=COLOR_TEXT_GREEN,
                            )

                        if not models:
                            if hasattr(self, "ollama_no_models_frame"):
                                self.ollama_no_models_frame.pack(fill="x", pady=(PAD_NONE, PAD_10))
                        else:
                            if hasattr(self, "ollama_no_models_frame"):
                                self.ollama_no_models_frame.pack_forget()

                        if models:
                            self.ai_model_combo.configure(values=models)
                            if current_model in models:
                                self.ai_model_combo.set(current_model)
                            else:
                                self.ai_model_combo.set(models[0])
                                if hasattr(self, "ai_model_entry"):
                                    self.ai_model_entry.delete(0, "end")
                                    self.ai_model_entry.insert(0, models[0])
                except Exception:
                    pass

            try:
                self.after(0, done)
            except Exception:
                pass

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def on_start_ollama_server(self):
        from services.i18n_service import tr
        self.ollama_action_lbl.configure(text=AI_STATUS_STARTING, text_color=COLOR_TEXT_ORANGE)
        def worker():
            from services.ai_service import AiService
            url = self.ai_url_entry.get().strip() if hasattr(self, "ai_url_entry") else self.profile.ai_settings.ollama_url
            svc = AiService(ollama_url=url)
            ok, msg = svc.start_ollama_server()
            def done():
                try:
                    if not self.winfo_exists():
                        return
                    if ok:
                        self.ollama_action_lbl.configure(text=f"{ICON_STATUS_SUCCESS} {msg}", text_color=COLOR_TEXT_GREEN)
                        from ui.widgets.toast_notification import ToastNotification
                        ToastNotification(self, tr("profile.ollama_server_title", "Ollama Server"), tr("profile.ollama_starting", "Ollama Server wird gestartet..."))
                    else:
                        self.ollama_action_lbl.configure(text=f"{ICON_STATUS_ERROR} {msg}", text_color=COLOR_TEXT_RED)
                    self.after(DELAY_OLLAMA_STATUS_SCAN_MS, self.scan_ollama_status)
                except Exception:
                    pass
            try:
                self.after(0, done)
            except Exception:
                pass
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def on_stop_ollama_server(self):
        from services.i18n_service import tr
        self.ollama_action_lbl.configure(text=AI_STATUS_STOPPING, text_color=COLOR_TEXT_ORANGE)
        def worker():
            from services.ai_service import AiService
            url = self.ai_url_entry.get().strip() if hasattr(self, "ai_url_entry") else self.profile.ai_settings.ollama_url
            svc = AiService(ollama_url=url)
            ok, msg = svc.stop_ollama_server()
            def done():
                try:
                    if not self.winfo_exists():
                        return
                    self.ollama_action_lbl.configure(text=f"{ICON_STATUS_FLASH} {msg}", text_color=COLOR_TEXT_GRAY)
                    from ui.widgets.toast_notification import ToastNotification
                    ToastNotification(self, tr("profile.ollama_server_title", "Ollama Server"), tr("profile.ollama_stopped", "Ollama Server wurde beendet."))
                    self.scan_ollama_status()
                except Exception:
                    pass
            try:
                self.after(0, done)
            except Exception:
                pass
        import threading
        threading.Thread(target=worker, daemon=True).start()

    def on_toggle_global_ai(self):
        from services.i18n_service import tr
        enabled = bool(self.ai_enable_chk.get())
        self.profile.ai_settings.enable_ai = enabled

        if not enabled:
            self.ollama_action_lbl.configure(
                text=AI_STATUS_UNLOADING,
                text_color=COLOR_TEXT_ORANGE,
            )
            def worker():
                from services.ai_service import AiService
                url = self.ai_url_entry.get().strip() if hasattr(self, "ai_url_entry") else self.profile.ai_settings.ollama_url
                current_model = self.ai_model_entry.get().strip() if hasattr(self, "ai_model_entry") else self.profile.ai_settings.model_name
                svc = AiService(ollama_url=url, model_name=current_model)
                svc.unload_model()

                def done():
                    try:
                        if not self.winfo_exists():
                            return
                        self.ollama_action_lbl.configure(
                            text=AI_STATUS_UNLOADED,
                            text_color=COLOR_TEXT_GRAY,
                        )
                        from ui.widgets.toast_notification import ToastNotification
                        ToastNotification(self, tr("ai_constants.toast_ai_status_title", "KI-Status"), tr("ai_constants.toast_ai_disabled", "KI global deaktiviert & Modelle entladen"))
                        self.scan_ollama_status()
                    except Exception:
                        pass

                try:
                    self.after(0, done)
                except Exception:
                    pass

            import threading
            threading.Thread(target=worker, daemon=True).start()
        else:
            self.ollama_action_lbl.configure(
                text=AI_STATUS_ACTIVATED,
                text_color=COLOR_TEXT_GREEN,
            )
            from ui.widgets.toast_notification import ToastNotification
            ToastNotification(self, tr("ai_constants.toast_ai_status_title", "KI-Status"), tr("ai_constants.toast_ai_enabled", "KI global aktiviert"))
            self.scan_ollama_status()

    def on_select_ai_model(self, selected_model: str):
        if hasattr(self, "ai_model_entry"):
            self.ai_model_entry.delete(0, "end")
            self.ai_model_entry.insert(0, selected_model)
        self.profile.ai_settings.model_name = selected_model
        from services.i18n_service import tr
        self.ollama_action_lbl.configure(text=tr("profile.model_set_active", "Aktives Modell auf '{model}' gesetzt.", model=selected_model), text_color=COLOR_PRIMARY_BLUE)

    def on_create_pvs_model(self):
        from services.ai_service import AiService
        from services.i18n_service import tr
        url = self.ai_url_entry.get().strip() or self.profile.ai_settings.ollama_url
        svc = AiService(ollama_url=url)
        self.ollama_action_lbl.configure(text=tr("profile.creating_pvs_model", "⏳ Erstelle 'pvs-support' Modell aus Modelfile..."), text_color=COLOR_TEXT_ORANGE)
        self.update_idletasks()

        def worker():
            ok, msg = svc.create_pvs_support_model()
            def done():
                if ok:
                    self.ollama_action_lbl.configure(text=f"{ICON_STATUS_SUCCESS} {msg}", text_color=COLOR_TEXT_GREEN)
                    self.profile.ai_settings.model_name = DEFAULT_PVS_MODEL_NAME
                    self.scan_ollama_status()
                else:
                    self.ollama_action_lbl.configure(text=f"{ICON_STATUS_WARNING} {msg}", text_color=COLOR_TEXT_RED)
            self.after(0, done)

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def on_preload_model(self):
        from services.ai_service import AiService
        url = self.ai_url_entry.get().strip() or self.profile.ai_settings.ollama_url
        model = self.ai_model_entry.get().strip() or self.profile.ai_settings.model_name
        svc = AiService(ollama_url=url, model_name=model)
        from services.i18n_service import tr
        self.ollama_action_lbl.configure(text=tr("profile.model_loading", "⏳ Lade Modell '{model}' in den Speicher...", model=model), text_color=COLOR_TEXT_ORANGE)
        self.update_idletasks()

        def worker():
            ok, msg = svc.preload_model(model)
            def done():
                color = COLOR_TEXT_GREEN if ok else COLOR_TEXT_RED
                self.ollama_action_lbl.configure(text=f"{ICON_STATUS_SUCCESS if ok else ICON_STATUS_WARNING} {msg}", text_color=color)
                self.scan_ollama_status()
            self.after(0, done)

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def on_unload_model(self):
        from services.ai_service import AiService
        url = self.ai_url_entry.get().strip() or self.profile.ai_settings.ollama_url
        model = self.ai_model_entry.get().strip() or self.profile.ai_settings.model_name
        svc = AiService(ollama_url=url, model_name=model)
        from services.i18n_service import tr
        self.ollama_action_lbl.configure(text=tr("profile.model_unloading", "⏳ Entlade Modell '{model}' aus dem Speicher...", model=model), text_color=COLOR_TEXT_ORANGE)
        self.update_idletasks()

        def worker():
            ok, msg = svc.unload_model(model)
            def done():
                color = COLOR_TEXT_GREEN if ok else COLOR_TEXT_RED
                self.ollama_action_lbl.configure(text=f"{ICON_STATUS_SUCCESS if ok else ICON_STATUS_WARNING} {msg}", text_color=color)
                self.scan_ollama_status()
            self.after(0, done)

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def refresh_ai_tab_labels(self) -> None:
        """Re-translates this tab's option lists on a language change.

        The plain labels are handled by register_i18n; the provider selector
        carries its texts as *values*, which register_i18n cannot reach.
        """
        if hasattr(self, "ai_provider_seg"):
            self.retranslate_choices(self.ai_provider_seg, AI_PROVIDER_CHOICES)

    def reload_ai_fields(self) -> None:
        ai = getattr(self.profile, "ai_settings", None)
        if ai is None:
            return

        current_provider = getattr(ai, "provider", "OLLAMA").upper()
        if hasattr(self, "ai_provider_seg"):
            from services.i18n_service import tr
            self.ai_provider_seg.set(tr("profile.provider_gemini", "GOOGLE GEMINI (Cloud)") if current_provider == "GEMINI" else tr("profile.provider_ollama", "OLLAMA (Lokal)"))
            self.on_change_ai_provider(self.ai_provider_seg.get())

        if hasattr(self, "anonymize_chk_var"):
            self.anonymize_chk_var.set(bool(getattr(ai, "enable_anonymization", True)))

        if hasattr(self, "gemini_key_entry"):
            self.gemini_key_entry.delete(0, "end")
            self.gemini_key_entry.insert(0, getattr(ai, "gemini_api_key", "") or "")

        if hasattr(self, "gemini_model_combo"):
            saved_g_model = getattr(ai, "gemini_model", DEFAULT_GEMINI_MODEL)
            self.gemini_model_combo.set(saved_g_model if saved_g_model in AVAILABLE_GEMINI_MODELS else DEFAULT_GEMINI_MODEL)

        if hasattr(self, "gemini_status_lbl"):
            self.gemini_status_lbl.configure(text="")

        if hasattr(self, "gemini_modelfile_chk_var"):
            self.gemini_modelfile_chk_var.set(bool(getattr(ai, "use_modelfile_rules_for_gemini", False)))

        if hasattr(self, "ai_model_combo"):
            m_name = getattr(ai, "model_name", DEFAULT_OLLAMA_MODEL) or DEFAULT_OLLAMA_MODEL
            self.ai_model_combo.set(m_name)

        if hasattr(self, "ai_model_entry"):
            self.ai_model_entry.delete(0, "end")
            self.ai_model_entry.insert(0, getattr(ai, "model_name", "") or "")

        if hasattr(self, "ai_url_entry"):
            self.ai_url_entry.delete(0, "end")
            self.ai_url_entry.insert(0, getattr(ai, "ollama_url", DEFAULT_OLLAMA_URL) or DEFAULT_OLLAMA_URL)

        if hasattr(self, "ai_enable_chk"):
            if getattr(ai, "enable_ai", True):
                self.ai_enable_chk.select()
            else:
                self.ai_enable_chk.deselect()

        if hasattr(self, "ai_base_rules_txt"):
            self.ai_base_rules_txt.delete("1.0", "end")
            rules = getattr(ai, "base_rules", [])
            if rules:
                self.ai_base_rules_txt.insert("1.0", "\n".join(rules))

    def save_ai_settings(self) -> bool:
        provider_val = AI_PROVIDER_KEYS[self.selected_choice_index(self.ai_provider_seg)]
        self.profile.ai_settings.provider = provider_val
        self.profile.ai_settings.ollama_url = self.ai_url_entry.get().strip()
        self.profile.ai_settings.model_name = self.ai_model_entry.get().strip()
        self.profile.ai_settings.gemini_api_key = self.gemini_key_entry.get().strip()
        self.profile.ai_settings.gemini_model = self.gemini_model_combo.get()
        self.profile.ai_settings.enable_anonymization = self.anonymize_chk_var.get()
        self.profile.ai_settings.enable_ai = bool(self.ai_enable_chk.get())
        self.profile.ai_settings.use_modelfile_rules_for_gemini = self.gemini_modelfile_chk_var.get()
        raw_rules = self.ai_base_rules_txt.get("1.0", "end-1c").splitlines()
        self.profile.ai_settings.base_rules = [r.strip() for r in raw_rules if r.strip()]
        return True

