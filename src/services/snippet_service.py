import json
from pathlib import Path
from typing import Any
from models.snippet import Snippet

DEFAULT_SNIPPETS = [
    Snippet(
        snippet_id="SNIP-01",
        title="📸 Rückfrage: Screenshots & Uhrzeit anfordern",
        category="Rückfrage",
        content="Bitte lassen Sie uns Screenshots der Fehlermeldung sowie das genaue Datum und die Uhrzeit des ersten Auftretens zukommen.",
        tags=["rückfrage", "screenshot", "fehler"],
    ),
    Snippet(
        snippet_id="SNIP-02",
        title="🛠 Ersthilfe: PVS & Support-Dienst neustarten",
        category="Anleitung",
        content="Schritte zur Ersthilfe:\n1. PVS an allen Arbeitsplätzen beenden.\n2. Support-Dienst auf dem Hauptserver neustarten.\n3. PVS erneut öffnen und Funktion testen.",
        tags=["ersthilfe", "neustart", "pvs"],
    ),
    Snippet(
        snippet_id="SNIP-03",
        title="🔍 DB-Check: SQL Fehler-Log Abfrage",
        category="SQL / Datenbank",
        content="SELECT TOP 20 * FROM dbo.SystemLog WHERE ErrorCode LIKE '%AL-%' ORDER BY LogTimestamp DESC;",
        tags=["sql", "datenbank", "log"],
    ),
    Snippet(
        snippet_id="SNIP-04",
        title="✅ Fallabschluss & Dankeschön",
        category="Standardantwort",
        content="Vielen Dank für Ihre Rückmeldung. Das Anliegen konnte erfolgreich gelöst werden. Wir schließen diesen Vorgang.",
        tags=["abschluss", "danke", "erledigt"],
    ),
]


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
            self.snippets = list(DEFAULT_SNIPPETS)
            self.save_snippets()
            return self.snippets

        try:
            with open(self.snippets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.snippets = [Snippet.from_dict(d) for d in data]
                else:
                    self.snippets = list(DEFAULT_SNIPPETS)
        except Exception:
            self.snippets = list(DEFAULT_SNIPPETS)

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
        cats = sorted({s.category for s in self.snippets if s.category})
        return ["Alle"] + cats

    def search_snippets(self, query: str = "", category: str = "Alle") -> list[Snippet]:
        """Filters snippets by search query and category."""
        results = self.snippets

        if category and category != "Alle":
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
