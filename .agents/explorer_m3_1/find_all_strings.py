import ast
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

files = [
    "src/ui/app.py",
    "src/ui/views/cockpit_view.py",
    "src/ui/views/cockpit_layout_builders.py",
    "src/ui/views/board_view.py",
    "src/ui/views/table_view.py",
    "src/ui/views/analytics_view.py",
]

class StringVisitor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.strings = []

    def visit_Constant(self, node):
        if isinstance(node.value, str) and len(node.value.strip()) > 1:
            self.strings.append((node.lineno, node.col_offset, node.value))
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        # f-string
        self.strings.append((node.lineno, node.col_offset, f"<f-string line {node.lineno}>"))
        self.generic_visit(node)

for rel_path in files:
    fpath = root / rel_path
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read(), filename=rel_path)
    visitor = StringVisitor(rel_path)
    visitor.visit(tree)
    print(f"=== {rel_path} ({len(visitor.strings)} strings) ===")
    for line, col, val in visitor.strings:
        # filter out purely code symbols / regex
        if any(c in val for c in ["ä", "ö", "ü", "Ä", "Ö", "Ü", "ß", " ", "🔔", "✓", "📋", "🏥", "🏢", "👤", "⏳", "❌", "🌗", "🧪", "⚙", "📄", "🔄", "📥", "📤", "📦", "📖", "🎯", "💻", "🚨", "🔴", "🟡", "🟢", "🏆", "⭐", "⏱"]):
            print(f"  Line {line:3d}:{col:2d} -> {repr(val)}")
    print()
