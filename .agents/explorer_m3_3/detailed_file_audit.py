import os
import sys
import json
import ast
from pathlib import Path

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

files = [
    "src/ui/app.py",
    "src/ui/app_dialogs.py",
    "src/ui/views/analytics_view.py",
    "src/ui/views/board_view.py",
    "src/ui/views/cockpit_layout_builders.py",
    "src/ui/views/cockpit_view.py",
    "src/ui/views/table_view.py",
    "src/ui/widgets/attachment_widget.py",
    "src/ui/widgets/case_list_widget.py",
    "src/ui/widgets/ctk_tooltip.py",
    "src/ui/widgets/date_picker.py",
    "src/ui/widgets/dynamic_form_field_renderers.py",
    "src/ui/widgets/dynamic_form_widget.py",
    "src/ui/widgets/searchable_combobox.py",
    "src/ui/widgets/timeline_widget.py",
    "src/ui/widgets/toast_notification.py",
    "src/ui/widgets/wiki_widget.py",
]

def analyze_file(rel_path):
    fpath = project_root / rel_path
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    lines = content.splitlines()
    tree = ast.parse(content, filename=rel_path)

    report = {
        "file": rel_path,
        "widgets_created": [],
        "string_constants": [],
        "tr_calls": [],
        "hardcoded_ui_texts": [],
    }

    # Collect all AST nodes
    for node in ast.walk(tree):
        # tr calls
        if isinstance(node, ast.Call):
            is_tr = False
            if isinstance(node.func, ast.Name) and node.func.id in ("tr", "_"):
                is_tr = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "tr":
                is_tr = True
            if is_tr and node.args:
                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    k = node.args[0].value
                    d = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else ""
                    report["tr_calls"].append({
                        "line": getattr(node, "lineno", 0),
                        "key": k,
                        "default": d
                    })

            # Check widgets & calls
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            # Check UI widgets
            if func_name.startswith("CTk") or func_name in ("ToastNotification", "DatePickerWidget", "SearchableComboBox", "Tooltip", "CTkToolTip"):
                kw_dict = {}
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Constant):
                        kw_dict[kw.arg] = kw.value.value
                    elif isinstance(kw.value, ast.Call):
                        kw_dict[kw.arg] = "<Call>"
                report["widgets_created"].append({
                    "line": getattr(node, "lineno", 0),
                    "component": func_name,
                    "kwargs": kw_dict
                })

    return report

all_reports = {}
for f in files:
    all_reports[f] = analyze_file(f)

with open(project_root / ".agents" / "explorer_m3_3" / "file_audits.json", "w", encoding="utf-8") as f:
    json.dump(all_reports, f, indent=2, ensure_ascii=False)

print("File audit completed.")
