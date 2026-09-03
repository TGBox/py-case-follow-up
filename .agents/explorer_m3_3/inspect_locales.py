import json
from pathlib import Path

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

with open(project_root / "locales" / "de.json", "r", encoding="utf-8") as f:
    de = json.load(f)
with open(project_root / "locales" / "en.json", "r", encoding="utf-8") as f:
    en = json.load(f)
with open(project_root / "locales" / "sv.json", "r", encoding="utf-8") as f:
    sv = json.load(f)

sections = ["analytics", "attachments", "board", "case_list", "cockpit", "common", "date_picker", "dynamic_form", "table", "timeline", "toast", "wiki"]

out_lines = []
for s in sections:
    out_lines.append(f"=== {s} ===")
    s_de = de.get(s, {})
    for k, v in sorted(s_de.items()):
        en_v = en.get(s, {}).get(k, 'MISSING')
        sv_v = sv.get(s, {}).get(k, 'MISSING')
        out_lines.append(f"  {k}:\n    DE: {v}\n    EN: {en_v}\n    SV: {sv_v}")

with open(project_root / ".agents" / "explorer_m3_3" / "existing_ui_locales.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Wrote existing_ui_locales.txt successfully.")
