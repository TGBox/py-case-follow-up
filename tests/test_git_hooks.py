"""Tests for Git hooks configuration and pre-push hook integrity.

Der Hook ist nur so viel wert, wie er von der CI abdeckt. Genau da lag der
Fehler: der Hook baute die Exe, prüfte Typen und fuhr die Tests - den
ruff-Job aus .github/workflows/tests.yml kannte er aber nicht. Ein E731 kam
damit sauber durch den Push und fiel erst in den GitHub Actions auf.

test_pre_push_covers_every_static_check_from_ci hält die beiden deshalb
aneinander: kommt in der Workflow-Datei eine Prüfung dazu, ohne dass der Hook
sie kennt, schlägt dieser Test fehl statt der nächsten CI-Runde.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = PROJECT_ROOT / ".githooks" / "pre-push"
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "tests.yml"

# Prüfungen, die der Hook wortgleich zur CI fahren muss. pytest und pyinstaller
# stehen bewusst nicht hier: lokal laufen sie mit --no-cov bzw. --noconfirm,
# die Befehle sind also absichtlich nicht identisch.
EXACT_CI_CHECKS = ("uv run ruff check", "uvx pyright")


def _hook_text() -> str:
    return HOOK_PATH.read_text(encoding="utf-8")


def test_pre_push_hook_exists_and_configured():
    """Verify that .githooks/pre-push exists, is non-empty, and contains exe build and pytest commands."""
    assert HOOK_PATH.exists(), ".githooks/pre-push must exist in repository"
    content = _hook_text()

    # Verify building the exe via spec file
    assert "pyinstaller" in content.lower()
    assert "py-case-follow-up.spec" in content

    # Verify static typecheck via pyright
    assert "pyright" in content

    # Verify linting via ruff
    assert "ruff check" in content

    # Verify running tests
    assert "pytest" in content


def test_pre_push_runs_the_cheap_checks_before_the_expensive_ones():
    """Lint und Typecheck brauchen Sekunden, der Build Minuten.

    Der Build muss trotzdem vor pytest bleiben: dist/ ist gitignored, und
    test_pyinstaller_bundle.py überspringt sich selbst ohne gebaute .exe.
    """
    content = _hook_text()
    lint_idx = content.find("uv run ruff check")
    typecheck_idx = content.find("uvx pyright")
    build_idx = content.find("uv run pyinstaller")
    test_idx = content.find("uv run pytest")

    assert min(lint_idx, typecheck_idx, build_idx, test_idx) != -1, "Ein Schritt fehlt im Hook"
    assert lint_idx < typecheck_idx < build_idx < test_idx, (
        "Reihenfolge muss Lint -> Typecheck -> Build -> Tests sein"
    )


def test_pre_push_covers_every_static_check_from_ci():
    """Der Hook darf nicht hinter der CI zurückfallen.

    Prüft jede 'run:'-Zeile der Workflow-Datei, die eine der in EXACT_CI_CHECKS
    genannten Prüfungen startet, und verlangt sie wortgleich im Hook - samt
    Pfadargumenten, damit nicht der halbe Baum ungeprüft bleibt.
    """
    assert WORKFLOW_PATH.exists(), ".github/workflows/tests.yml must exist"
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    hook = _hook_text()

    ci_commands = [
        m.group(1).strip()
        for m in re.finditer(r"^\s*run:\s*(.+)$", workflow, re.MULTILINE)
    ]
    relevant = [c for c in ci_commands if any(c.startswith(p) for p in EXACT_CI_CHECKS)]

    assert relevant, "Keine der erwarteten CI-Prüfungen in tests.yml gefunden"
    fehlend = [c for c in relevant if c not in hook]
    assert not fehlend, (
        "Diese CI-Prüfungen fehlen im pre-push-Hook (oder laufen dort mit anderem "
        f"Umfang): {fehlend}"
    )
