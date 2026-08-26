import os
import json
from pathlib import Path
from typing import Any
from models.case import Case

TEXT_FILE_EXTENSIONS = {".txt", ".log", ".json", ".csv", ".xml", ".sql", ".backup", ".md", ".ini", ".cfg", ".yaml", ".yml"}


class DeepSearchService:
    """Service for deep full-text searching across case attachment files and offline Wiki articles."""

    def __init__(self, workspace_dir: Path | str | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self._file_lines_cache: dict[str, tuple[float, list[str]]] = {}
        self._wiki_cache_data: tuple[float, list[dict]] | None = None

    def _get_file_lines(self, file_path: Path) -> list[str]:
        path_str = str(file_path)
        try:
            mtime = file_path.stat().st_mtime
            if path_str in self._file_lines_cache:
                cached_mtime, lines = self._file_lines_cache[path_str]
                if cached_mtime == mtime:
                    return lines
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            self._file_lines_cache[path_str] = (mtime, lines)
            return lines
        except Exception:
            return []

    def search_case_attachments(self, case: Case, query: str, max_matches_per_file: int = 3) -> list[dict[str, Any]]:
        """Searches text files inside a case's attachment directory for the query string."""
        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        matches = []

        # Resolve directory path
        if case.attachment_directory:
            dir_path = Path(case.attachment_directory)
            if not dir_path.is_absolute():
                dir_path = self.workspace_dir / case.attachment_directory
        else:
            dir_path = self.workspace_dir / "data" / "attachments" / case.case_id

        if not dir_path.exists() or not dir_path.is_dir():
            return []

        try:
            for file_path in dir_path.iterdir():
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() not in TEXT_FILE_EXTENSIONS and file_path.name != "data-al.backup":
                    continue

                lines = self._get_file_lines(file_path)
                file_matches = 0
                for line_idx, line in enumerate(lines, start=1):
                    if clean_query in line.lower():
                        matches.append({
                            "file_name": file_path.name,
                            "file_path": str(file_path),
                            "line_number": line_idx,
                            "snippet": line.strip()[:120],
                        })
                        file_matches += 1
                        if file_matches >= max_matches_per_file:
                            break
        except Exception:
            pass

        return matches

    def _get_wiki_articles(self, cache_path: Path) -> list[dict]:
        try:
            mtime = cache_path.stat().st_mtime
            if self._wiki_cache_data:
                cached_mtime, articles = self._wiki_cache_data
                if cached_mtime == mtime:
                    return articles
            with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
                articles = json.load(f)
            if isinstance(articles, list):
                self._wiki_cache_data = (mtime, articles)
                return articles
        except Exception:
            pass
        return []

    def search_wiki_cache(self, query: str, wiki_cache_file: Path | str | None = None) -> list[dict[str, Any]]:
        """Searches offline Wiki cache articles for the query string."""
        if not query or not query.strip():
            return []

        clean_query = query.strip().lower()
        matches = []

        cache_path = Path(wiki_cache_file) if wiki_cache_file else self.workspace_dir / "src" / "data" / "wiki_cache.json"
        if not cache_path.exists():
            cache_path = self.workspace_dir / "data" / "wiki_cache.json"

        if not cache_path.exists():
            return []

        articles = self._get_wiki_articles(cache_path)
        for art in articles:
            title = str(art.get("title", ""))
            content = str(art.get("content", ""))
            tags = " ".join(art.get("tags", []))

            if clean_query in title.lower() or clean_query in content.lower() or clean_query in tags.lower():
                snippet = title
                if clean_query in content.lower():
                    idx = content.lower().find(clean_query)
                    start = max(0, idx - 30)
                    end = min(len(content), idx + 80)
                    snippet = f"...{content[start:end]}..."

                matches.append({
                    "article_id": art.get("article_id", ""),
                    "title": title,
                    "snippet": snippet,
                })

        return matches

    def perform_deep_search(self, cases: list[Case], query: str) -> dict[str, dict[str, Any]]:
        """Performs deep search across all cases and returns a mapping of case_id -> search results."""
        results: dict[str, dict[str, Any]] = {}
        if not query or len(query.strip()) < 2:
            return results

        clean_query = query.strip()
        wiki_matches = self.search_wiki_cache(clean_query)

        for case in cases:
            att_matches = self.search_case_attachments(case, clean_query)
            
            # Check if wiki matches relate to case module or tags
            related_wiki = []
            if wiki_matches:
                module_name = str(case.form_data.get("module_name", "")).lower()
                case_tags = [t.lower() for t in case.classification.tags]
                for w in wiki_matches:
                    w_title = w["title"].lower()
                    if module_name and module_name in w_title:
                        related_wiki.append(w)
                    elif any(t in w_title for t in case_tags if len(t) > 2):
                        related_wiki.append(w)

            if att_matches or related_wiki:
                results[case.case_id] = {
                    "attachment_matches": att_matches,
                    "wiki_matches": related_wiki or (wiki_matches[:1] if att_matches else []),
                }

        return results
