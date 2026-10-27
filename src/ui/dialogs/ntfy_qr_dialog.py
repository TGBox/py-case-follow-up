import webbrowser
import customtkinter as ctk

from constants import (
    BTN_WIDTH_ACTION,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_QR_BACKGROUND,
    COLOR_QR_ERROR_TEXT,
    CORNER_RADIUS_MD,
    DEFAULT_NTFY_SERVER_URL,
    DIALOG_DIMENSIONS,
    FONT_SIZE_BODY,
    FONT_SIZE_TITLE_SM,
    FONT_WEIGHT_BOLD,
    NTFY_QR_SIZE,
    NTFY_QR_URL_ENTRY_WIDTH,
    NTFY_QR_WRAPLENGTH,
    PAD_CONTAINER,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
)
from services.i18n_service import tr
from services.ntfy_service import NtfyService
from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast_notification import ToastNotification


class NtfyQrDialog(BaseDialog):
    """Modal dialog displaying a scannable QR code to easily subscribe to an ntfy topic on a smartphone."""

    def __init__(self, parent, topic: str, server_url: str = DEFAULT_NTFY_SERVER_URL) -> None:
        super().__init__(parent)
        self.topic = (topic or "").strip()
        self.server_url = server_url or DEFAULT_NTFY_SERVER_URL
        self.target_url = NtfyService.get_topic_url(self.topic, self.server_url)

        self.setup_window(
            parent,
            title=tr("ntfy.qr_dialog_title", "Smartphone koppeln (ntfy)"),
            size=DIALOG_DIMENSIONS["ntfy_qr"],
            resizable=False,
            modal=True,
            center=True,
        )

        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=PAD_CONTAINER)

        # Header Title
        title_lbl = ctk.CTkLabel(
            container,
            text=tr("ntfy.qr_dialog_heading", "Thema auf Smartphone scannen"),
            font=ctk.CTkFont(size=FONT_SIZE_TITLE_SM, weight=FONT_WEIGHT_BOLD),
        )
        title_lbl.pack(pady=(PAD_NONE, PAD_XS))

        # Description
        desc_lbl = ctk.CTkLabel(
            container,
            text=tr(
                "ntfy.qr_dialog_desc",
                "Scanne diesen QR-Code mit deiner Smartphone-Kamera oder der ntfy-App, um das Thema '{topic}' direkt zu abonnieren:",
                topic=self.topic,
            ),
            font=ctk.CTkFont(size=FONT_SIZE_BODY),
            wraplength=NTFY_QR_WRAPLENGTH,
            justify="center",
        )
        desc_lbl.pack(pady=(PAD_NONE, PAD_MD))

        # QR-Code Canvas / Frame (always on pure white background with border for optimal camera readability)
        qr_frame = ctk.CTkFrame(
            container,
            fg_color=COLOR_QR_BACKGROUND,
            corner_radius=CORNER_RADIUS_MD,
            width=NTFY_QR_SIZE + PAD_CONTAINER,
            height=NTFY_QR_SIZE + PAD_CONTAINER,
        )
        qr_frame.pack(pady=(PAD_NONE, PAD_MD))
        qr_frame.pack_propagate(False)

        try:
            pil_image = NtfyService.generate_qr_image(self.target_url)
            self.qr_ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(NTFY_QR_SIZE, NTFY_QR_SIZE),
            )
            qr_label = ctk.CTkLabel(qr_frame, image=self.qr_ctk_image, text="")
            qr_label.pack(expand=True, fill="both", padx=PAD_SM, pady=PAD_SM)
        except Exception as e:
            err_lbl = ctk.CTkLabel(
                qr_frame,
                text=f"QR-Code Fehler:\n{e}",
                text_color=COLOR_QR_ERROR_TEXT,
                justify="center",
            )
            err_lbl.pack(expand=True, fill="both", padx=PAD_SM, pady=PAD_SM)

        # URL Textbox / Entry (read-only)
        url_entry = ctk.CTkEntry(
            container,
            width=NTFY_QR_URL_ENTRY_WIDTH,
            justify="center",
        )
        url_entry.insert(0, self.target_url)
        url_entry.configure(state="readonly")
        url_entry.pack(pady=(PAD_NONE, PAD_LG))

        # Action Button Row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", pady=(PAD_NONE, PAD_XS))

        open_browser_btn = ctk.CTkButton(
            btn_row,
            text=tr("ntfy.btn_open_browser", "🌐 Im Browser öffnen"),
            command=self._on_open_browser,
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_MUTED_GRAY_HOVER,
        )
        open_browser_btn.pack(side="left", expand=True, fill="x", padx=(PAD_NONE, PAD_XS))

        copy_link_btn = ctk.CTkButton(
            btn_row,
            text=tr("ntfy.btn_copy_link", "📋 Link kopieren"),
            command=self._on_copy_link,
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_MUTED_GRAY_HOVER,
        )
        copy_link_btn.pack(side="left", expand=True, fill="x", padx=(PAD_XS, PAD_NONE))

        # Close Button
        close_btn = ctk.CTkButton(
            container,
            text=tr("ntfy.btn_close", "Schließen"),
            command=self.destroy,
            width=BTN_WIDTH_ACTION,
        )
        close_btn.pack(pady=(PAD_SM, PAD_NONE))

    def _on_open_browser(self) -> None:
        webbrowser.open(self.target_url)

    def _on_copy_link(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.target_url)
        ToastNotification(
            self,
            title=tr("ntfy.qr_dialog_title", "Smartphone koppeln (ntfy)"),
            message=tr("ntfy.link_copied_toast", "Link in die Zwischenablage kopiert."),
        )
