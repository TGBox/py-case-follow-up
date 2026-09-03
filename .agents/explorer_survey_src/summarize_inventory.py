import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

p = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\ui_inventory.json")
data = json.loads(p.read_text(encoding="utf-8"))

total_items = 0
print("=== UI INVENTORY BREAKDOWN ===")
for section, files in data.items():
    print(f"\n--- {section.upper()} ---")
    for fname, info in files.items():
        if info:
            items_count = len(info.get("items", []))
            total_items += items_count
            if items_count > 0:
                print(f"  {fname}: {items_count} hardcoded UI items (lines: {info['loc']})")
                for it in info.get("items", [])[:3]:
                    print(f"    - L{it['line']} [{it['kind']}] {it['widget']}.{it['prop']}: \"{it['text']}\"")
                if items_count > 3:
                    print(f"    ... and {items_count - 3} more items")

print(f"\nTotal Hardcoded UI Items: {total_items}")
