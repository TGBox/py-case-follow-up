import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

de_d = json.loads(Path("locales/de.json").read_text(encoding="utf-8"))
en_d = json.loads(Path("locales/en.json").read_text(encoding="utf-8"))
sv_d = json.loads(Path("locales/sv.json").read_text(encoding="utf-8"))

def flatten(d, prefix=""):
    flat = {}
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(flatten(v, full))
        else:
            flat[full] = v
    return flat

de = flatten(de_d)
en = flatten(en_d)
sv = flatten(sv_d)

print(f"Total keys: DE={len(de)}, EN={len(en)}, SV={len(sv)}")

# Check format placeholder parity across languages:
placeholder_regex = re.compile(r"\{([a-zA-Z0-9_]+)\}")
placeholder_mismatches = []
for k in de:
    de_ph = set(placeholder_regex.findall(str(de[k])))
    en_ph = set(placeholder_regex.findall(str(en.get(k, ""))))
    sv_ph = set(placeholder_regex.findall(str(sv.get(k, ""))))
    if de_ph != en_ph or de_ph != sv_ph:
        placeholder_mismatches.append((k, de_ph, en_ph, sv_ph))

print(f"\nPlaceholder mismatches ({len(placeholder_mismatches)}):")
for k, de_ph, en_ph, sv_ph in placeholder_mismatches:
    print(f"  {k}: DE={de_ph}, EN={en_ph}, SV={sv_ph}")

# Check German-specific tokens with word boundaries in en.json
german_tokens = [
    r"\bder\b", r"\bdie\b", r"\bdas\b", r"\bund\b", r"\boder\b", r"\bnicht\b",
    r"\bbitte\b", r"\bspeichern\b", r"\babbrechen\b", r"\blöschen\b", r"\bloeschen\b",
    r"\bmitarbeiter\b", r"\bpraxis\b", r"\bpraxen\b", r"\bvorlagen\b", r"\bformulare\b",
    r"\beinstellungen\b", r"\bhinzufügen\b", r"\bbearbeiten\b", r"\bwiedervorlage\b",
    r"\bzeitleiste\b", r"\banhänge\b", r"\bzurück\b", r"\bweiter\b", r"\berledigt\b",
    r"\bkeine\b", r"\bkein\b", r"\bfehlschlag\b", r"\berfolgreich\b"
]

german_token_re = re.compile("|".join(german_tokens), re.IGNORECASE)

en_german_matches = []
for k, v in en.items():
    if isinstance(v, str):
        found = german_token_re.findall(v)
        if found:
            en_german_matches.append((k, set(found), v))

print(f"\nGerman tokens found in en.json ({len(en_german_matches)}):")
for k, tokens, v in en_german_matches:
    print(f"  {k} (tokens: {tokens}): {v[:70]}")

sv_german_matches = []
# For Swedish, exclude common shared words like 'und', but check distinct German words
sv_german_tokens = [
    r"\bder\b", r"\bdie\b", r"\bdas\b", r"\bnicht\b",
    r"\bbitte\b", r"\bspeichern\b", r"\babbrechen\b", r"\blöschen\b",
    r"\bmitarbeiter\b", r"\bpraxis\b", r"\bpraxen\b", r"\bvorlagen\b", r"\bformulare\b",
    r"\beinstellungen\b", r"\bhinzufügen\b", r"\bbearbeiten\b", r"\bwiedervorlage\b",
    r"\bzeitleiste\b", r"\banhänge\b", r"\bzurück\b", r"\berledigt\b",
    r"\bkeine\b", r"\bkein\b", r"\bfehlschlag\b", r"\berfolgreich\b"
]
sv_token_re = re.compile("|".join(sv_german_tokens), re.IGNORECASE)
for k, v in sv.items():
    if isinstance(v, str):
        found = sv_token_re.findall(v)
        if found:
            sv_german_matches.append((k, set(found), v))

print(f"\nGerman tokens found in sv.json ({len(sv_german_matches)}):")
for k, tokens, v in sv_german_matches:
    print(f"  {k} (tokens: {tokens}): {v[:70]}")
