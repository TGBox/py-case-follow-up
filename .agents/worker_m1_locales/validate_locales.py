# -*- coding: utf-8 -*-
"""
Validation script for Milestone 1:
1. 100% Key parity across de.json, en.json, sv.json.
2. Format token matching across translations.
3. No empty leaf values.
4. All tr(...) calls in src/ resolve to existing keys.
"""

import json
import re
import os
import ast

def validate():
    # 1. Load files
    with open('locales/de.json', 'r', encoding='utf-8') as f:
        de = json.load(f)
    with open('locales/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    with open('locales/sv.json', 'r', encoding='utf-8') as f:
        sv = json.load(f)

    def get_all_leaf_keys(d, prefix=''):
        keys = {}
        for k, v in d.items():
            full = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                keys.update(get_all_leaf_keys(v, full))
            else:
                keys[full] = v
        return keys

    de_keys = get_all_leaf_keys(de)
    en_keys = get_all_leaf_keys(en)
    sv_keys = get_all_leaf_keys(sv)

    print(f"Total leaf keys in de: {len(de_keys)}")
    print(f"Total leaf keys in en: {len(en_keys)}")
    print(f"Total leaf keys in sv: {len(sv_keys)}")

    # Check parity
    diff_de_en = set(de_keys.keys()) ^ set(en_keys.keys())
    diff_de_sv = set(de_keys.keys()) ^ set(sv_keys.keys())

    assert len(diff_de_en) == 0, f"Key mismatch DE vs EN: {diff_de_en}"
    assert len(diff_de_sv) == 0, f"Key mismatch DE vs SV: {diff_de_sv}"
    print("[OK] 100% Key Parity confirmed across all 3 files!")

    # Check format tokens
    token_pattern = re.compile(r'\{([a-zA-Z0-9_]+)\}')
    token_errors = []
    for k in de_keys:
        de_tokens = set(token_pattern.findall(str(de_keys[k])))
        en_tokens = set(token_pattern.findall(str(en_keys[k])))
        sv_tokens = set(token_pattern.findall(str(sv_keys[k])))

        if de_tokens != en_tokens or de_tokens != sv_tokens:
            token_errors.append((k, de_tokens, en_tokens, sv_tokens))

    assert len(token_errors) == 0, f"Token mismatch found in keys: {token_errors}"
    print("[OK] All format tokens {placeholder} match 100% across DE, EN, and SV!")

    # Check non-empty
    empty_keys = [k for k, v in de_keys.items() if not str(v).strip() and k not in ('handover_dialog.header_suffix', 'datetime.o_clock')]
    print(f"Empty keys in DE (excluding intentional suffix/clock): {len(empty_keys)}")
    assert len(empty_keys) == 0, f"Empty values in DE: {empty_keys}"

    # Check tr(...) calls in src/
    missing_in_locales = []
    for root, dirs, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8') as fh:
                    tree = ast.parse(fh.read(), filename=p)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            func_name = None
                            if isinstance(node.func, ast.Name):
                                func_name = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                func_name = node.func.attr
                            if func_name == 'tr':
                                key = None
                                if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                                    key = node.args[0].value
                                for kw in node.keywords:
                                    if kw.arg == 'key' and isinstance(kw.value, ast.Constant):
                                        key = kw.value.value
                                if key:
                                    if key not in de_keys:
                                        missing_in_locales.append((key, f"{p}:{node.lineno}"))

    print(f"Total static tr(...) missing keys after update: {len(missing_in_locales)}")
    if missing_in_locales:
        for k, loc in missing_in_locales:
            print(f"  STILL MISSING: {k} at {loc}")
    assert len(missing_in_locales) == 0, f"Found missing tr(...) keys: {missing_in_locales}"
    print("[OK] 100% of all static tr(...) calls in src/ now resolve to valid keys in locales/*.json!")

    print("\nALL VALIDATIONS PASSED CLEANLY!")

if __name__ == '__main__':
    validate()
