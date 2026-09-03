import json

with open(".agents/explorer_survey_i18n/scan_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total files: {data['total_files_with_hardcoded']}")
print(f"Total occurrences: {data['total_occurrences']}")
print("\nFiles breakdown:")
for fpath, items in sorted(data["files"].items(), key=lambda x: len(x[1]), reverse=True):
    print(f"- `{fpath}`: {len(items)} strings")

print("\nSample strings per file:")
for fpath, items in sorted(data["files"].items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n### `{fpath}` ({len(items)})")
    for it in items[:6]:
        print(f"  - L{it['line']} [{it['type']}]: {it['text']}")
