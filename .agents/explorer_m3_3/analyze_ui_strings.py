import os
import sys
import json
import ast
import re
from pathlib import Path

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

# Load locales
locales = {}
for lang in ("de", "en", "sv"):
    p = project_root / "locales" / f"{lang}.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            locales[lang] = json.load(f)
    else:
        locales[lang] = {}

def get_nested_val(data, key):
    keys = key.split(".")
    curr = data
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return None
    return curr

# Find all tr(...) calls in files
class TrCallExtractor(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.tr_calls = []

    def visit_Call(self, node):
        is_tr = False
        if isinstance(node.func, ast.Name) and node.func.id in ("tr", "_"):
            is_tr = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "tr":
            is_tr = True

        if is_tr and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                key = first_arg.value
                default_val = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                    default_val = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "default" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        default_val = kw.value.value

                self.tr_calls.append({
                    "file": self.file_path,
                    "line": getattr(node, "lineno", 0),
                    "key": key,
                    "default": default_val
                })
        self.generic_visit(node)

files_to_scan = [
    project_root / "src" / "ui" / "app.py",
    project_root / "src" / "ui" / "app_dialogs.py",
] + sorted(list((project_root / "src" / "ui" / "views").glob("*.py"))) + sorted(list((project_root / "src" / "ui" / "widgets").glob("*.py")))

all_tr_calls = []
for fpath in files_to_scan:
    rel = fpath.relative_to(project_root).as_posix()
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()
    tree = ast.parse(code, filename=rel)
    extractor = TrCallExtractor(rel)
    extractor.visit(tree)
    all_tr_calls.extend(extractor.tr_calls)

print(f"Total tr(...) calls across M3 UI files: {len(all_tr_calls)}")

# Check key status in locales
tr_status = []
missing_in_de = []
missing_in_en = []
missing_in_sv = []

for item in all_tr_calls:
    k = item["key"]
    de_val = get_nested_val(locales.get("de", {}), k)
    en_val = get_nested_val(locales.get("en", {}), k)
    sv_val = get_nested_val(locales.get("sv", {}), k)
    
    st = {
        **item,
        "de": de_val,
        "en": en_val,
        "sv": sv_val,
        "has_de": de_val is not None,
        "has_en": en_val is not None,
        "has_sv": sv_val is not None,
    }
    tr_status.append(st)
    if de_val is None:
        missing_in_de.append(st)
    if en_val is None:
        missing_in_en.append(st)
    if sv_val is None:
        missing_in_sv.append(st)

print(f"tr(...) keys missing in de.json: {len(missing_in_de)}")
print(f"tr(...) keys missing in en.json: {len(missing_in_en)}")
print(f"tr(...) keys missing in sv.json: {len(missing_in_sv)}")

with open(project_root / ".agents" / "explorer_m3_3" / "tr_calls_audit.json", "w", encoding="utf-8") as f:
    json.dump({
        "total_tr_calls": len(all_tr_calls),
        "missing_in_de_count": len(missing_in_de),
        "missing_in_en_count": len(missing_in_en),
        "missing_in_sv_count": len(missing_in_sv),
        "missing_in_de": missing_in_de,
        "missing_in_en": missing_in_en,
        "missing_in_sv": missing_in_sv,
        "all_tr_calls": tr_status
    }, f, indent=2, ensure_ascii=False)
