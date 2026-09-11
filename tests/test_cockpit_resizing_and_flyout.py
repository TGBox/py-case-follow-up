"""Unit tests for Cockpit proportional 3-column resizing, flexible follow-up input,
title truncation, and vector rendering configuration.
"""
from datetime import datetime
from typing import Any
import pytest
from unittest.mock import MagicMock
import customtkinter as ctk
from customtkinter.windows.widgets.core_rendering import DrawEngine

from utils.datetime_utils import parse_flexible_followup_input
from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
from ui.views.cockpit_view import CockpitView


def test_draw_engine_is_polygon_shapes():
    """Verify that DrawEngine uses polygon_shapes for reliable multi-monitor DPI scaling."""
    assert DrawEngine.preferred_drawing_method == "polygon_shapes"


class TestFlexibleFollowupInput:
    def test_empty_and_invalid(self):
        assert parse_flexible_followup_input("") is None
        assert parse_flexible_followup_input("   ") is None
        assert parse_flexible_followup_input("invalid") is None
        assert parse_flexible_followup_input("99:99") is None

    def test_time_only_uses_current_date(self):
        now = datetime.now()
        res = parse_flexible_followup_input("14:30")
        assert res is not None
        assert res.year == now.year
        assert res.month == now.month
        assert res.day == now.day
        assert res.hour == 14
        assert res.minute == 30

    def test_date_only_uses_current_time(self):
        now = datetime.now()
        res = parse_flexible_followup_input("15.11.2026")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == now.hour
        assert res.minute == now.minute

    def test_iso_date_only_uses_current_time(self):
        now = datetime.now()
        res = parse_flexible_followup_input("2026-11-15")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == now.hour
        assert res.minute == now.minute

    def test_combined_date_and_time(self):
        res = parse_flexible_followup_input("15.11.2026 10:45")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == 10
        assert res.minute == 45

    def test_combined_iso_datetime(self):
        res = parse_flexible_followup_input("2026-11-15 08:30")
        assert res is not None
        assert res.year == 2026
        assert res.month == 11
        assert res.day == 15
        assert res.hour == 8
        assert res.minute == 30


class TestTitleTruncation:
    def test_short_title_unchanged(self):
        short = "Kurzer Betreff"
        assert FollowupFlyoutDialog._truncate_title_to_two_lines(short, line_length=50) == short

    def test_long_title_capped_at_two_lines(self):
        long_title = "Das ist ein extrem langer Titel fuer einen Supportfall, welcher sich ueber viele Zeilen hinweg erstrecken koennte und deshalb gekuerzt werden muss, damit der Button nicht verschwindet."
        result = FollowupFlyoutDialog._truncate_title_to_two_lines(long_title, line_length=45)
        lines = result.split("\n")
        assert len(lines) <= 2
        assert result.endswith("...")


class TestCockpitProportionalResizing:
    def test_cockpit_resize_user_example(self):
        """User example: 600px -> 450px:
        Initial: mid=400, left=100, right=100.
        Delta: -150 -> mid: -100 (300), left: -25 (75), right: -25 (75).
        """
        view: Any = CockpitView.__new__(CockpitView)
        view.paned = MagicMock()
        view.paned.winfo_exists.return_value = True
        view.paned.winfo_width.return_value = 450
        view._last_paned_width = 600
        view._in_paned_configure = False

        # sash0 is at 100, sash1 is at 500 (so right = 600 - 500 = 100, mid = 500 - 100 = 400)
        view.paned.sash_coord.side_effect = lambda idx: [100, 0] if idx == 0 else [500, 0]
        view.profile = MagicMock()
        view.profile.ui_settings.column_widths = {}

        mock_event = MagicMock()
        mock_event.widget = view.paned
        mock_event.width = 450

        view._on_paned_configure(mock_event)

        # Placed sashes:
        # new_left = 100 - 25 = 75
        # new_sash0 = 75
        # new_mid = 400 - 100 = 300
        # new_right = 100 - 25 = 75
        # new_sash1 = 450 - 75 = 375
        view.paned.sash_place.assert_any_call(0, 75, 0)
        view.paned.sash_place.assert_any_call(1, 375, 0)
        assert view._last_paned_width == 450

    def test_cockpit_resize_expansion(self):
        """Expansion: 450px -> 600px:
        Initial: mid=300, left=75, right=75.
        Delta: +150 -> mid: +100 (400), left: +25 (100), right: +25 (100).
        """
        view: Any = CockpitView.__new__(CockpitView)
        view.paned = MagicMock()
        view.paned.winfo_exists.return_value = True
        view.paned.winfo_width.return_value = 600
        view._last_paned_width = 450
        view._in_paned_configure = False

        view.paned.sash_coord.side_effect = lambda idx: [75, 0] if idx == 0 else [375, 0]
        view.profile = MagicMock()
        view.profile.ui_settings.column_widths = {}

        mock_event = MagicMock()
        mock_event.widget = view.paned
        mock_event.width = 600

        view._on_paned_configure(mock_event)

        view.paned.sash_place.assert_any_call(0, 100, 0)
        view.paned.sash_place.assert_any_call(1, 500, 0)
        assert view._last_paned_width == 600
