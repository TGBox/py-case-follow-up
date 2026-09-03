import json
from pathlib import Path
from typing import Any
from models.snippet import Snippet


def get_default_snippets() -> list[Snippet]:
    from services.i18n_service import tr

    return [
        Snippet(
            snippet_id="SNIP-01",
            title=tr("snippets.s1_title", "📸 Rückfrage: Screenshots & Uhrzeit anfordern"),
            category=tr("snippet_categories.inquiry", "Rückfrage"),
            content=tr("snippets.s1_content", "Bitte lassen Sie uns Screenshots der Fehlermeldung sowie das genaue Datum und die Uhrzeit des ersten Auftretens zukommen."),
            tags=[t.strip() for t in tr("snippets.s1_tags", "rückfrage, screenshot, fehler").split(",")],
            shortcut="<Control-Alt-1>",
        ),
        Snippet(
            snippet_id="SNIP-02",
            title=tr("snippets.s2_title", "🛠 Ersthilfe: PVS & Support-Dienst neustarten"),
            category=tr("snippet_categories.instructions", "Anleitung"),
            content=tr("snippets.s2_content", "Schritte zur Ersthilfe:\n1. PVS an allen Arbeitsplätzen beenden.\n2. Support-Dienst auf dem Hauptserver neustarten.\n3. PVS erneut öffnen und Funktion testen."),
            tags=[t.strip() for t in tr("snippets.s2_tags", "ersthilfe, neustart, pvs").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-03",
            title=tr("snippets.s3_title", "🔍 DB-Check: SQL Fehler-Log Abfrage"),
            category=tr("snippet_categories.sql_db", "SQL / Datenbank"),
            content=tr("snippets.s3_content", "SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;"),
            tags=[t.strip() for t in tr("snippets.s3_tags", "sql, datenbank, log").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-04",
            title=tr("snippets.s4_title", "✅ Fallabschluss & Dankeschön"),
            category=tr("snippet_categories.standard_reply", "Standardantwort"),
            content=tr("snippets.s4_content", "Vielen Dank für Ihre Rückmeldung. Das Anliegen konnte erfolgreich gelöst werden. Wir schließen diesen Vorgang."),
            tags=[t.strip() for t in tr("snippets.s4_tags", "abschluss, danke, erledigt").split(",")],
            shortcut="<Control-Alt-2>",
        ),
        Snippet(
            snippet_id="SNIP-05",
            title=tr("snippets.s5_title", "🩺 Telematikinfrastruktur: Konnektor & SMC-B Prüfung"),
            category=tr("snippet_categories.telematics", "Telematik (TI)"),
            content=tr("snippets.s5_content", "Schritte zur TI-Entstörung:\n1. Status der SMC-B Karte im Kartenterminal prüfen (grüne LED).\n2. Konnektor über Web-Oberfläche oder Schalter kurz stromlos machen (30 Sek. warten).\n3. PVS-Dienst neu starten und TI-Verbindungstest in der Administration ausführen."),
            tags=[t.strip() for t in tr("snippets.s5_tags", "ti, telematik, konnektor, smc-b").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-06",
            title=tr("snippets.s6_title", "📑 Abrechnung: Zuzahlungs- & ESOL-Korrektur weitergeleitet"),
            category=tr("snippet_categories.billing", "Abrechnung"),
            content=tr("snippets.s6_content", "Sehr geehrte Praxisleitung,\n\ndie angeforderte Korrekturdatei bzw. Nachberechnung für die ESOL-Abrechnung wurde an unsere Entwicklungsabteilung weitergeleitet. Sobald die korrigierten Datensätze vorliegen, stellen wir Ihnen diese zur Verfügung."),
            tags=[t.strip() for t in tr("snippets.s6_tags", "abrechnung, zuzahlung, esol, korrektur").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-07",
            title=tr("snippets.s7_title", "💾 Backup-Anforderung für Fehleranalyse"),
            category=tr("snippet_categories.system", "System"),
            content=tr("snippets.s7_content", "Für die detaillierte Fehleranalyse benötigen wir ein aktuelles Datenbank-Backup (.backup). Bitte legen Sie die Datei im gesicherten Fallordner oder Transferverzeichnis ab."),
            tags=[t.strip() for t in tr("snippets.s7_tags", "backup, datenbank, analyse").split(",")],
        ),
        Snippet(
            snippet_id="SNIP-08",
            title=tr("snippets.s8_title", "🔄 Quartalsupdate Hinweis & Vorbereitung"),
            category=tr("snippet_categories.maintenance", "Wartung"),
            content=tr("snippets.s8_content", "Vor Einspielen des Quartalsupdates bitte sicherstellen:\n1. Vollständige Datensicherung durchführen.\n2. Alle Arbeitsplätze schließen.\n3. Server-Dienste beenden und Update-Installer als Administrator ausführen."),
            tags=[t.strip() for t in tr("snippets.s8_tags", "quartalsupdate, update, wartung").split(",")],
        ),
    ]


DEFAULT_SNIPPETS = get_default_snippets()


class SnippetService:
    """Service for managing text snippets and templates."""

    def __init__(self, workspace_dir: Path | str | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.snippets_dir = self.workspace_dir / "data"
        self.snippets_file = self.snippets_dir / "snippets.json"
        self.snippets: list[Snippet] = []
        self.load_snippets()

    def load_snippets(self) -> list[Snippet]:
        """Loads snippets from snippets.json or seeds defaults if not present."""
        if not self.snippets_file.exists():
            self.snippets = get_default_snippets()
            self.save_snippets()
            return self.snippets

        try:
            with open(self.snippets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.snippets = [Snippet.from_dict(d) for d in data]
                else:
                    self.snippets = get_default_snippets()
        except Exception:
            self.snippets = get_default_snippets()

        return self.snippets

    def save_snippets(self) -> None:
        """Saves current snippets to snippets.json."""
        self.snippets_dir.mkdir(parents=True, exist_ok=True)
        raw_data = [s.to_dict() for s in self.snippets]
        with open(self.snippets_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)

    def get_all_snippets(self) -> list[Snippet]:
        return self.snippets

    def get_categories(self) -> list[str]:
        from services.i18n_service import tr
        cats = sorted({s.category for s in self.snippets if s.category})
        return [tr("snippet_picker.all_categories", "Alle")] + cats

    def search_snippets(self, query: str = "", category: str = "Alle") -> list[Snippet]:
        """Filters snippets by search query and category."""
        from services.i18n_service import tr
        results = self.snippets

        all_cat_labels = {"Alle", "All", "Alla", tr("snippet_picker.all_categories", "Alle")}
        if category and category not in all_cat_labels:
            results = [s for s in results if s.category == category]

        if query and query.strip():
            clean_q = query.strip().lower()
            filtered = []
            for s in results:
                if (
                    clean_q in s.title.lower()
                    or clean_q in s.content.lower()
                    or any(clean_q in t.lower() for t in s.tags)
                ):
                    filtered.append(s)
            results = filtered

        return results

    def add_or_update_snippet(self, snippet: Snippet) -> None:
        """Adds a new snippet or updates an existing one."""
        existing_idx = next((i for i, s in enumerate(self.snippets) if s.snippet_id == snippet.snippet_id), None)
        if existing_idx is not None:
            self.snippets[existing_idx] = snippet
        else:
            if not snippet.snippet_id:
                snippet.snippet_id = f"SNIP-{len(self.snippets)+1:02d}"
            self.snippets.append(snippet)
        self.save_snippets()

    def delete_snippet(self, snippet_id: str) -> None:
        """Deletes a snippet by ID."""
        self.snippets = [s for s in self.snippets if s.snippet_id != snippet_id]
        self.save_snippets()
