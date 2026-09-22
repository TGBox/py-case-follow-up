"""Uebersetzt die Texte eines Frageschemas erst bei der Anzeige.

Beschriftungen, Anzeigenamen und Beschreibungen entstehen einmal beim Seeding
und werden mit dem Text in question_schemas.json eingefroren - in der Sprache,
die zu diesem Zeitpunkt aktiv war. Ein spaeterer Sprachwechsel hat sie deshalb
nie erreicht: im Formular stand weiter Deutsch, im Bericht sogar der rohe
Feldschluessel.

Aufgeloest wird daher hier, bei jedem Aufbau der Oberflaeche. Der gespeicherte
Text bleibt dabei unangetastet. Er hat zwei Aufgaben: Rueckfallebene fuer alles,
wofuer es keinen Locale-Eintrag gibt - eigene Schemata aus dem Schema-Builder
zum Beispiel -, und Erkennungsmerkmal dafuer, ob jemand den Text selbst
geaendert hat.

Genau daran haengt die Regel in translate_schema_text(): ersetzt wird nur, was
noch einer der hinterlegten Sprachvarianten entspricht und damit unveraendert
vom Seeding stammt. Passt der gespeicherte Text zu keiner davon, hat ihn jemand
im Schema-Builder angefasst, und dann gewinnt er - sonst waere jede eigene
Umbenennung still wieder verschwunden.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from constants import SCHEMA_ID_PREFIX, SCHEMA_LOCALE_SECTIONS
from models.schema import QuestionSchema, SchemaField
from services.i18n_service import tr, tr_all

_MISSING = object()


def schema_locale_section(schema_id: str) -> str:
    """Locale-Sektion zu einer schema_id ('schema_quick' -> 'quick')."""
    if not schema_id:
        return ""
    known = SCHEMA_LOCALE_SECTIONS.get(schema_id)
    if known:
        return known
    return schema_id[len(SCHEMA_ID_PREFIX):] if schema_id.startswith(SCHEMA_ID_PREFIX) else schema_id


def _candidate_keys(schema_id: str, suffix: str) -> list[str]:
    """Locale-Keys, unter denen ein Schema-Text stehen kann.

    Neben der regulaeren Sektion wird die schema_id selbst probiert, damit ein
    eigenes Schema, dessen Id direkt einer Sektion entspricht, ebenfalls greift.
    """
    sections = []
    for section in (schema_locale_section(schema_id), schema_id):
        if section and section not in sections:
            sections.append(section)
    return [f"schemas.{section}.{suffix}" for section in sections]


def translate_schema_text(keys: Sequence[str], stored: str) -> str:
    """Liefert den Text in der aktuellen Sprache, ohne eigene Aenderungen zu kippen."""
    stored = stored or ""
    for key in keys:
        current = tr(key, default=_MISSING)
        if current is _MISSING or not isinstance(current, str) or not current.strip():
            continue
        if not stored.strip():
            return current
        # Nur ersetzen, solange der gespeicherte Text noch der geseedete ist.
        if stored in tr_all(key):
            return current
        return stored
    return stored


def schema_field_label(schema_id: str, field: SchemaField) -> str:
    """Beschriftung eines Feldes fuer die Anzeige.

    Wichtig: nur fuer den sichtbaren Text verwenden. Die Renderer entscheiden
    anhand von field.label (deutsche Stichworte wie 'programm' oder 'browser'),
    welches Eingabeelement ein Feld bekommt - waere dort der uebersetzte Text,
    bekaeme dasselbe Feld in einer anderen Sprache ein anderes Element.
    """
    return translate_schema_text(_candidate_keys(schema_id, field.field_id), field.label) or field.field_id


def schema_display_name(schema: QuestionSchema) -> str:
    return translate_schema_text(_candidate_keys(schema.schema_id, "display_name"), schema.display_name)


def schema_description(schema: QuestionSchema) -> str:
    return translate_schema_text(_candidate_keys(schema.schema_id, "description"), schema.description)


def schema_repeatable_title(schema: QuestionSchema) -> str:
    return translate_schema_text(_candidate_keys(schema.schema_id, "repeatable_title"), schema.repeatable_group_title)


def field_label_resolver(
    schema_id: str,
    schemas: Sequence[QuestionSchema] | None = None,
) -> Callable[[str], str]:
    """Liefert eine Funktion field_id -> Beschriftung.

    Fuer den Bericht, der nur die Schluessel aus case.form_data kennt und ohne
    das nackte 'module_name' oder 'unformatted_description' anzeigen wuerde.
    """
    fields: dict[str, SchemaField] = {}
    for schema in schemas or []:
        if schema.schema_id == schema_id:
            fields = {f.field_id: f for f in schema.fields}
            break

    def resolve(field_id: str) -> str:
        field = fields.get(field_id)
        if field is not None:
            return schema_field_label(schema_id, field)
        for key in _candidate_keys(schema_id, field_id):
            translated = tr(key, default=_MISSING)
            if translated is not _MISSING and isinstance(translated, str) and translated.strip():
                return translated
        return field_id

    return resolve
