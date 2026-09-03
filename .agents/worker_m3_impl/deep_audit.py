import json
import re
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

de = json.load(open('locales/de.json', encoding='utf-8'))
en = json.load(open('locales/en.json', encoding='utf-8'))
sv = json.load(open('locales/sv.json', encoding='utf-8'))

def get_keys(d, prefix=''):
    keys = {}
    for k, v in d.items():
        fk = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            keys.update(get_keys(v, fk))
        else:
            keys[fk] = v
    return keys

de_k = get_keys(de)
en_k = get_keys(en)
sv_k = get_keys(sv)

# 1. Check all tr calls in python files
print("=== AUDIT 1: tr() calls vs locales ===")
m3_files = [
    Path('src/ui/app.py'),
    Path('src/ui/app_dialogs.py'),
] + list(Path('src/ui/views').glob('*.py')) + list(Path('src/ui/widgets').glob('*.py'))

for p in m3_files:
    text = p.read_text(encoding='utf-8')
    tree = ast.parse(text, filename=str(p))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_id = ""
            if isinstance(node.func, ast.Name):
                func_id = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_id = node.func.attr
            if func_id == "tr" and node.args and isinstance(node.args[0], ast.Constant):
                key = node.args[0].value
                if key not in de_k:
                    print(f"MISSING KEY in de.json: {p.name}:{node.lineno} -> tr('{key}')")
                else:
                    # Check kwargs vs format tokens in locale
                    de_val = de_k[key]
                    tokens = set(re.findall(r'\{([a-zA-Z0-9_]+)\}', de_val))
                    kw_names = {kw.arg for kw in node.keywords}
                    if tokens != kw_names:
                        print(f"KWARG MISMATCH: {p.name}:{node.lineno} -> tr('{key}') expects {tokens} but got {kw_names} (de='{de_val}')")

# 2. Check refresh_ui_labels implementation in all views and widgets
print("\n=== AUDIT 2: refresh_ui_labels in views & widgets ===")
for p in list(Path('src/ui/views').glob('*.py')) + list(Path('src/ui/widgets').glob('*.py')):
    text = p.read_text(encoding='utf-8')
    tree = ast.parse(text, filename=str(p))
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for c in classes:
        methods = [n.name for n in c.body if isinstance(n, ast.FunctionDef)]
        has_refresh = "refresh_ui_labels" in methods
        print(f"Class {c.name} in {p.name}: refresh_ui_labels -> {'YES' if has_refresh else 'NO'}")
