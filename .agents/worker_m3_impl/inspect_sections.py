import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

de = json.load(open('locales/de.json', encoding='utf-8'))
en = json.load(open('locales/en.json', encoding='utf-8'))
sv = json.load(open('locales/sv.json', encoding='utf-8'))

sections = [
    'app', 'cockpit', 'board', 'table', 'analytics',
    'case_list', 'date_picker', 'datetime', 'dynamic_form',
    'attachments', 'wiki', 'timeline', 'searchable_combo',
    'toast', 'common'
]

for s in sections:
    print(f"\n=== SECTION: {s} ===")
    de_sec = de.get(s, {})
    en_sec = en.get(s, {})
    sv_sec = sv.get(s, {})
    all_keys = sorted(set(de_sec.keys()) | set(en_sec.keys()) | set(sv_sec.keys()))
    for k in all_keys:
        de_val = de_sec.get(k, '<MISSING>')
        en_val = en_sec.get(k, '<MISSING>')
        sv_val = sv_sec.get(k, '<MISSING>')
        print(f"  {k}:")
        print(f"    DE: {de_val}")
        print(f"    EN: {en_val}")
        print(f"    SV: {sv_val}")
