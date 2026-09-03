import ast
import json
from pathlib import Path

src_dir = Path("src")
results = {}
total_occurrences = 0

ignore_values = {
    "nsew", "center", "left", "right", "top", "bottom", "x", "y", "both",
    "normal", "disabled", "readonly", "transparent", "clam", "w", "e", "n", "s",
    "ew", "ns", "nw", "ne", "sw", "se", "horizontal", "vertical", "browse", "extended",
    "none", "single", "multiple", "Dark", "Light", "System", "dark", "light", "system",
    "gray", "blue", "green", "red", "white", "black", "forestgreen", "darkblue", "firebrick",
    "darkgoldenrod", "darkgreen", "limegreen", "gold", "dodgerblue", "darkviolet",
    "Arial", "Segoe UI", "Consolas", "Courier", "Helvetica", "Roboto",
    "bold", "italic", "underline",
}

for py_file in sorted(src_dir.rglob("*.py")):
    rel_path = py_file.relative_to(src_dir.parent).as_posix()
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=str(py_file))
    except Exception as e:
        print(f"Error parsing {rel_path}: {e}")
        continue

    file_findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            # Check self.title("...")
            if func_name == "title" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                s = node.args[0].value.strip()
                if s and s not in ignore_values and len(s) > 1:
                    file_findings.append({
                        "line": node.lineno,
                        "type": "title",
                        "call": func_name,
                        "text": s
                    })

            # Check CTk widget creation with string literals
            for kw in node.keywords:
                if kw.arg in ("text", "placeholder_text", "title", "message") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    s = kw.value.value.strip()
                    if s and s not in ignore_values and not s.startswith("#") and len(s) > 1:
                        # Avoid single symbols unless emoji or meaningful
                        file_findings.append({
                            "line": node.lineno,
                            "type": kw.arg,
                            "call": func_name,
                            "text": s
                        })
                elif kw.arg == "values" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    # Check list of string literals in values=[...]
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            s = elt.value.strip()
                            if s and s not in ignore_values and len(s) > 1:
                                file_findings.append({
                                    "line": node.lineno,
                                    "type": "values_item",
                                    "call": func_name,
                                    "text": s
                                })

    if file_findings:
        results[rel_path] = file_findings
        total_occurrences += len(file_findings)

output_data = {
    "total_files_with_hardcoded": len(results),
    "total_occurrences": total_occurrences,
    "files": results
}

with open(".agents/explorer_survey_i18n/scan_results.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Scan complete: {total_occurrences} occurrences in {len(results)} files.")
