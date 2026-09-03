import json
from pathlib import Path

with open(".agents/explorer_survey_i18n/scan_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("# Detailed Audit of Extracted Hardcoded UI Strings in `src/`\n")
lines.append(f"**Total Files with Unlocalized String Literals:** {data['total_files_with_hardcoded']}\n")
lines.append(f"**Total Hardcoded String Occurrences Found:** {data['total_occurrences']}\n")

lines.append("## Summary Table by File\n")
lines.append("| File Path | Hardcoded Occurrences | Key Categories |")
lines.append("| :--- | :---: | :--- |")

for fpath, items in sorted(data["files"].items(), key=lambda x: len(x[1]), reverse=True):
    types = set(it["type"] for it in items)
    lines.append(f"| `{fpath}` | {len(items)} | {', '.join(sorted(types))} |")

lines.append("\n---\n")
lines.append("## Detailed File-by-File Breakdown\n")

for fpath, items in sorted(data["files"].items(), key=lambda x: len(x[1]), reverse=True):
    lines.append(f"### `{fpath}` ({len(items)} occurrences)\n")
    lines.append("| Line | Type | Function / Widget | String Literal |")
    lines.append("| :---: | :--- | :--- | :--- |")
    for it in items:
        clean_text = it['text'].replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {it['line']} | `{it['type']}` | `{it['call']}` | \"{clean_text}\" |")
    lines.append("")

with open(".agents/explorer_survey_i18n/extracted_strings_audit.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Wrote detailed audit to extracted_strings_audit.md")
