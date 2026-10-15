"""Model dataclasses: validation, dict round-trips, legacy data and the shipped data_examples/ files."""

import json
from pathlib import Path

import pytest

from enums import Actor, TargetType
from models.case import Case, TimelineEntry
from models.customer import Customer
from models.export_template import ExportTemplate
from models.profile import Colleague, ShortcutSettings, UserProfile
from models.schema import QuestionSchema
from models.snippet import Snippet

DATA_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "data_examples"


def _load_example(name: str):
    return json.loads((DATA_EXAMPLES_DIR / name).read_text(encoding="utf-8"))


# --- data_examples/ ---------------------------------------------------------

@pytest.mark.parametrize("filename,model,expected_fields", [
    ("customers.json", Customer, {
        "customer_id", "practice_name", "is_vip", "system_version", "website",
        "vm_number", "instance_number", "general_notes", "contacts",
    }),
    ("colleagues.json", Colleague, {
        "username", "name", "department", "extension", "email", "mobile",
        "notes", "cases_path", "is_absent", "absence_reason",
    }),
])
def test_example_records_are_complete_and_valid(filename, model, expected_fields):
    data = _load_example(filename)
    assert isinstance(data, list) and data
    for item in data:
        assert expected_fields <= item.keys(), f"{filename}: missing {expected_fields - item.keys()}"
        assert model.from_dict(item).validate() == []


@pytest.mark.parametrize("filename", ["cases.json", "archive.json"])
def test_example_cases_are_valid(filename):
    data = _load_example(filename)
    assert data
    for item in data:
        assert Case.from_dict(item).validate() == []
        assert "tags" in item.get("classification", {})
        wf = item.get("workflow_status", {})
        assert "followup_at" in wf and "followup_note" in wf


def test_example_profile_templates_and_schemas_load():
    profile = UserProfile.from_dict(_load_example("app_profile.json"))
    assert profile.user.name and profile.user.department
    assert [ExportTemplate.from_dict(t) for t in _load_example("export_templates.json").get("templates", [])]
    assert [QuestionSchema.from_dict(s) for s in _load_example("question_schemas.json").get("schemas", [])]


# --- ExportTemplate ---------------------------------------------------------

def test_export_template_validation():
    assert sorted(ExportTemplate().validate()) == sorted([
        "Template ID is required.", "Display name is required.", "Template string cannot be empty.",
    ])
    # Whitespace-only counts as missing.
    assert len(ExportTemplate(template_id="  ", display_name="\t", template_string="\n").validate()) == 3
    assert ExportTemplate(template_id="t", display_name="Jira", template_string="h1. {case_id}").validate() == []


def test_export_template_round_trip_and_empty_dict_defaults():
    orig = ExportTemplate(
        template_id="tmpl_custom",
        display_name="Custom Markdown",
        target_type=TargetType.FILE_EXPORT,
        applicable_cases=["schema_hotline", "schema_technik"],
        description="Markdown export for external partners",
        required_schema_fields=["kundennr", "kontakt"],
        template_string="# Fall {{ case.case_id }}",
    )
    assert ExportTemplate.from_dict(orig.to_dict()) == orig
    assert ExportTemplate.from_dict({}) == ExportTemplate()
    assert ExportTemplate().target_type == TargetType.CLIPBOARD_TEXT


# --- Profile: colleagues and shortcuts --------------------------------------

def test_colleague_absence_survives_round_trip():
    col = Colleague(username="mmueller", name="Max Müller", department="Support",
                    is_absent=True, absence_reason="Urlaub bis 30.08.")
    loaded = Colleague.from_dict(col.to_dict())
    assert loaded.is_absent is True
    assert loaded.absence_reason == "Urlaub bis 30.08."


def test_shortcut_settings_defaults_round_trip_and_legacy_data():
    s = ShortcutSettings()
    assert (s.new_case, s.save_case, s.archive_case, s.toggle_theme) == (
        "<Control-n>", "<Control-s>", "<Control-Shift-A>", "<Control-t>")
    assert ShortcutSettings.from_dict(s.to_dict()) == s

    # Old profiles only stored three keys: the rest falls back to defaults.
    legacy = ShortcutSettings.from_dict({
        "new_case": "<Control-n>", "export_dialog": "<Control-e>", "wiki_search": "<Control-w>",
    })
    assert legacy.save_case == "<Control-s>"
    assert legacy.archive_case == "<Control-Shift-A>"


# --- Snippet ----------------------------------------------------------------

def test_snippet_validation_and_shortcut_round_trip():
    assert Snippet(snippet_id="S-01", title="Test", content="Text").validate() == []
    assert len(Snippet().validate()) == 3

    snip = Snippet(snippet_id="SNIP-10", title="Macro", category="Test", content="Hi", shortcut="<Control-Alt-9>")
    assert Snippet.from_dict(snip.to_dict()) == snip


# --- Case handover ----------------------------------------------------------

def test_case_handover_changes_actor_and_logs_timeline():
    c = Case(case_id="T-2026-999")
    assert c.workflow_status.current_actor == Actor.SUPPORT

    c.workflow_status.current_actor = Actor.DEVELOPMENT
    c.timeline.append(TimelineEntry(
        timestamp="2026-08-23T10:00:00",
        author="Daniel Rösch",
        note="Fall an Hr. Becker übergeben (Kanal: GitLab Issue).",
        status_change="ZUSTÄNDIGKEIT: Support -> Entwicklung",
    ))

    restored = Case.from_dict(c.to_dict())
    assert restored.workflow_status.current_actor == Actor.DEVELOPMENT
    assert restored.timeline[-1].status_change == "ZUSTÄNDIGKEIT: Support -> Entwicklung"
    assert "Hr. Becker" in restored.timeline[-1].note
