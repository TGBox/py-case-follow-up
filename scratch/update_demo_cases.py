import json
from pathlib import Path

cases_de = {
    "c1_title": "Zuzahlungsnachforderungsdatei fehlerhaft erzeugt",
    "c2_title": "Absturz beim Drucken von BMA-Rezepten",
    "c3_title": "KV-Abrechnungstext korrigieren",
    "c4_title": "Prüfung Nachforderung 2026-Q1",
    "c5_title": "GUI-Schriftgröße im Laborfenster zu klein"
}

cases_en = {
    "c1_title": "Additional co-payment claim file generated with errors",
    "c2_title": "Crash when printing BMA prescriptions",
    "c3_title": "Correct KV billing text",
    "c4_title": "Review 2026-Q1 additional claim",
    "c5_title": "GUI font size in laboratory window too small"
}

cases_sv = {
    "c1_title": "Tilläggsbetalningsfil genererad med fel",
    "c2_title": "Krasch vid utskrift av BMA-recept",
    "c3_title": "Korrigera KV-faktureringstext",
    "c4_title": "Granskning av tilläggsanspråk 2026-Q1",
    "c5_title": "GUI-teckenstorlek i laboratoriefönstret för liten"
}

for path, data in [("locales/de.json", cases_de), ("locales/en.json", cases_en), ("locales/sv.json", cases_sv)]:
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["demo_cases"] = data
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

print("demo_cases successfully updated in all locale JSON files!")
