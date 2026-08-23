import json
import logging
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any
from config import AppConfig
from enums import SyncMode
from models.profile import WikiSettings
from utils.security import resolve_secret, normalize_url

logger = logging.getLogger("SupportCockpit")


class WikiSyncService:
    def __init__(self, config: AppConfig, wiki_settings: WikiSettings | None = None):
        self.config = config
        self.settings = wiki_settings or WikiSettings()
        self.db_path = self.config.wiki_db_path
        self.init_db()

    def init_db(self) -> None:
        """Initializes SQLite database and FTS5 virtual table."""
        self.config.ensure_directories()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wiki_pages (
                page_id INTEGER PRIMARY KEY,
                book_id INTEGER,
                title TEXT,
                slug TEXT,
                url TEXT,
                updated_at TEXT,
                content_markdown TEXT
            )
        """)

        # FTS5 virtual table
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
                    page_id UNINDEXED,
                    title,
                    content
                )
            """)
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 not supported in this SQLite build, using standard table fallback: {e}")

        conn.commit()
        conn.close()

    def is_fts5_available(self) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT count(*) FROM wiki_fts")
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    def sync_from_bookstack(self, mock_client: Any | None = None) -> tuple[bool, str]:
        """Synchronizes articles from BookStack REST API according to configured sync mode.
        Accepts optional mock_client for unit testing.
        """
        api_url = normalize_url(self.settings.api_url)
        if not api_url and not mock_client:
            return False, "Wiki API URL is not configured."

        token_id = resolve_secret(self.settings.token_id)
        token_secret = resolve_secret(self.settings.token_secret)

        if not token_id or not token_secret:
            if not mock_client:
                return False, "BookStack API tokens are missing in environment variables."

        headers = {
            "Authorization": f"Token {token_id}:{token_secret}",
            "User-Agent": "SupportCockpit/1.0",
        }

        try:
            pages_data = []
            if mock_client:
                pages_data = mock_client.get_pages()
            else:
                endpoint = f"{api_url}/api/pages"
                req = urllib.request.Request(endpoint, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    pages_data = res_json.get("data", [])

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for item in pages_data:
                page_id = item.get("id")
                book_id = item.get("book_id", 0)
                title = item.get("name", item.get("title", ""))
                slug = item.get("slug", "")
                url = item.get("url", f"{api_url}/pages/{slug}")
                updated_at = item.get("updated_at", "")
                content = ""

                if self.settings.sync_mode == SyncMode.FULL_OFFLINE:
                    if mock_client:
                        content = mock_client.get_page_content(page_id)
                    else:
                        page_endpoint = f"{api_url}/api/pages/{page_id}"
                        p_req = urllib.request.Request(page_endpoint, headers=headers)
                        with urllib.request.urlopen(p_req, timeout=10) as p_res:
                            p_json = json.loads(p_res.read().decode("utf-8"))
                            content = p_json.get("markdown", p_json.get("html", ""))

                cursor.execute("""
                    INSERT OR REPLACE INTO wiki_pages (page_id, book_id, title, slug, url, updated_at, content_markdown)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (page_id, book_id, title, slug, url, updated_at, content))

                if self.is_fts5_available():
                    cursor.execute("DELETE FROM wiki_fts WHERE page_id = ?", (page_id,))
                    cursor.execute("""
                        INSERT INTO wiki_fts (page_id, title, content)
                        VALUES (?, ?, ?)
                    """, (page_id, title, content or title))

            conn.commit()
            conn.close()
            return True, f"Successfully synced {len(pages_data)} pages."

        except Exception as e:
            logger.error(f"Wiki sync failed safely: {e}")
            return False, f"Wiki Sync Error: {e}"

    def search(self, query: str) -> list[dict[str, Any]]:
        """Searches offline SQLite wiki database.
        Returns list of matching page results.
        """
        if not query or not query.strip():
            return []

        cleaned_query = query.strip()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        results = []

        if self.is_fts5_available():
            try:
                # FTS5 Match query
                fts_pattern = f'"{cleaned_query}"*'
                cursor.execute("""
                    SELECT p.page_id, p.title, p.url, snippet(wiki_fts, 2, '<b>', '</b>', '...', 10)
                    FROM wiki_fts f
                    JOIN wiki_pages p ON f.page_id = p.page_id
                    WHERE wiki_fts MATCH ?
                    LIMIT 20
                """, (fts_pattern,))
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "page_id": row[0],
                        "title": row[1],
                        "url": row[2],
                        "snippet": row[3] or row[1],
                    })
                conn.close()
                return results
            except Exception as fts_err:
                logger.warning(f"FTS search failed, falling back to LIKE: {fts_err}")

        # Fallback LIKE search
        like_pattern = f"%{cleaned_query}%"
        cursor.execute("""
            SELECT page_id, title, url, content_markdown
            FROM wiki_pages
            WHERE title LIKE ? OR content_markdown LIKE ?
            LIMIT 20
        """, (like_pattern, like_pattern))
        rows = cursor.fetchall()
        for row in rows:
            content_snippet = (row[3] or row[1])[:100]
            results.append({
                "page_id": row[0],
                "title": row[1],
                "url": row[2],
                "snippet": content_snippet,
            })

        conn.close()
        return results
