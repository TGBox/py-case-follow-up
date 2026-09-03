import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

def inspect_constants():
    import importlib.util
    spec = importlib.util.spec_from_file_location("constants", PROJECT_ROOT / "src" / "constants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    print("=== CONSTANTS INSPECTION ===")
    attrs = dir(mod)
    for a in sorted(attrs):
        if a.startswith("__"):
            continue
        val = getattr(mod, a)
        if isinstance(val, (dict, list, str, tuple)) and not callable(val):
            val_repr = str(val)
            if len(val_repr) > 80:
                val_repr = val_repr[:77] + "..."
            print(f"  {a} ({type(val).__name__}): {val_repr}")

def inspect_enums():
    import importlib.util
    spec = importlib.util.spec_from_file_location("enums", PROJECT_ROOT / "src" / "enums.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    print("\n=== ENUMS INSPECTION ===")
    for a in dir(mod):
        if a.startswith("__"):
            continue
        val = getattr(mod, a)
        print(f"  {a}: {type(val).__name__}")

def inspect_services():
    print("\n=== SERVICES WITH STRINGS ===")
    for p in (PROJECT_ROOT / "src" / "services").glob("*.py"):
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        tr_count = content.count("tr(")
        print(f"  {p.name}: {len(lines)} lines, {tr_count} tr() occurrences")

if __name__ == "__main__":
    inspect_constants()
    inspect_enums()
    inspect_services()
