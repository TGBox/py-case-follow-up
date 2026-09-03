import json
from pathlib import Path

LOCALES_DIR = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\locales")

de = json.loads((LOCALES_DIR / "de.json").read_text(encoding="utf-8"))
en = json.loads((LOCALES_DIR / "en.json").read_text(encoding="utf-8"))
sv = json.loads((LOCALES_DIR / "sv.json").read_text(encoding="utf-8"))

def flatten(d, prefix=""):
    items = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten(v, key))
        else:
            items[key] = v
    return items

de_flat = flatten(de)
en_flat = flatten(en)
sv_flat = flatten(sv)

all_keys = sorted(set(de_flat) | set(en_flat) | set(sv_flat))

print(f"Total Unique Keys: {len(all_keys)}")
print(f"DE Keys: {len(de_flat)}")
print(f"EN Keys: {len(en_flat)}")
print(f"SV Keys: {len(sv_flat)}")

# Check key discrepancies
missing_in_en = [k for k in all_keys if k not in en_flat]
missing_in_sv = [k for k in all_keys if k not in sv_flat]
missing_in_de = [k for k in all_keys if k not in de_flat]

print(f"Missing in EN: {len(missing_in_en)}")
print(f"Missing in SV: {len(missing_in_sv)}")
print(f"Missing in DE: {len(missing_in_de)}")

# Check identical strings (untranslated)
de_sv_identical = [(k, de_flat[k], sv_flat[k]) for k in all_keys if k in de_flat and k in sv_flat and de_flat[k] == sv_flat[k] and len(de_flat[k]) > 3 and any(c.isalpha() for c in de_flat[k])]
de_en_identical = [(k, de_flat[k], en_flat[k]) for k in all_keys if k in de_flat and k in en_flat and de_flat[k] == en_flat[k] and len(de_flat[k]) > 3 and any(c.isalpha() for c in de_flat[k])]

print(f"Identical DE == SV values (potential untranslated): {len(de_sv_identical)}")
print(f"Identical DE == EN values (potential untranslated): {len(de_en_identical)}")

# Print sample identical DE == SV
print("\n--- Sample DE == SV Identical Values ---")
for k, d, s in de_sv_identical[:20]:
    print(f"  {k}: '{d}'")

# Check top-level namespaces
namespaces = sorted(set(k.split('.')[0] for k in all_keys))
print(f"\nNamespaces in locales: {namespaces}")
for ns in namespaces:
    ns_keys = [k for k in all_keys if k.startswith(ns + ".") or k == ns]
    print(f"  {ns}: {len(ns_keys)} keys")
