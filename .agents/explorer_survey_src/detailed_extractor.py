import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"

def analyze_file_detailed(rel_path: str):
    file_path = SRC_DIR / rel_path
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    tree = ast.parse(content, filename=str(file_path))
    
    items = []
    
    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            # 1. CTk widgets with text/placeholder/values
            if func_name in ("CTkButton", "CTkLabel", "CTkCheckBox", "CTkEntry", "CTkOptionMenu", 
                             "CTkSegmentedButton", "CTkRadioButton", "CTkTabview", "CTkSwitch",
                             "CTkProgressBar", "CTkTextbox", "CTkInputDialog", "SearchableCombobox", "DatePicker"):
                for kw in node.keywords:
                    if kw.arg in ("text", "placeholder_text", "values", "message"):
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            val = kw.value.value.strip()
                            if val and not val.isdigit():
                                items.append({
                                    "kind": "UI_WIDGET_PROP",
                                    "widget": func_name,
                                    "prop": kw.arg,
                                    "line": kw.value.lineno,
                                    "text": kw.value.value,
                                    "code_snippet": lines[kw.value.lineno - 1].strip() if kw.value.lineno <= len(lines) else ""
                                })
                        elif isinstance(kw.value, (ast.List, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    items.append({
                                        "kind": "UI_WIDGET_LIST_ITEM",
                                        "widget": func_name,
                                        "prop": kw.arg,
                                        "line": elt.lineno,
                                        "text": elt.value,
                                        "code_snippet": lines[elt.lineno - 1].strip() if elt.lineno <= len(lines) else ""
                                    })
                                    
            # 2. CTkToolTip / ToolTip
            elif func_name in ("CTkToolTip", "ToolTip", "CTkTooltip"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    items.append({
                        "kind": "TOOLTIP",
                        "widget": func_name,
                        "prop": "message",
                        "line": node.args[0].lineno,
                        "text": node.args[0].value,
                        "code_snippet": lines[node.args[0].lineno - 1].strip()
                    })
                for kw in node.keywords:
                    if kw.arg in ("message", "text") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        items.append({
                            "kind": "TOOLTIP",
                            "widget": func_name,
                            "prop": kw.arg,
                            "line": kw.value.lineno,
                            "text": kw.value.value,
                            "code_snippet": lines[kw.value.lineno - 1].strip()
                        })

            # 3. ToastNotification / show_toast
            elif func_name in ("ToastNotification", "show_toast"):
                for kw in node.keywords:
                    if kw.arg in ("title", "message") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        items.append({
                            "kind": "TOAST",
                            "widget": func_name,
                            "prop": kw.arg,
                            "line": kw.value.lineno,
                            "text": kw.value.value,
                            "code_snippet": lines[kw.value.lineno - 1].strip()
                        })

            # 4. messagebox & file dialogs
            elif func_name in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askretrycancel", "askquestion", "askopenfilename", "asksaveasfilename", "askdirectory"):
                for kw in node.keywords:
                    if kw.arg in ("title", "message") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        items.append({
                            "kind": "DIALOG_POPUP",
                            "widget": func_name,
                            "prop": kw.arg,
                            "line": kw.value.lineno,
                            "text": kw.value.value,
                            "code_snippet": lines[kw.value.lineno - 1].strip()
                        })
                for idx, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        items.append({
                            "kind": "DIALOG_POPUP",
                            "widget": func_name,
                            "prop": f"arg{idx}",
                            "line": arg.lineno,
                            "text": arg.value,
                            "code_snippet": lines[arg.lineno - 1].strip()
                        })
                        
            # 5. self.title(...)
            elif func_name == "title":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    items.append({
                        "kind": "WINDOW_TITLE",
                        "widget": "title",
                        "prop": "title",
                        "line": node.args[0].lineno,
                        "text": node.args[0].value,
                        "code_snippet": lines[node.args[0].lineno - 1].strip()
                    })

            self.generic_visit(node)

    Visitor().visit(tree)
    return {
        "file": rel_path,
        "loc": len(lines),
        "items": items
    }

def main():
    dialog_files = [f.name for f in (SRC_DIR / "ui" / "dialogs").glob("*.py")]
    view_files = [f.name for f in (SRC_DIR / "ui" / "views").glob("*.py")]
    widget_files = [f.name for f in (SRC_DIR / "ui" / "widgets").glob("*.py")]
    core_files = ["ui/app.py", "ui/app_dialogs.py"]

    report_data = {
        "dialogs": {},
        "views": {},
        "widgets": {},
        "core": {}
    }

    for d in sorted(dialog_files):
        report_data["dialogs"][d] = analyze_file_detailed(f"ui/dialogs/{d}")

    for v in sorted(view_files):
        report_data["views"][v] = analyze_file_detailed(f"ui/views/{v}")

    for w in sorted(widget_files):
        report_data["widgets"][w] = analyze_file_detailed(f"ui/widgets/{w}")

    for c in sorted(core_files):
        report_data["core"][c] = analyze_file_detailed(c)

    out_p = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\ui_inventory.json")
    out_p.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("UI Inventory completed and saved.")

if __name__ == "__main__":
    main()
