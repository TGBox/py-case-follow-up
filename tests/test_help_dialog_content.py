"""Tests for HelpDialog articles, search indexing, and category filtering."""

import customtkinter as ctk
import pytest
from ui.dialogs.help_dialog import HELP_ARTICLES, HelpDialog


def test_help_articles_coverage():
    """Verify HELP_ARTICLES contains entries for all major features including email/calendar/outlook,

    print reporting, and time pickers.
    """
    article_ids = [a["id"] for a in HELP_ARTICLES]
    assert "email_calendar_outlook" in article_ids
    assert "case_print_reporting" in article_ids
    assert "stepper_time_picker" in article_ids
    assert "handover_followup" in article_ids
    assert "wiki" in article_ids


def test_help_dialog_search_filter():
    """Verify HelpDialog filters articles by keyword and selection."""
    app = ctk.CTk()
    app.withdraw()

    dialog = HelpDialog(app)

    # Search for Outlook
    dialog.search_entry.insert(0, "Outlook")
    dialog.on_search_changed()

    filtered_ids = [a["id"] for a in dialog.filtered_articles]
    assert "email_calendar_outlook" in filtered_ids

    dialog.select_article("email_calendar_outlook")
    assert dialog.active_article["id"] == "email_calendar_outlook"
    assert "Outlook" in dialog.article_title_lbl.cget("text")

    dialog.destroy()
    app.destroy()
