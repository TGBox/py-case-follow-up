import ast
import json
from pathlib import Path

# Load de.json keys
with open("locales/de.json", "r", encoding="utf-8") as f:
    de_data = json.load(f)

def flatten(d, prefix=""):
    items = {}
    for k, v in d.items():
        curr = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, curr))
        else:
            items[curr] = v
    return items

de_keys = flatten(de_data)

# Scan all tr(...) calls in src/
src_dir = Path("src")
tr_calls = []

for py_file in sorted(src_dir.rglob("*.py")):
    rel_path = py_file.relative_to(src_dir.parent).as_posix()
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        tree = ast.parse(content, filename=str(py_file))
    except Exception:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            is_tr = False
            if isinstance(node.func, ast.Name) and node.func.id == "tr":
                is_tr = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "tr":
                is_tr = True

            if is_tr and node.args:
                key_arg = node.args[0]
                if isinstance(key_arg, ast.Constant) and isinstance(key_arg.value, str):
                    key = key_arg.value
                    default_val = None
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        default_val = node.args[1].value
                    for kw in node.keywords:
                        if kw.arg == "default" and isinstance(kw.value, ast.Constant):
                            default_val = kw.value.value
                    tr_calls.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "key": key,
                        "default": default_val,
                        "exists_in_de_json": key in de_keys
                    })
                elif isinstance(key_arg, ast.JoinedStr):
                    # dynamic f-string key
                    tr_calls.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "key": "<f-string dynamic>",
                        "default": None,
                        "exists_in_de_json": None
                    })

missing_keys = [c for c in tr_calls if c["exists_in_de_json"] is False]

report = {
    "total_tr_calls": len(tr_calls),
    "missing_keys_count": len(missing_keys),
    "missing_keys": missing_keys,
    "all_tr_calls": tr_calls
}

with open(".agents/explorer_survey_i18n/tr_calls_audit.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"Total tr(...) calls: {len(tr_calls)}")
print(f"Missing in locales/de.json: {len(missing_keys)}")
for m in missing_keys:
    print(f"  - {m['key']} (in {m['file']}:{m['line']}, default='{m['default']}')")
