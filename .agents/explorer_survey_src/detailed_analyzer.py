import ast
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"
LOCALES_DIR = PROJECT_ROOT / "locales"

def get_files():
    files_by_category = {
        "root": [],
        "models": [],
        "services": [],
        "ui_core": [],
        "ui_views": [],
        "ui_widgets": [],
        "ui_dialogs": [],
        "utils": []
    }
    for root, dirs, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                p = Path(root) / f
                rel = p.relative_to(SRC_DIR).as_posix()
                if "/" not in rel:
                    files_by_category["root"].append(p)
                elif rel.startswith("models/"):
                    files_by_category["models"].append(p)
                elif rel.startswith("services/"):
                    files_by_category["services"].append(p)
                elif rel.startswith("ui/views/"):
                    files_by_category["ui_views"].append(p)
                elif rel.startswith("ui/widgets/"):
                    files_by_category["ui_widgets"].append(p)
                elif rel.startswith("ui/dialogs/"):
                    files_by_category["ui_dialogs"].append(p)
                elif rel.startswith("ui/"):
                    files_by_category["ui_core"].append(p)
                elif rel.startswith("utils/"):
                    files_by_category["utils"].append(p)
    return files_by_category

def analyze_file(p: Path):
    rel = p.relative_to(PROJECT_ROOT).as_posix()
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()
    tree = ast.parse(content, filename=str(p))

    ui_hardcoded = []
    dialog_hardcoded = []
    toast_hardcoded = []
    tooltip_hardcoded = []
    tr_calls = []
    has_language_listener = False
    has_refresh_or_on_language = False

    class Visitor(ast.NodeVisitor):
        nonlocal has_language_listener, has_refresh_or_on_language

        def visit_FunctionDef(self, node):
            if node.name in ("on_language_changed", "refresh_ui_labels", "retranslate_ui", "update_language"):
                has_refresh_or_on_language = True
            self.generic_visit(node)

        def visit_Call(self, node):
            nonlocal has_language_listener
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "register_listener":
                has_language_listener = True

            if func_name == "tr":
                # record key if constant
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    tr_calls.append({"line": node.lineno, "key": node.args[0].value})

            # Check UI widgets
            ui_classes = {
                "CTkButton", "CTkLabel", "CTkCheckBox", "CTkEntry", "CTkOptionMenu",
                "CTkSegmentedButton", "CTkRadioButton", "CTkTabview", "CTkSwitch",
                "CTkProgressBar", "CTkTextbox", "CTkInputDialog", "SearchableCombobox",
                "DatePicker"
            }
            if func_name in ui_classes:
                for kw in node.keywords:
                    if kw.arg in ("text", "placeholder_text", "values"):
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            val = kw.value.value.strip()
                            if val and not val.isdigit() and len(val) > 0:
                                ui_hardcoded.append({
                                    "widget": func_name,
                                    "prop": kw.arg,
                                    "line": kw.value.lineno,
                                    "text": kw.value.value
                                })
                        elif isinstance(kw.value, (ast.List, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    ui_hardcoded.append({
                                        "widget": func_name,
                                        "prop": f"{kw.arg}[]",
                                        "line": elt.lineno,
                                        "text": elt.value
                                    })

            # Check Tooltips
            if func_name in ("CTkToolTip", "ToolTip", "CTkTooltip"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    tooltip_hardcoded.append({
                        "line": node.lineno,
                        "text": node.args[0].value
                    })
                for kw in node.keywords:
                    if kw.arg in ("message", "text"):
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            tooltip_hardcoded.append({
                                "line": kw.value.lineno,
                                "text": kw.value.value
                            })

            # Check ToastNotification
            if func_name in ("ToastNotification", "show_toast"):
                toast_info = {"line": node.lineno}
                for kw in node.keywords:
                    if kw.arg in ("title", "message") and isinstance(kw.value, ast.Constant):
                        toast_info[kw.arg] = kw.value.value
                if "title" in toast_info or "message" in toast_info:
                    toast_hardcoded.append(toast_info)

            # Check standard dialogs / file dialogs
            dialog_methods = {
                "showinfo", "showwarning", "showerror", "askyesno", "askokcancel",
                "askretrycancel", "askquestion", "askopenfilename", "asksaveasfilename",
                "askdirectory"
            }
            if func_name in dialog_methods:
                diag_info = {"line": node.lineno, "func": func_name}
                for idx, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        diag_info[f"arg{idx}"] = arg.value
                for kw in node.keywords:
                    if kw.arg in ("title", "message", "filetypes") and isinstance(kw.value, ast.Constant):
                        diag_info[kw.arg] = kw.value.value
                dialog_hardcoded.append(diag_info)

            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)

    # Also regex search for common user visible patterns (e.g. self.title("..."), ctk.CTkLabel(..., text="..."), messagebox.show...
    return {
        "file": rel,
        "loc": len(lines),
        "has_language_listener": has_language_listener,
        "has_refresh_or_on_language": has_refresh_or_on_language,
        "tr_calls_count": len(tr_calls),
        "ui_hardcoded": ui_hardcoded,
        "tooltip_hardcoded": tooltip_hardcoded,
        "toast_hardcoded": toast_hardcoded,
        "dialog_hardcoded": dialog_hardcoded,
    }

if __name__ == "__main__":
    files_by_cat = get_files()
    cat_summary = {}
    detailed_files = {}

    for cat, file_list in files_by_cat.items():
        cat_summary[cat] = {
            "file_count": len(file_list),
            "ui_hardcoded_count": 0,
            "dialog_count": 0,
            "toast_count": 0,
            "tooltip_count": 0,
            "tr_calls_count": 0,
            "files": []
        }
        for f in sorted(file_list):
            res = analyze_file(f)
            detailed_files[res["file"]] = res
            cat_summary[cat]["ui_hardcoded_count"] += len(res["ui_hardcoded"])
            cat_summary[cat]["dialog_count"] += len(res["dialog_hardcoded"])
            cat_summary[cat]["toast_count"] += len(res["toast_hardcoded"])
            cat_summary[cat]["tooltip_count"] += len(res["tooltip_hardcoded"])
            cat_summary[cat]["tr_calls_count"] += res["tr_calls_count"]
            cat_summary[cat]["files"].append(res["file"])

    out = {
        "category_summary": cat_summary,
        "detailed_files": detailed_files
    }
    out_p = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\detailed_analysis.json")
    out_p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Detailed analysis saved.")
    for cat, s in cat_summary.items():
        print(f"[{cat}] {s['file_count']} files, UI hardcoded: {s['ui_hardcoded_count']}, Dialogs: {s['dialog_count']}, Toasts: {s['toast_count']}, Tooltips: {s['tooltip_count']}, tr() calls: {s['tr_calls_count']}")
