"""Anti-regression test suite ensuring the complete absence of invisible Unicode

control characters and variation selectors across the entire codebase.
"""

from pathlib import Path


def test_unicode_no_variation_selectors_in_src():
    """Anti-regression test: Ensure no \\ufe0f or \\ufe0e variation selectors exist anywhere in src/*.py."""
    forbidden_chars = {
        "\ufe0f": "VARIATION SELECTOR-16 (\\ufe0f)",
        "\ufe0e": "VARIATION SELECTOR-15 (\\ufe0e)",
        "\u200b": "ZERO WIDTH SPACE (\\u200b)",
        "\ufeff": "ZERO WIDTH NO-BREAK SPACE (\\ufeff)",
    }

    violations = []
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for char, char_name in forbidden_chars.items():
            if char in content:
                violations.append(f"{py_file} contains {char_name}")

    assert not violations, f"Found forbidden Unicode control characters in codebase:\n" + "\n".join(violations)
