import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from constants import DIALOG_DIMENSIONS
from utils.ui_utils import create_highlighted_label, bind_mouse_wheel_to_canvas


# Article order for the navigation list. The texts themselves live in
# locales/{de,en,sv}.json under "help_content" - they used to be duplicated here
# as a 543-line German constant, which meant the help could not be translated
# with the tr() mechanism used everywhere else.
HELP_ARTICLE_IDS = (
    "first_steps",
    "basics",
    "ui_customization",
    "praxis",
    "case_lifecycle",
    "scoring",
    "schemas",
    "convert_schema",
    "export",
    "wiki",
    "p2p",
    "shortcuts",
    "storage_paths",
    "template_editor",
    "handover_followup",
    "email_calendar_outlook",
    "case_print_reporting",
    "ai_ollama_management",
    "stepper_time_picker",
    "internal_cases",
    "cobra_crm_import",
    "snippets_manager",
    "repeatable_sub_forms",
    "analytics_kpi_dashboard",
    "advanced_search_filters",
    "attachments_and_screenshots",
    "zip_backup_restore",
    "email_webhook_integration",
    "faq_troubleshooting",
)


def _localized(key: str) -> str | None:
    """Returns the translation for key, or None if the locale files have no entry.

    tr() hands back the key itself when nothing is found, which would otherwise
    end up on screen as "help_content.basics.title".
    """
    from services.i18n_service import tr
    value = tr(key, default=None)
    if not isinstance(value, str) or value == key or not value.strip():
        return None
    return value


def get_help_articles() -> list[dict]:
    """Builds the article list in the active language, in HELP_ARTICLE_IDS order.

    Articles missing from the locale files are skipped rather than rendered as
    raw keys, so a damaged locale file degrades to fewer topics, not to garbage.
    """
    articles = []
    for article_id in HELP_ARTICLE_IDS:
        title = _localized(f"help_content.{article_id}.title")
        content = _localized(f"help_content.{article_id}.content")
        if not title or not content:
            continue
        articles.append({
            "id": article_id,
            "title": title,
            "category": _localized(f"help_content.{article_id}.category") or "",
            "content": content,
        })
    return articles


# Snapshot in the language active at import time. Kept as a module-level name for
# callers that only need the available article ids; the dialog itself always
# re-reads via get_help_articles() so a language switch takes effect.
HELP_ARTICLES = get_help_articles()


class HelpDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent)
        from services.i18n_service import tr

        w, h = DIALOG_DIMENSIONS["help"]
        self.setup_window(
            parent,
            tr("dialog_titles.help", "📖 Handbuch & Anwendungsdokumentation"),
            (w, h),
            min_size=(960, 600),

            title_factory=lambda: tr("dialog_titles.help", "📖 Handbuch & Anwendungsdokumentation"),
        )

        # Make modal window

        self.articles = self.get_localized_articles()
        self.filtered_articles = list(self.articles)
        self.active_article = self.articles[0] if self.articles else None

        self.create_widgets()
        if self.active_article:
            self.select_article(self.active_article["id"])

    def get_localized_articles(self) -> list[dict]:
        return get_help_articles()

    def refresh_ui_labels(self):
        """Reloads the articles in the newly selected language and redraws."""
        from services.i18n_service import tr
        super().refresh_ui_labels()
        if hasattr(self, "header_lbl"):
            self.header_lbl.configure(text=tr("help_dialog.header", "📖 Handbuch & Hilfe"))
        if hasattr(self, "nav_title_lbl"):
            self.nav_title_lbl.configure(text=tr("help_dialog.nav_title", "Themenübersicht"))
        if hasattr(self, "search_entry"):
            self.search_entry.configure(placeholder_text=tr("help_dialog.search_placeholder", "🔍 Themen & Stichworte suchen..."))

        active_id = self.active_article["id"] if self.active_article else None
        self.articles = self.get_localized_articles()
        self.on_search_changed()
        if active_id and any(a["id"] == active_id for a in self.articles):
            self.select_article(active_id)
        elif self.articles:
            self.select_article(self.articles[0]["id"])
        else:
            self.render_nav_list()

    def create_widgets(self):
        from services.i18n_service import tr

        # Main Layout: Top search bar, Left navigation list, Right detail view
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        self.header_lbl = self.register_i18n(ctk.CTkLabel(top_bar, text=tr("help_dialog.header", "📖 Handbuch & Hilfe"), font=ctk.CTkFont(size=16, weight="bold")), "help_dialog.header", "📖 Handbuch & Hilfe")
        self.header_lbl.pack(side="left", padx=10)

        self.search_entry = self.register_i18n(ctk.CTkEntry(top_bar, placeholder_text=tr("help_dialog.search_placeholder", "🔍 Themen & Stichworte suchen..."), width=320), "help_dialog.search_placeholder", "🔍 Themen & Stichworte suchen...", attr="placeholder_text")
        self.search_entry.pack(side="right", padx=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Left Sidebar (Article list)
        left_frame = ctk.CTkFrame(body_frame, width=280)
        left_frame.pack(side="left", fill="y", padx=(0, 5), pady=0)
        left_frame.pack_propagate(False)

        self.nav_title_lbl = self.register_i18n(ctk.CTkLabel(left_frame, text=tr("help_dialog.nav_title", "Themenübersicht"), font=ctk.CTkFont(size=13, weight="bold")), "help_dialog.nav_title", "Themenübersicht")
        self.nav_title_lbl.pack(anchor="w", padx=10, pady=(10, 5))

        self.nav_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.nav_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right Detail View (Article Content)
        right_frame = ctk.CTkFrame(body_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)

        self.article_title_lbl = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(size=18, weight="bold"), anchor="w")
        self.article_title_lbl.pack(fill="x", padx=15, pady=(15, 5))

        self.content_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        self.content_scroll.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.render_nav_list()

    def render_nav_list(self):
        from services.i18n_service import tr

        for w in self.nav_scroll.winfo_children():
            w.destroy()

        if not self.filtered_articles:
            self.register_i18n(ctk.CTkLabel(self.nav_scroll, text=tr("help_dialog.no_topics", "Keine Themen gefunden."), text_color="gray"), "help_dialog.no_topics", "Keine Themen gefunden.").pack(pady=20)
            return

        active_id = self.active_article["id"] if self.active_article else None
        query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        query_lower = query.lower()

        for art in self.filtered_articles:
            is_active = art["id"] == active_id
            fg_color = ("gray75", "gray30") if is_active else ("gray85", "gray20")

            if not query:
                btn = ctk.CTkButton(
                    self.nav_scroll,
                    text=art["title"],
                    anchor="w",
                    fg_color=fg_color,
                    hover_color=("gray70", "gray35"),
                    text_color=("black", "white") if is_active else ("gray10", "gray90"),
                    command=lambda a_id=art["id"]: self.select_article(a_id)
                )
                btn.pack(fill="x", pady=3, padx=2)
            else:
                card = ctk.CTkFrame(self.nav_scroll, fg_color=fg_color, corner_radius=6, cursor="hand2")
                card.pack(fill="x", pady=3, padx=2)

                def on_enter(e, c=card):
                    c.configure(fg_color=("gray70", "gray35"))

                def on_leave(e, c=card, col=fg_color):
                    c.configure(fg_color=col)

                card.bind("<Enter>", on_enter)
                card.bind("<Leave>", on_leave)

                def on_click(e=None, a_id=art["id"]):
                    self.select_article(a_id)

                card.bind("<Button-1>", on_click)

                content_lower = art.get("content", "").lower()
                idx = content_lower.find(query_lower) if query_lower else -1
                has_content_match = idx != -1 and query_lower not in art["title"].lower()

                title_lbl = create_highlighted_label(
                    card,
                    text=art["title"],
                    query=query,
                    font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                    text_color=("black", "white") if is_active else ("gray10", "gray90"),
                    bg_color=fg_color,
                    wrap="none",
                    on_click=on_click,
                    scroll_frame=self.nav_scroll,
                )
                title_lbl.pack(fill="x", padx=8, pady=(4, 2) if has_content_match else (6, 6))

                if has_content_match:
                    raw_content = art.get("content", "")
                    start = max(0, idx - 20)
                    end = min(len(raw_content), idx + len(query) + 30)
                    snippet = raw_content[start:end].replace("\n", " ").strip()
                    if start > 0:
                        snippet = f"...{snippet}"
                    if end < len(raw_content):
                        snippet = f"{snippet}..."

                    snip_lbl = create_highlighted_label(
                        card,
                        text=snippet,
                        query=query,
                        font=ctk.CTkFont(size=11),
                        text_color=("gray40", "gray70"),
                        bg_color=fg_color,
                        wrap="none",
                        on_click=on_click,
                        scroll_frame=self.nav_scroll,
                    )
                    snip_lbl.pack(fill="x", padx=8, pady=(0, 4))

                bind_mouse_wheel_to_canvas(card, self.nav_scroll)

    def select_article(self, article_id: str):
        article = next((a for a in self.articles if a["id"] == article_id), None)
        if not article:
            return

        self.active_article = article
        self.article_title_lbl.configure(text=article["title"])

        self.render_markdown(article["content"])
        self.render_nav_list()

    def render_markdown(self, markdown_text: str):
        import re

        for w in self.content_scroll.winfo_children():
            w.destroy()

        lines = markdown_text.strip().split("\n")
        in_table = False
        table_rows = []

        def clean_inline(text: str) -> str:
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
            cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)
            return cleaned.strip()

        def flush_table():
            nonlocal in_table, table_rows
            if not table_rows:
                return

            table_frame = ctk.CTkFrame(self.content_scroll, fg_color=("gray85", "gray20"), corner_radius=6)
            table_frame.pack(fill="x", padx=10, pady=8)

            header_cols = [clean_inline(c) for c in table_rows[0].strip("|").split("|")]
            data_rows = table_rows[2:] if len(table_rows) > 2 and "---" in table_rows[1] else table_rows[1:]

            # Header Frame
            hdr_frame = ctk.CTkFrame(table_frame, fg_color=("gray70", "gray30"), corner_radius=4)
            hdr_frame.pack(fill="x", padx=4, pady=(4, 2))
            for col_txt in header_cols:
                ctk.CTkLabel(hdr_frame, text=col_txt.strip(), font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=4)

            # Data Rows
            for r_idx, r_line in enumerate(data_rows):
                r_cols = [clean_inline(c) for c in r_line.strip("|").split("|")]
                r_bg = ("gray90", "gray22") if r_idx % 2 == 0 else ("gray85", "gray25")
                row_frame = ctk.CTkFrame(table_frame, fg_color=r_bg, corner_radius=2)
                row_frame.pack(fill="x", padx=4, pady=1)

                for col_txt in r_cols:
                    ctk.CTkLabel(row_frame, text=col_txt.strip(), font=ctk.CTkFont(size=11), anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=4)

            table_rows = []
            in_table = False

        for line in lines:
            stripped = line.strip()

            # Check Table line
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_rows.append(stripped)
                continue
            elif in_table:
                flush_table()

            if not stripped:
                continue

            # Horizontal rule
            if stripped in ("---", "***", "___"):
                sep = ctk.CTkFrame(self.content_scroll, height=2, fg_color=("gray75", "gray35"))
                sep.pack(fill="x", padx=10, pady=10)
                continue

            # Headings
            if stripped.startswith("### "):
                txt = clean_inline(stripped[4:])
                lbl = ctk.CTkLabel(self.content_scroll, text=txt, font=ctk.CTkFont(size=15, weight="bold"), text_color=("dodgerblue", "#4dabf7"), anchor="w")
                lbl.pack(fill="x", padx=10, pady=(12, 4))
                continue

            if stripped.startswith("#### "):
                txt = clean_inline(stripped[5:])
                lbl = ctk.CTkLabel(self.content_scroll, text=txt, font=ctk.CTkFont(size=13, weight="bold"), text_color=("gray10", "gray90"), anchor="w")
                lbl.pack(fill="x", padx=10, pady=(8, 2))
                continue

            # Lists (unordered or ordered)
            is_bullet = stripped.startswith("- ") or stripped.startswith("* ")
            is_num = bool(re.match(r'^\d+\.\s', stripped))

            if is_bullet or is_num:
                prefix = "• " if is_bullet else stripped.split()[0] + " "
                raw_body = stripped.split(" ", 1)[1] if " " in stripped else stripped
                clean_body = clean_inline(raw_body)

                row = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)

                bullet_lbl = ctk.CTkLabel(row, text=prefix, font=ctk.CTkFont(size=12, weight="bold"), text_color=("dodgerblue", "cyan"), anchor="nw", width=20)
                bullet_lbl.pack(side="left", anchor="nw")

                txt_lbl = ctk.CTkLabel(row, text=clean_body, font=ctk.CTkFont(size=12), anchor="w", justify="left", wraplength=560)
                txt_lbl.pack(side="left", fill="x", expand=True)
                continue

            # Standard Paragraph
            clean_para = clean_inline(stripped)
            para_lbl = ctk.CTkLabel(self.content_scroll, text=clean_para, font=ctk.CTkFont(size=12), anchor="w", justify="left", wraplength=580)
            para_lbl.pack(fill="x", padx=10, pady=3)

        if in_table:
            flush_table()

    def on_search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()
        if not query:
            self.filtered_articles = list(self.articles)
        else:
            self.filtered_articles = [
                a for a in self.articles
                if query in a["title"].lower() or query in a["content"].lower() or query in a["category"].lower()
            ]

        if self.filtered_articles and self.active_article not in self.filtered_articles:
            self.active_article = self.filtered_articles[0]
            self.select_article(self.active_article["id"])

        self.render_nav_list()
