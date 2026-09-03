import sys
import io
from pathlib import Path

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

from tests.test_ast_i18n_scanner import scan_python_file

files = [
    "src/ui/app.py",
    "src/ui/views/cockpit_view.py",
    "src/ui/views/cockpit_layout_builders.py",
    "src/ui/views/board_view.py",
    "src/ui/views/table_view.py",
    "src/ui/views/analytics_view.py",
]

total = 0
for f in files:
    v = scan_python_file(root / f)
    total += len(v)
    print(f"=== {f} ({len(v)} AST violations) ===")
    for item in v:
        print(f"  Line {item.line}:{item.col} [{item.component}({item.argument}=\"{item.raw_value}\")] -> {item.reason}")
    print()

print(f"TOTAL AST VIOLATIONS IN TARGET FILES: {total}")
