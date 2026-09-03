import ast
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"

def generate_inventory():
    all_files = sorted(list(SRC_DIR.glob("**/*.py")))
    
    file_catalogs = {}
    
    for f in all_files:
        rel = f.relative_to(SRC_DIR).as_posix()
        content = f.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        try:
            tree = ast.parse(content, filename=str(f))
        except Exception as e:
            file_catalogs[rel] = {"error": str(e), "entries": []}
            continue
            
        entries = []
        
        class InvVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    
                # 1. UI Widgets
                if func_name in ("CTkButton", "CTkLabel", "CTkCheckBox", "CTkEntry", "CTkOptionMenu", 
                                 "CTkSegmentedButton", "CTkRadioButton", "CTkTabview", "CTkSwitch",
                                 "CTkProgressBar", "CTkTextbox", "CTkInputDialog", "SearchableCombobox", "DatePicker"):
                    for kw in node.keywords:
                        if kw.arg in ("text", "placeholder_text", "values", "message"):
                            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                val = kw.value.value.strip()
                                if val and not val.isdigit() and not (val.startswith("●") or val.startswith("▶") or val.startswith("◀") or val.startswith("👁")):
                                    entries.append({
                                        "line": kw.value.lineno,
                                        "category": "UI Widget",
                                        "target": f"{func_name}.{kw.arg}",
                                        "value": kw.value.value,
                                        "snippet": lines[kw.value.lineno - 1].strip() if kw.value.lineno <= len(lines) else ""
                                    })
                            elif isinstance(kw.value, (ast.List, ast.Tuple)):
                                for elt in kw.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        val = elt.value.strip()
                                        if val and not val.isdigit():
                                            entries.append({
                                                "line": elt.lineno,
                                                "category": "UI Widget List Option",
                                                "target": f"{func_name}.{kw.arg}[]",
                                                "value": elt.value,
                                                "snippet": lines[elt.lineno - 1].strip() if elt.lineno <= len(lines) else ""
                                            })
                                            
                # 2. Tooltips
                elif func_name in ("CTkToolTip", "ToolTip", "CTkTooltip"):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        entries.append({
                            "line": node.args[0].lineno,
                            "category": "Tooltip",
                            "target": "CTkToolTip(message=...)",
                            "value": node.args[0].value,
                            "snippet": lines[node.args[0].lineno - 1].strip()
                        })
                    for kw in node.keywords:
                        if kw.arg in ("message", "text") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            entries.append({
                                "line": kw.value.lineno,
                                "category": "Tooltip",
                                "target": f"CTkToolTip({kw.arg}=...)",
                                "value": kw.value.value,
                                "snippet": lines[kw.value.lineno - 1].strip()
                            })
                            
                # 3. Toasts & Popups
                elif func_name in ("ToastNotification", "show_toast"):
                    for kw in node.keywords:
                        if kw.arg in ("title", "message") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            entries.append({
                                "line": kw.value.lineno,
                                "category": "Toast Notification",
                                "target": f"ToastNotification.{kw.arg}",
                                "value": kw.value.value,
                                "snippet": lines[kw.value.lineno - 1].strip()
                            })
                            
                # 4. Dialogs / File Dialogs
                elif func_name in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askretrycancel", "askquestion", "askopenfilename", "asksaveasfilename", "askdirectory"):
                    for kw in node.keywords:
                        if kw.arg in ("title", "message") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            entries.append({
                                "line": kw.value.lineno,
                                "category": "Dialog / FileDialog",
                                "target": f"{func_name}.{kw.arg}",
                                "value": kw.value.value,
                                "snippet": lines[kw.value.lineno - 1].strip()
                            })
                    for idx, arg in enumerate(node.args):
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and len(arg.value) > 2:
                            entries.append({
                                "line": arg.lineno,
                                "category": "Dialog / FileDialog",
                                "target": f"{func_name}.arg{idx}",
                                "value": arg.value,
                                "snippet": lines[arg.lineno - 1].strip()
                            })
                            
                # 5. Window Titles
                elif func_name == "title":
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        entries.append({
                            "line": node.args[0].lineno,
                            "category": "Window Title",
                            "target": "self.title(...)",
                            "value": node.args[0].value,
                            "snippet": lines[node.args[0].lineno - 1].strip()
                        })

                self.generic_visit(node)

        InvVisitor().visit(tree)
        file_catalogs[rel] = {
            "loc": len(lines),
            "entries_count": len(entries),
            "entries": entries
        }
        
    return file_catalogs

if __name__ == "__main__":
    cat = generate_inventory()
    out_p = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\full_inventory.json")
    out_p.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    
    total = sum(v["entries_count"] for v in cat.values())
    print(f"Inventory completed. Total files: {len(cat)}, Total hardcoded UI/Dialog items: {total}")
    for k, v in sorted(cat.items(), key=lambda x: x[1]["entries_count"], reverse=True):
        if v["entries_count"] > 0:
            print(f"  {k}: {v['entries_count']} entries")
