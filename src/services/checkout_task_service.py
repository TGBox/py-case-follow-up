"""Task service for managing recurring checklist items, dated tasks, and daily notes.

Provides midnight reset handling for tasks and sticky notes.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from models.profile import CheckoutSettings


class CheckoutTaskService:
    """Manages tasks, state transitions, and midnight rollover for checkout companion."""

    @classmethod
    def check_and_perform_midnight_reset(
        cls, settings: CheckoutSettings, current_date_str: str | None = None
    ) -> bool:
        """Check if date has rolled over since last tasks date, and reset items accordingly.

        Returns True if settings were modified and need persisting.
        """
        today = current_date_str or date.today().isoformat()
        if settings.last_tasks_date == today:
            return False

        # Reset all recurring tasks to undone
        for task in settings.recurring_tasks:
            if task.get("done"):
                task["done"] = False

        # Clear daily note if not marked to keep overnight
        if not settings.daily_note_keep_overnight and settings.daily_note_text:
            settings.daily_note_text = ""

        # Update last tasks date
        settings.last_tasks_date = today
        return True

    @classmethod
    def add_dated_task(
        cls, settings: CheckoutSettings, text: str, date_str: str | None = None
    ) -> dict[str, Any]:
        """Add a one-off dated task to the checkout settings."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Task text cannot be empty")

        target_date = date_str or date.today().isoformat()
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "text": cleaned_text,
            "date": target_date,
            "done": False,
        }
        settings.dated_tasks.append(task)
        return task

    @classmethod
    def add_recurring_task(cls, settings: CheckoutSettings, text: str) -> dict[str, Any]:
        """Add a recurring task template."""
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Task text cannot be empty")

        task_id = f"rec_{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "text": cleaned_text,
            "done": False,
        }
        settings.recurring_tasks.append(task)
        return task

    @classmethod
    def toggle_task(cls, settings: CheckoutSettings, task_id: str) -> bool:
        """Toggle the done state of a recurring or dated task.

        Returns True if found and toggled.
        """
        for task in settings.recurring_tasks:
            if task.get("id") == task_id:
                task["done"] = not bool(task.get("done"))
                return True

        for task in settings.dated_tasks:
            if task.get("id") == task_id:
                task["done"] = not bool(task.get("done"))
                return True

        return False

    @classmethod
    def delete_task(cls, settings: CheckoutSettings, task_id: str) -> bool:
        """Delete a task by its ID from recurring or dated tasks.

        Returns True if found and deleted.
        """
        for i, task in enumerate(settings.recurring_tasks):
            if task.get("id") == task_id:
                settings.recurring_tasks.pop(i)
                return True

        for i, task in enumerate(settings.dated_tasks):
            if task.get("id") == task_id:
                settings.dated_tasks.pop(i)
                return True

        return False

    @classmethod
    def get_tasks_for_date(
        cls, settings: CheckoutSettings, date_str: str | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Return (recurring_tasks, dated_tasks_for_date)."""
        target_date = date_str or date.today().isoformat()
        dated = [t for t in settings.dated_tasks if t.get("date") == target_date]
        return list(settings.recurring_tasks), dated

