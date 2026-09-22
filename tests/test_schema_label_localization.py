"""Schema-Texte folgen der eingestellten Sprache - ohne eigene Aenderungen zu kippen.

Gemeldet: nach einem Sprachwechsel standen im Cockpit-Formular weiter die
deutschen Feldbeschriftungen. Ursache war nicht die Uebersetzung selbst, sondern
der Zeitpunkt: display_name, description und die Feldbeschriftungen entstehen
einmal beim Seeding und werden als fertiger Text in question_schemas.json
eingefroren. Ein spaeterer Sprachwechsel hat sie damit nie erreicht.

Aufgeloest wird jetzt bei der Anzeige. Der gespeicherte Text bleibt stehen und
dient zugleich als Erkennungsmerkmal: entspricht er noch einer der hinterlegten
Sprachvarianten, stammt er unveraendert vom Seeding und darf ersetzt werden.
Passt er zu keiner, hat ihn jemand im Schema-Builder umbenannt - dann gewinnt er.
"""

import pytest
from models.schema import QuestionSchema, SchemaField
from services.i18n_service import get_i18n
from services.schema_i18n import (
    field_label_resolver,
    schema_display_name,
    schema_field_label,
    schema_locale_section,
)


@pytest.fixture
def sprache():
    """Stellt die vorher eingestellte Sprache wieder her."""
    i18n = get_i18n()
    vorher = i18n.current_language
    yield i18n
    i18n.current_language = vorher


def _geseedetes_feld() -> SchemaField:
    return SchemaField(field_id="module_name", label="Betroffenes Modul / Programmbereich (optional)")


def test_schema_id_maps_to_its_locale_section():
    """Die Sektion ist die schema_id ohne Praefix - mit einer Ausnahme."""
    assert schema_locale_section("schema_quick") == "quick"
    assert schema_locale_section("schema_bug_report") == "bug_report"
    # Diese eine Abweichung steht als SCHEMA_LOCALE_SECTIONS in constants.py.
    assert schema_locale_section("schema_zuzahlungsnachforderung") == "zuzahlung"
    assert schema_locale_section("eigenes_schema") == "eigenes_schema"


def test_seeded_labels_follow_the_selected_language(sprache):
    feld = _geseedetes_feld()

    sprache.current_language = "de"
    assert schema_field_label("schema_quick", feld) == "Betroffenes Modul / Programmbereich (optional)"

    sprache.current_language = "en"
    assert schema_field_label("schema_quick", feld) == "Affected Module / Area (optional)"

    sprache.current_language = "sv"
    assert schema_field_label("schema_quick", feld) == "Berörd modul / programområde (valfritt)"


def test_a_label_seeded_in_another_language_is_translated_back(sprache):
    """Das Schema kann in jeder Sprache geseedet worden sein, nicht nur auf Deutsch."""
    schwedisch = SchemaField(field_id="module_name", label="Berörd modul / programområde (valfritt)")
    sprache.current_language = "de"
    assert schema_field_label("schema_quick", schwedisch) == "Betroffenes Modul / Programmbereich (optional)"


def test_a_renamed_label_survives_the_translation(sprache):
    """Der Schema-Builder bearbeitet auch die mitgelieferten Schemata.

    Wuerde stur der Locale-Wert gewinnen, waere jede dort vorgenommene
    Umbenennung beim naechsten Aufbau des Formulars still wieder verschwunden.
    """
    umbenannt = SchemaField(field_id="module_name", label="Welches Modul betrifft es?")
    for lang in ("de", "en", "sv"):
        sprache.current_language = lang
        assert schema_field_label("schema_quick", umbenannt) == "Welches Modul betrifft es?"


def test_a_field_without_locale_entry_keeps_its_stored_label(sprache):
    """Eigene Felder aus dem Schema-Builder haben keine Locale-Eintraege."""
    eigenes = SchemaField(field_id="eigenes_feld", label="Selbstgebautes Feld")
    sprache.current_language = "en"
    assert schema_field_label("schema_quick", eigenes) == "Selbstgebautes Feld"


def test_a_field_without_any_text_falls_back_to_its_id(sprache):
    """Lieber der rohe Schluessel als eine leere Beschriftung."""
    leer = SchemaField(field_id="voellig_unbekannt", label="")
    sprache.current_language = "de"
    assert schema_field_label("eigenes_schema", leer) == "voellig_unbekannt"


def test_display_name_follows_the_selected_language(sprache):
    schema = QuestionSchema(
        schema_id="schema_quick",
        display_name="⚡ Schnellerfassung / Allgemeiner Vorgang",
    )
    sprache.current_language = "en"
    assert schema_display_name(schema) != schema.display_name
    sprache.current_language = "de"
    assert schema_display_name(schema) == "⚡ Schnellerfassung / Allgemeiner Vorgang"


def test_report_resolver_prefers_the_schema_field_over_the_bare_locale_entry(sprache):
    """Der Bericht muss dieselbe Beschriftung zeigen wie das Formular daneben."""
    umbenannt = SchemaField(field_id="module_name", label="Welches Modul betrifft es?")
    schemas = [QuestionSchema(schema_id="schema_quick", fields=[umbenannt])]

    sprache.current_language = "en"
    assert field_label_resolver("schema_quick", schemas)("module_name") == "Welches Modul betrifft es?"
    # Ohne Schema bleibt nur der Locale-Eintrag.
    assert field_label_resolver("schema_quick", None)("module_name") == "Affected Module / Area (optional)"


def test_the_stored_label_stays_untouched(sprache):
    """Uebersetzt wird nur die Anzeige - question_schemas.json bleibt, wie es ist."""
    feld = _geseedetes_feld()
    original = feld.label
    sprache.current_language = "sv"
    schema_field_label("schema_quick", feld)
    assert feld.label == original
