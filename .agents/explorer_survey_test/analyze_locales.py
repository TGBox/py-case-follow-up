import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

german_words = [
    "wiedervorlage", "speichern", "abbrechen", "schließen", "schliessen", "löschen", "loeschen",
    "mitarbeiter", "einstellungen", "praxis", "praxen", "vorlagen", "formulare", "hilfetext",
    "datenaustausch", "zuständigkeit", "zustaendigkeit", "bearbeiten", "hinzufügen", "hinzufuegen",
    "übersicht", "uebersicht", "anwendungsdokumentation", "zeitleiste", "anhänge", "anhaenge",
    "beispieldaten", "neuer fall", "programmbereiche", "textbausteine", "fall-akte", "drucken",
    "umwandeln", "erledigt", "bitte", "nicht", "oder", "und", "konfiguration", "kommunikation"
]

for lang in ["en", "sv"]:
    p = Path(f"locales/{lang}.json")
    if not p.exists():
        print(f"Missing {p}")
        continue
    data = json.loads(p.read_text(encoding="utf-8"))

    def check_words(d, prefix=""):
        matches = []
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                matches.extend(check_words(v, full))
            elif isinstance(v, str):
                v_lower = v.lower()
                for gw in german_words:
                    # check word boundary
                    if f" {gw} " in f" {v_lower} " or gw in v_lower:
                        matches.append((full, gw, v))
                        break
        return matches

    matches = check_words(data)
    print(f"=== German word / pattern matches in {lang}.json ({len(matches)}) ===")
    for full, gw, v in matches[:20]:
        print(f"  [{full}] (matched '{gw}'): {v[:80]}")
    if len(matches) > 20:
        print(f"  ... and {len(matches)-20} more")
