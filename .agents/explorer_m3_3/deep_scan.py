import os
import sys
import json
import ast
import re
from pathlib import Path

# Add project root and tests to path
sys.path.insert(0, r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
sys.path.insert(0, r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\tests")

from test_ast_i18n_scanner import I18nASTScanner, scan_python_file, ASTViolation

project_root = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")

# Load existing locales
locales = {}
for lang in ("de", "en", "sv"):
    p = project_root / "locales" / f"{lang}.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            locales[lang] = json.load(f)
    else:
        locales[lang] = {}

def get_all_keys(d, prefix=""):
    keys = {}
    for k, v in d.items():
        full_k = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_all_keys(v, full_k))
        else:
            keys[full_k] = v
    return keys

all_locale_keys = {lang: get_all_keys(locales[lang]) for lang in locales}

# Enhanced AST Scanner for UI scope
class DeepUIASTScanner(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings = []
        self.base_scanner = I18nASTScanner(file_path=file_path)

    def is_exempt_string(self, text: str) -> bool:
        return self.base_scanner.is_exempt_string(text)

    def is_tr_call(self, node: ast.AST) -> bool:
        return self.base_scanner.is_tr_or_localized_call(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Ignore logging
        if func_name in ("debug", "info", "warning", "error", "critical", "exception", "log"):
            return

        # 1. Base scanner checks
        # CTkTabview.add("tab_name")
        if func_name == "add" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if not self.is_exempt_string(arg.value) and not self.is_tr_call(arg):
                    self.findings.append({
                        "file": self.file_path,
                        "line": getattr(node, "lineno", 0),
                        "component": "CTkTabview.add",
                        "arg": "name",
                        "value": arg.value,
                        "type": "tab_name"
                    })

        # Treeview .heading("col", text="Header") or .heading("col", ...)
        if func_name == "heading":
            for kw in node.keywords:
                if kw.arg == "text":
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": "treeview.heading",
                                "arg": "text",
                                "value": kw.value.value,
                                "type": "treeview_heading"
                            })

        # CTkTooltip(widget, text="...") or CTkTooltip(widget, message="...")
        if func_name == "CTkToolTip" or func_name == "CTkTooltip":
            if node.args and len(node.args) > 1 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                if not self.is_exempt_string(node.args[1].value) and not self.is_tr_call(node.args[1]):
                    self.findings.append({
                        "file": self.file_path,
                        "line": getattr(node, "lineno", 0),
                        "component": "CTkToolTip",
                        "arg": "message",
                        "value": node.args[1].value,
                        "type": "tooltip"
                    })
            for kw in node.keywords:
                if kw.arg in ("text", "message"):
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": "CTkToolTip",
                                "arg": kw.arg,
                                "value": kw.value.value,
                                "type": "tooltip"
                            })

        # ToastNotification(parent, message="...", title="...")
        if func_name == "ToastNotification":
            if node.args and len(node.args) > 1:
                # 2nd positional arg is message
                arg2 = node.args[1]
                if isinstance(arg2, ast.Constant) and isinstance(arg2.value, str):
                    if not self.is_exempt_string(arg2.value) and not self.is_tr_call(arg2):
                        self.findings.append({
                            "file": self.file_path,
                            "line": getattr(node, "lineno", 0),
                            "component": "ToastNotification",
                            "arg": "message",
                            "value": arg2.value,
                            "type": "toast_message"
                        })
            for kw in node.keywords:
                if kw.arg in ("message", "title"):
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": "ToastNotification",
                                "arg": kw.arg,
                                "value": kw.value.value,
                                "type": "toast_kwarg"
                            })

        # Check standard UI widgets
        if func_name in I18nASTScanner.UI_WIDGET_CLASSES:
            # check positional args (some widgets might take text as first or second arg)
            # but usually ctk widgets take master as first arg, text as kwarg
            for kw in node.keywords:
                if kw.arg in I18nASTScanner.USER_VISIBLE_KWARGS:
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": func_name,
                                "arg": kw.arg,
                                "value": kw.value.value,
                                "type": "widget_kwarg"
                            })
                elif kw.arg == "values":
                    if isinstance(kw.value, ast.List):
                        for elem in kw.value.elts:
                            if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
                                if not self.is_exempt_string(elem.value) and not self.is_tr_call(elem):
                                    self.findings.append({
                                        "file": self.file_path,
                                        "line": getattr(node, "lineno", 0),
                                        "component": func_name,
                                        "arg": "values",
                                        "value": elem.value,
                                        "type": "values_list"
                                    })

        elif func_name == "configure":
            for kw in node.keywords:
                if kw.arg in I18nASTScanner.USER_VISIBLE_KWARGS or kw.arg == "values":
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": "configure",
                                "arg": kw.arg,
                                "value": kw.value.value,
                                "type": "configure_kwarg"
                            })
                    elif isinstance(kw.value, ast.List) and kw.arg == "values":
                        for elem in kw.value.elts:
                            if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
                                if not self.is_exempt_string(elem.value) and not self.is_tr_call(elem):
                                    self.findings.append({
                                        "file": self.file_path,
                                        "line": getattr(node, "lineno", 0),
                                        "component": "configure",
                                        "arg": "values",
                                        "value": elem.value,
                                        "type": "configure_values"
                                    })

        elif func_name == "title":
            if node.args and len(node.args) == 1:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if not self.is_exempt_string(arg.value) and not self.is_tr_call(arg):
                        self.findings.append({
                            "file": self.file_path,
                            "line": getattr(node, "lineno", 0),
                            "component": "title",
                            "arg": "title",
                            "value": arg.value,
                            "type": "window_title"
                        })

        elif func_name in I18nASTScanner.POPUP_FUNCTION_NAMES:
            for kw in node.keywords:
                if kw.arg in ("title", "message"):
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        if not self.is_exempt_string(kw.value.value) and not self.is_tr_call(kw.value):
                            self.findings.append({
                                "file": self.file_path,
                                "line": getattr(node, "lineno", 0),
                                "component": func_name,
                                "arg": kw.arg,
                                "value": kw.value.value,
                                "type": "popup"
                            })

        self.generic_visit(node)

# Scan files
files_to_scan = [
    project_root / "src" / "ui" / "app.py",
    project_root / "src" / "ui" / "app_dialogs.py",
] + sorted(list((project_root / "src" / "ui" / "views").glob("*.py"))) + sorted(list((project_root / "src" / "ui" / "widgets").glob("*.py")))

all_findings = []
file_summary = {}

for fpath in files_to_scan:
    rel = fpath.relative_to(project_root).as_posix()
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()
    try:
        tree = ast.parse(code, filename=rel)
        scanner = DeepUIASTScanner(rel)
        scanner.visit(tree)
        findings = scanner.findings
        all_findings.extend(findings)
        file_summary[rel] = len(findings)
    except Exception as e:
        file_summary[rel] = f"Error: {e}"

output_data = {
    "total_findings": len(all_findings),
    "file_summary": file_summary,
    "findings": all_findings,
}

with open(project_root / ".agents" / "explorer_m3_3" / "ast_scan_results.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Deep AST Scan completed. Total findings: {len(all_findings)}")
for f, cnt in file_summary.items():
    print(f"  {f}: {cnt}")
