import ast
from pathlib import Path

dialog_dir = Path("src/ui/dialogs")
dialog_report = []

for py_file in sorted(dialog_dir.glob("*.py")):
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=str(py_file))
    except Exception as e:
        continue

    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    methods = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    has_refresh = "refresh_ui_labels" in methods

    # Check title calls
    title_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute) and node.func.attr == "title":
                # get arg
                if node.args:
                    arg_str = ast.unparse(node.args[0])
                    title_calls.append((node.lineno, arg_str))

    dialog_report.append({
        "file": py_file.name,
        "classes": classes,
        "has_refresh_ui_labels": has_refresh,
        "title_calls": title_calls,
    })

lines = ["# Dialogs Survey\n"]
lines.append("| Dialog File | Main Class | Has `refresh_ui_labels` | `self.title(...)` expression |")
lines.append("| :--- | :--- | :---: | :--- |")

for d in dialog_report:
    cls_str = ", ".join(d["classes"]) if d["classes"] else "-"
    titles_str = "<br>".join(f"L{lno}: `{expr}`" for lno, expr in d["title_calls"]) if d["title_calls"] else "-"
    lines.append(f"| `{d['file']}` | `{cls_str}` | {'✅' if d['has_refresh_ui_labels'] else '❌'} | {titles_str} |")

with open(".agents/explorer_survey_i18n/dialogs_survey.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Wrote dialogs survey to dialogs_survey.md")
