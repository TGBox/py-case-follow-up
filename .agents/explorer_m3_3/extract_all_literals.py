import os
import sys
import json
import ast
import re
from pathlib import Path

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

from test_ast_i18n_scanner import I18nASTScanner

scanner = I18nASTScanner()

class LiteralInspector(ast.NodeVisitor):
    def __init__(self, file_path, source_lines):
        self.file_path = file_path
        self.source_lines = source_lines
        self.literals = []
        self.current_func = None
        self.current_class = None

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def visit_AsyncFunctionDef(self, node):
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            val = node.value
            # Ignore docstrings
            # Check if exempt
            is_exempt = scanner.is_exempt_string(val)
            line_idx = getattr(node, "lineno", 1) - 1
            line_content = self.source_lines[line_idx].strip() if 0 <= line_idx < len(self.source_lines) else ""
            
            # Check if line is logging
            if any(l in line_content for l in ("logger.", "logging.", "print(", ".debug(", ".info(", ".warning(", ".error(")):
                is_logging = True
            else:
                is_logging = False

            # Check if inside tr(...) or LocalizedDict or constants
            is_tr = "tr(" in line_content or "LocalizedDict" in line_content or "gettext" in line_content

            self.literals.append({
                "file": self.file_path,
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "class": self.current_class,
                "func": self.current_func,
                "value": val,
                "is_exempt": is_exempt,
                "is_logging": is_logging,
                "is_tr": is_tr,
                "line_content": line_content
            })
        self.generic_visit(node)

files_to_scan = [
    project_root / "src" / "ui" / "app.py",
    project_root / "src" / "ui" / "app_dialogs.py",
] + sorted(list((project_root / "src" / "ui" / "views").glob("*.py"))) + sorted(list((project_root / "src" / "ui" / "widgets").glob("*.py")))

all_literals = []
file_stats = {}

for fpath in files_to_scan:
    rel = fpath.relative_to(project_root).as_posix()
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    lines = src.splitlines()
    tree = ast.parse(src, filename=rel)
    inspector = LiteralInspector(rel, lines)
    inspector.visit(tree)
    
    # Filter for non-exempt, non-logging, non-tr strings
    candidate_untranslated = [
        lit for lit in inspector.literals
        if not lit["is_exempt"] and not lit["is_logging"] and not lit["is_tr"]
    ]
    file_stats[rel] = {
        "total_literals": len(inspector.literals),
        "candidates_untranslated": len(candidate_untranslated),
        "items": candidate_untranslated
    }
    all_literals.extend(candidate_untranslated)

with open(project_root / ".agents" / "explorer_m3_3" / "untranslated_candidates.json", "w", encoding="utf-8") as f:
    json.dump({
        "total_candidates": len(all_literals),
        "file_stats": file_stats
    }, f, indent=2, ensure_ascii=False)

print(f"Total candidate non-exempt string literals: {len(all_literals)}")
for f, stat in file_stats.items():
    print(f"  {f}: {stat['candidates_untranslated']} candidate literals")
