import os
import sys
import json
from pathlib import Path

# Add project root and tests to path
sys.path.insert(0, r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
sys.path.insert(0, r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\tests")

from test_ast_i18n_scanner import scan_python_file, ASTViolation

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

files_to_scan = [
    project_root / "src" / "ui" / "app.py",
    project_root / "src" / "ui" / "app_dialogs.py",
] + list((project_root / "src" / "ui" / "views").glob("*.py")) + list((project_root / "src" / "ui" / "widgets").glob("*.py"))

results = {}
total_violations = 0

for file_path in sorted(files_to_scan):
    rel_path = file_path.relative_to(project_root).as_posix()
    violations = scan_python_file(file_path)
    results[rel_path] = violations
    total_violations += len(violations)
    print(f"{rel_path}: {len(violations)} violations")
    for v in violations:
        print(f"  L{v.line}:{v.col} [{v.component}({v.argument})] -> {repr(v.raw_value)}")

print(f"\nTotal violations found by test_ast_i18n_scanner: {total_violations}")
