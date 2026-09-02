import ast
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

src_dir = Path("src").resolve()

hardcoded_findings = []

for root, _, files in os.walk(src_dir):
    for file in files:
        if not file.endswith(".py"):
            continue
        filepath = Path(root) / file
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(filepath))
            except Exception:
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                for keyword in node.keywords:
                    if keyword.arg in ("text", "placeholder_text", "title"):
                        if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                            val = keyword.value.value
                            if val and len(val.strip()) > 1 and any(c.isalpha() for c in val):
                                hardcoded_findings.append((filepath, node.lineno, func_name, keyword.arg, val))

print(f"Total findings: {len(hardcoded_findings)}")
# Group by relative path
from collections import defaultdict
by_file = defaultdict(list)
for fp, line, fn, arg, val in hardcoded_findings:
    rel = str(fp.relative_to(src_dir))
    by_file[rel].append((line, fn, arg, val))

for rel in sorted(by_file.keys()):
    print(f"\n=== {rel} ({len(by_file[rel])} strings) ===")
    for line, fn, arg, val in by_file[rel][:15]:
        print(f"  L{line:03d} | {fn}({arg}='{val[:60]}')")
