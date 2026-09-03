import json
import re
from pathlib import Path

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

print(f"Total keys - DE: {len(de_k)}, EN: {len(en_k)}, SV: {len(sv_k)}")

diff_de_en = set(de_k.keys()) ^ set(en_k.keys())
diff_de_sv = set(de_k.keys()) ^ set(sv_k.keys())
print(f"DE vs EN key differences: {len(diff_de_en)}")
print(f"DE vs SV key differences: {len(diff_de_sv)}")

tr_pattern = re.compile(r'\btr\(\s*[\"\']([^\"\']+)[\"\']')
missing = []
for p in Path('src').rglob('*.py'):
    text = p.read_text(encoding='utf-8')
    for m in tr_pattern.findall(text):
        if m not in de_k:
            missing.append(f"{p}: {m}")

print(f"Missing tr keys in de.json: {len(missing)}")
for x in missing:
    print("  ", x)
