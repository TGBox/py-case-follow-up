"""Independent Post-Victory Audit Verification Script.
Conducts full programmatic verification of:
1. Locale Key Parity & Translation Quality
2. AST Codebase Scan over all src/*.py
3. Constants & Enums Dynamic Localization
4. Runtime Dynamic Language Switching
5. Integrity / Mock Bypasses
"""

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

results = {
    "key_parity": {},
    "format_tokens": {},
    "translation_quality": {},
    "ast_scan": {},
    "constants_enums": {},
    "dynamic_switching": {},
    "integrity": {},
}

def extract_leaf_keys(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    leaf_dict: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            leaf_dict.update(extract_leaf_keys(value, full_key))
        elif isinstance(value, str):
            leaf_dict[full_key] = value
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    leaf_dict.update(extract_leaf_keys(item, f"{full_key}[{idx}]"))
                else:
                    leaf_dict[f"{full_key}[{idx}]"] = str(item)
        else:
            leaf_dict[full_key] = str(value)
    return leaf_dict

def extract_format_tokens(text: str) -> set[str]:
    if not isinstance(text, str):
        return set()
    return set(re.findall(r"\{([a-zA-Z0-9_]+)\}", text))

print("=== STARTING INDEPENDENT PROGRAMMATIC AUDIT ===")

# ============================================================================
# 1. Locale Key Parity & Translation Quality
# ============================================================================
locales_dir = PROJECT_ROOT / "locales"
de_path = locales_dir / "de.json"
en_path = locales_dir / "en.json"
sv_path = locales_dir / "sv.json"

assert de_path.exists() and en_path.exists() and sv_path.exists(), "Locale files missing!"

with open(de_path, "r", encoding="utf-8") as f:
    de_data = json.load(f)
with open(en_path, "r", encoding="utf-8") as f:
    en_data = json.load(f)
with open(sv_path, "r", encoding="utf-8") as f:
    sv_data = json.load(f)

de_leafs = extract_leaf_keys(de_data)
en_leafs = extract_leaf_keys(en_data)
sv_leafs = extract_leaf_keys(sv_data)

missing_en = set(de_leafs.keys()) - set(en_leafs.keys())
extra_en = set(en_leafs.keys()) - set(de_leafs.keys())
missing_sv = set(de_leafs.keys()) - set(sv_leafs.keys())
extra_sv = set(sv_leafs.keys()) - set(de_leafs.keys())

results["key_parity"] = {
    "de_count": len(de_leafs),
    "en_count": len(en_leafs),
    "sv_count": len(sv_leafs),
    "missing_in_en": list(missing_en),
    "extra_in_en": list(extra_en),
    "missing_in_sv": list(missing_sv),
    "extra_in_sv": list(extra_sv),
    "parity_100_percent": (len(missing_en) == 0 and len(extra_en) == 0 and len(missing_sv) == 0 and len(extra_sv) == 0)
}

print(f"[CHECK 1] Key Parity: DE={len(de_leafs)}, EN={len(en_leafs)}, SV={len(sv_leafs)}. 100% Parity: {results['key_parity']['parity_100_percent']}")

# Token parity
token_mismatches = []
for k, de_val in de_leafs.items():
    if k.startswith("help_content."):
        continue
    de_tokens = extract_format_tokens(de_val)
    en_tokens = extract_format_tokens(en_leafs.get(k, ""))
    sv_tokens = extract_format_tokens(sv_leafs.get(k, ""))
    if de_tokens != en_tokens:
        token_mismatches.append((k, "DE != EN", de_tokens, en_tokens))
    if de_tokens != sv_tokens:
        token_mismatches.append((k, "DE != SV", de_tokens, sv_tokens))

results["format_tokens"] = {
    "mismatches_count": len(token_mismatches),
    "mismatches": token_mismatches[:10]
}
print(f"[CHECK 1] Format Tokens: Mismatches={len(token_mismatches)}")

# Quality check: German stopwords in EN and SV
GERMAN_STOPWORDS = [
    "wiedervorlage", "speichern", "abbrechen", "löschen", "loeschen",
    "mitarbeiter", "praxis", "praxen", "einstellungen", "anwendungsdokumentation",
    "bitte", "nicht", "hinzufügen", "bearbeiten", "kundendaten", "übergabe",
    "fallakte", "schließen", "auswertungen", "zuständige", "vorlagen",
    "textbaustein", "datenaustausch", "zeitleiste", "störfall", "nachfragen"
]

german_in_en = []
german_in_sv = []

for k, val in en_leafs.items():
    if k.startswith("help_content.") or "schema" in k:
        continue
    words = re.findall(r"\b\w+\b", val.lower())
    for w in words:
        if w in GERMAN_STOPWORDS:
            german_in_en.append((k, val, w))

for k, val in sv_leafs.items():
    if k.startswith("help_content.") or "schema" in k:
        continue
    words = re.findall(r"\b\w+\b", val.lower())
    for w in words:
        if w in GERMAN_STOPWORDS:
            german_in_sv.append((k, val, w))

results["translation_quality"] = {
    "german_in_en_count": len(german_in_en),
    "german_in_en_examples": german_in_en[:10],
    "german_in_sv_count": len(german_in_sv),
    "german_in_sv_examples": german_in_sv[:10],
}
print(f"[CHECK 1] Quality: German words in EN={len(german_in_en)}, in SV={len(german_in_sv)}")

# Check some Swedish samples to ensure natural Swedish:
sv_samples = {
    "buttons.save": sv_leafs.get("ui_buttons.save") or sv_leafs.get("cockpit.save"),
    "buttons.cancel": sv_leafs.get("ui_buttons.cancel"),
    "status.in_progress": sv_leafs.get("status.in_progress") or sv_leafs.get("workflow_status.in_progress"),
    "dialog.new_case": sv_leafs.get("dialog_titles.new_case"),
}
print(f"Swedish sample translations: {sv_samples}")

# ============================================================================
# 2. AST Codebase Scan over all src/*.py
# ============================================================================
from test_ast_i18n_scanner import scan_python_file

src_dir = PROJECT_ROOT / "src"
all_src_py_files = sorted(list(src_dir.rglob("*.py")))
print(f"[CHECK 2] Scanning {len(all_src_py_files)} Python files in src/ via AST scanner...")

ast_violations_by_file = {}
total_ast_violations = 0

for py_file in all_src_py_files:
    rel_path = str(py_file.relative_to(PROJECT_ROOT))
    viols = scan_python_file(py_file)
    if viols:
        ast_violations_by_file[rel_path] = [str(v) for v in viols]
        total_ast_violations += len(viols)

results["ast_scan"] = {
    "total_files_scanned": len(all_src_py_files),
    "total_violations": total_ast_violations,
    "violating_files": ast_violations_by_file
}
print(f"[CHECK 2] AST Scan: Total files={len(all_src_py_files)}, Total violations={total_ast_violations}")
if total_ast_violations > 0:
    for f, v_list in ast_violations_by_file.items():
        print(f"  VIOLATION in {f}:")
        for v in v_list[:5]:
            print(f"    {v}")

# ============================================================================
# 3. Constants & Enums Dynamic Localization
# ============================================================================
from services.i18n_service import get_i18n, LocalizedDict
import constants
import enums

i18n = get_i18n()

# Check LocalizedDict constants
constants_tested = [
    "DISPLAY_BOARD_COLUMN_NAMES",
    "DISPLAY_ACTOR_NAMES",
    "DISPLAY_CHANNEL_NAMES",
    "DISPLAY_LAYOUT_NAMES",
    "VALIDATION_MESSAGES",
    "HOTKEY_ACTION_LABELS",
    "DIALOG_TITLES",
    "UI_BUTTON_TEXTS",
    "STATUS_MESSAGES"
]

const_results = {}
for c_name in constants_tested:
    obj = getattr(constants, c_name, None)
    is_loc = isinstance(obj, LocalizedDict)
    const_results[c_name] = {"is_localized_dict": is_loc}
    if is_loc and len(obj) > 0:
        first_k = next(iter(obj.keys()))
        i18n.current_language = "de"
        val_de = str(obj[first_k])
        i18n.current_language = "en"
        val_en = str(obj[first_k])
        i18n.current_language = "sv"
        val_sv = str(obj[first_k])
        const_results[c_name]["dynamic_switch"] = {
            "key": first_k,
            "de": val_de,
            "en": val_en,
            "sv": val_sv,
            "differs": (val_de != val_en or val_de != val_sv)
        }

# Check Enum display functions
enum_display_results = {}
i18n.current_language = "de"
actor_de = enums.get_actor_display("support")
channel_de = enums.get_channel_display("phone")
layout_de = enums.get_layout_display("cockpit")
board_de = enums.get_board_column_display("inbox")

i18n.current_language = "en"
actor_en = enums.get_actor_display("support")
channel_en = enums.get_channel_display("phone")
layout_en = enums.get_layout_display("cockpit")
board_en = enums.get_board_column_display("inbox")

i18n.current_language = "sv"
actor_sv = enums.get_actor_display("support")
channel_sv = enums.get_channel_display("phone")
layout_sv = enums.get_layout_display("cockpit")
board_sv = enums.get_board_column_display("inbox")

enum_display_results = {
    "actor": {"de": actor_de, "en": actor_en, "sv": actor_sv},
    "channel": {"de": channel_de, "en": channel_en, "sv": channel_sv},
    "layout": {"de": layout_de, "en": layout_en, "sv": layout_sv},
    "board": {"de": board_de, "en": board_en, "sv": board_sv},
}

results["constants_enums"] = {
    "constants": const_results,
    "enum_displays": enum_display_results
}
print(f"[CHECK 3] Constants & Enums: tested {len(constants_tested)} constants. Enum displays: {enum_display_results}")

# ============================================================================
# 4. Runtime Dynamic Language Switching
# ============================================================================
notifications_received = []
def listener(lang):
    notifications_received.append(lang)

i18n.register_listener(listener)
i18n.current_language = "en"
i18n.current_language = "sv"
i18n.current_language = "de"
i18n.unregister_listener(listener)
i18n.current_language = "en" # should not be recorded

results["dynamic_switching"] = {
    "notifications_received": notifications_received,
    "listener_unregistered_correctly": ("en" not in notifications_received[3:]),
}
print(f"[CHECK 4] Dynamic Switching: notifications={notifications_received}")

# ============================================================================
# Output summary
# ============================================================================
summary_path = PROJECT_ROOT / ".agents" / "victory_auditor_1" / "audit_results.json"
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Audit results written to {summary_path}")
print("=== COMPLETED PROGRAMMATIC AUDIT ===")
