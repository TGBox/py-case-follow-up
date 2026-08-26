"""Tests for CalendarDialog time picker range (07:00 - 20:00) and hour/minute steppers."""

import customtkinter as ctk
import pytest
from ui.widgets.date_picker import CalendarDialog


def test_calendar_dialog_time_range_and_steppers():
    """Verify CalendarDialog restricts hours to 07-20 and steppers modify hours and minutes correctly."""
    app = ctk.CTk()
    app.withdraw()

    dialog = CalendarDialog(app, initial_date="2026-08-25T14:30:00", include_time=True)

    # Initial state
    assert dialog.hour_var.get() == "14"
    assert dialog.minute_var.get() == "30"

    # Test hour range options
    hours = dialog.hour_menu.cget("values")
    assert hours[0] == "07"
    assert hours[-1] == "20"
    assert len(hours) == 14  # 7 to 20 inclusive

    # Test hour stepper up and down
    dialog.step_hour(1)
    assert dialog.hour_var.get() == "15"

    dialog.step_hour(-2)
    assert dialog.hour_var.get() == "13"

    # Clamping at boundary 20 and 07
    dialog.hour_var.set("20")
    dialog.step_hour(1)
    assert dialog.hour_var.get() == "20"

    dialog.hour_var.set("07")
    dialog.step_hour(-1)
    assert dialog.hour_var.get() == "07"

    # Test minute steppers (+5 / -5)
    dialog.minute_var.set("30")
    dialog.step_minute(5)
    assert dialog.minute_var.get() == "35"

    dialog.step_minute(-10)
    assert dialog.minute_var.get() == "25"

    # Minute wrap-around
    dialog.minute_var.set("55")
    dialog.step_minute(5)
    assert dialog.minute_var.get() == "00"

    dialog.destroy()
    app.destroy()
