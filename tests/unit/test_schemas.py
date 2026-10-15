"""Question schemas: model round-trip, date-field migration, SchemaService editing/validation and display localization."""

import pytest

from enums import FieldType
from models.schema import QuestionSchema, SchemaField, looks_like_date_field
from services.i18n_service import get_i18n
from services.schema_i18n import (
    field_label_resolver,
    schema_display_name,
    schema_field_label,
    schema_locale_section,
)
from services.schema_service import SchemaService
from services.seed_service import SeedService

SEEDED_LABEL_DE = "Betroffenes Modul / Programmbereich (optional)"
SEEDED_LABEL_EN = "Affected Module / Area (optional)"
SEEDED_LABEL_SV = "Berörd modul / programområde (valfritt)"
RENAMED_LABEL = "Welches Modul betrifft es?"


@pytest.fixture
def sprache():
    """The i18n service; conftest resets the language after each test."""
    return get_i18n()


# --- Model ------------------------------------------------------------------

def test_schema_round_trip_keeps_fields():
    f1 = SchemaField(field_id="patient_age", label="Patientenalter", field_type=FieldType.NUMBER,
                     required=True, options=["0-18", "19-65", "65+"], placeholder="Alter", order=1)
    f2 = SchemaField(field_id="f2", label="Feld 2", field_type=FieldType.BOOLEAN, order=2)
    schema = QuestionSchema(schema_id="schema_custom_01", display_name="Formular",
                            description="Ein Test-Schema", fields=[f1, f2])

    restored = QuestionSchema.from_dict(schema.to_dict())
    assert restored.schema_id == "schema_custom_01"
    assert restored.display_name == "Formular"
    assert [f.field_id for f in restored.fields] == ["patient_age", "f2"]
    age = restored.fields[0]
    assert (age.field_type, age.required, age.options, age.order) == (FieldType.NUMBER, True, ["0-18", "19-65", "65+"], 1)


@pytest.mark.parametrize("field_id,label,expected", [
    ("invoice_date", "Rechnungsdatum", True),
    ("prescription_date", "Datum der Verordnung", True),
    ("faelligkeit", "Bearbeitungsfrist", True),
    ("date", "Date", True),
    ("start_date", "Start", True),
    ("esol_filename", "Name der originalen ESOL-Datei", False),  # Regression: "Datei" contains "date"
    ("datei_upload", "Datei hochladen", False),
    ("update_info", "Update-Informationen", False),
    ("invoice_number", "Betroffene Rechnungsnummer", False),
    ("patient_names", "Namen der betroffenen Patienten", False),
])
def test_looks_like_date_field(field_id, label, expected):
    assert looks_like_date_field(field_id, label) is expected


@pytest.mark.parametrize("field_id,label,stored_type,expected", [
    ("invoice_date", "Rechnungsdatum", "text", FieldType.DATE),  # legacy text date gets migrated
    ("esol_filename", "Name der originalen ESOL-Datei", "text", FieldType.TEXT),
    *[("datum_bekannt", "Datum bekannt?", t, t)  # explicit non-text types are never overridden
      for t in (FieldType.DROPDOWN, FieldType.BOOLEAN, FieldType.FILE, FieldType.NUMBER)],
])
def test_from_dict_date_migration(field_id, label, stored_type, expected):
    restored = SchemaField.from_dict({"field_id": field_id, "label": label, "field_type": stored_type, "order": 1})
    assert restored.field_type == expected


def test_seed_schemas_include_defaults_with_typed_date_fields(storage):
    """Real date fields must be typed DATE explicitly - only then do they get the calendar button."""
    schemas = {s.schema_id: s for s in SeedService(storage).create_seed_schemas()}
    assert {"schema_zuzahlungsnachforderung", "schema_feature_request", "schema_bug_report"} <= schemas.keys()

    by_id = {f.field_id: f for f in schemas["schema_zuzahlungsnachforderung"].fields}
    assert by_id["invoice_date"].field_type == FieldType.DATE
    assert by_id["prescription_date"].field_type == FieldType.DATE
    assert by_id["esol_filename"].field_type == FieldType.TEXT


# --- SchemaService ----------------------------------------------------------

def test_schema_service_add_move_toggle_remove():
    s = QuestionSchema(schema_id="s1", display_name="Test", fields=[])
    for i, fid in enumerate(("f1", "f2", "f3"), start=1):
        SchemaService.add_field(s, SchemaField(field_id=fid, label=fid, order=i))
    ids = lambda: [f.field_id for f in s.fields]  # noqa: E731

    SchemaService.move_field(s, "f2", "up")
    assert ids() == ["f2", "f1", "f3"]
    SchemaService.move_field(s, "f2", "down")
    assert ids() == ["f1", "f2", "f3"]

    SchemaService.toggle_required(s, "f1")
    assert s.fields[0].required

    SchemaService.remove_field(s, "f2")
    assert ids() == ["f1", "f3"]


def test_schema_service_validate_form_data_reports_missing_required():
    s = QuestionSchema(schema_id="s1", display_name="Test", fields=[
        SchemaField(field_id="f1", label="Name", required=True),
        SchemaField(field_id="f2", label="Alter", required=True),
        SchemaField(field_id="f3", label="Notiz", required=False),
    ])
    assert SchemaService.validate_form_data(s, {"f1": "Max", "f3": "x"}) == (False, ["f2"])
    assert SchemaService.validate_form_data(s, {"f1": "Max", "f2": "42"}) == (True, [])


# --- Display localization ---------------------------------------------------
# Seeded texts are frozen into question_schemas.json; they are translated at
# display time. A stored label that still matches one of the locale variants is
# untouched seed text and gets replaced; anything else was renamed in the
# schema builder and wins.

def test_schema_id_maps_to_its_locale_section():
    assert schema_locale_section("schema_quick") == "quick"
    assert schema_locale_section("schema_bug_report") == "bug_report"
    assert schema_locale_section("schema_zuzahlungsnachforderung") == "zuzahlung"  # the one exception
    assert schema_locale_section("eigenes_schema") == "eigenes_schema"


@pytest.mark.parametrize("stored", [SEEDED_LABEL_DE, SEEDED_LABEL_SV])
def test_seeded_label_follows_language_whatever_language_it_was_seeded_in(sprache, stored):
    feld = SchemaField(field_id="module_name", label=stored)
    for lang, expected in (("de", SEEDED_LABEL_DE), ("en", SEEDED_LABEL_EN), ("sv", SEEDED_LABEL_SV)):
        sprache.current_language = lang
        assert sprache.current_language == lang
        assert schema_field_label("schema_quick", feld) == expected
    assert feld.label == stored  # only the display is translated, never the stored text


@pytest.mark.parametrize("schema_id,field,expected", [
    # Renamed in the schema builder: the user's text must survive every language.
    ("schema_quick", SchemaField(field_id="module_name", label=RENAMED_LABEL), RENAMED_LABEL),
    # Own fields have no locale entry.
    ("schema_quick", SchemaField(field_id="eigenes_feld", label="Selbstgebautes Feld"), "Selbstgebautes Feld"),
    # Rather the raw key than an empty label.
    ("eigenes_schema", SchemaField(field_id="voellig_unbekannt", label=""), "voellig_unbekannt"),
])
def test_non_seeded_labels_are_kept(sprache, schema_id, field, expected):
    for lang in ("de", "en", "sv"):
        sprache.current_language = lang
        assert schema_field_label(schema_id, field) == expected


def test_display_name_follows_the_selected_language(sprache):
    schema = QuestionSchema(schema_id="schema_quick", display_name="⚡ Schnellerfassung / Allgemeiner Vorgang")
    sprache.current_language = "en"
    assert schema_display_name(schema) != schema.display_name
    sprache.current_language = "de"
    assert schema_display_name(schema) == schema.display_name


def test_report_resolver_prefers_the_schema_field_over_the_bare_locale_entry(sprache):
    """The report must show the same label as the form next to it."""
    schemas = [QuestionSchema(schema_id="schema_quick", fields=[SchemaField(field_id="module_name", label=RENAMED_LABEL)])]
    sprache.current_language = "en"
    assert field_label_resolver("schema_quick", schemas)("module_name") == RENAMED_LABEL
    assert field_label_resolver("schema_quick", None)("module_name") == SEEDED_LABEL_EN
