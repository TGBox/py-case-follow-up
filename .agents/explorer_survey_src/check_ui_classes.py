import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"

def check_classes():
    classes_info = []
    
    for py_file in (SRC_DIR / "ui").glob("**/*.py"):
        rel = py_file.relative_to(SRC_DIR).as_posix()
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                has_refresh = any(m in ("refresh_ui_labels", "on_language_changed", "retranslate_ui", "update_language") for m in methods)
                base_names = []
                for b in node.bases:
                    if isinstance(b, ast.Name):
                        base_names.append(b.id)
                    elif isinstance(b, ast.Attribute):
                        base_names.append(b.attr)
                        
                classes_info.append({
                    "file": rel,
                    "class": node.name,
                    "line": node.lineno,
                    "bases": base_names,
                    "has_refresh": has_refresh,
                    "methods": methods
                })
                
    return classes_info

if __name__ == "__main__":
    res = check_classes()
    print(f"Total UI classes found: {len(res)}")
    with_refresh = [c for c in res if c["has_refresh"]]
    without_refresh = [c for c in res if not c["has_refresh"]]
    
    print(f"\nClasses WITH refresh/language handler ({len(with_refresh)}):")
    for c in with_refresh:
        print(f"  [+] {c['class']} ({c['file']}:{c['line']})")
        
    print(f"\nClasses WITHOUT refresh/language handler ({len(without_refresh)}):")
    for c in without_refresh:
        print(f"  [-] {c['class']} ({c['file']}:{c['line']}) bases={c['bases']}")
