import ast
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"
LOCALES_DIR = PROJECT_ROOT / "locales"

def get_all_py_files():
    py_files = []
    for root, dirs, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)
    return sorted(py_files)

def analyze_ast(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        return {"error": str(e), "hardcoded_ui_strings": [], "all_string_literals": []}

    hardcoded_ui_strings = []
    all_string_literals = []

    # Common UI widget classes or methods
    ui_classes = {
        "CTkButton", "CTkLabel", "CTkCheckBox", "CTkEntry", "CTkOptionMenu",
        "CTkSegmentedButton", "CTkRadioButton", "CTkTabview", "CTkSwitch",
        "CTkProgressBar", "CTkToolTip", "ToastNotification", "CTkTextbox",
        "CTkInputDialog"
    }

    ui_dialog_funcs = {
        "showinfo", "showwarning", "showerror", "askyesno", "askokcancel",
        "askretrycancel", "askquestion", "askopenfilename", "asksaveasfilename",
        "askdirectory"
    }

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            # Check if this is a UI widget call
            if func_name in ui_classes:
                for kw in node.keywords:
                    if kw.arg in ("text", "placeholder_text", "values", "message"):
                        # Check if it's a string literal (Constant)
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            val = kw.value.value.strip()
                            if val and not val.isdigit() and len(val) > 1:
                                hardcoded_ui_strings.append({
                                    "type": f"{func_name}.{kw.arg}",
                                    "line": kw.value.lineno,
                                    "text": kw.value.value
                                })
                        elif isinstance(kw.value, (ast.List, ast.Tuple)):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    val = elt.value.strip()
                                    if val and len(val) > 1:
                                        hardcoded_ui_strings.append({
                                            "type": f"{func_name}.{kw.arg}[]",
                                            "line": elt.lineno,
                                            "text": elt.value
                                        })

            elif func_name in ui_dialog_funcs:
                for kw in node.keywords:
                    if kw.arg in ("title", "message"):
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            hardcoded_ui_strings.append({
                                "type": f"{func_name}.{kw.arg}",
                                "line": kw.value.lineno,
                                "text": kw.value.value
                            })
                # Check positional args
                for idx, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        hardcoded_ui_strings.append({
                            "type": f"{func_name}.arg{idx}",
                            "line": arg.lineno,
                            "text": arg.value
                        })

            self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                s = node.value.strip()
                # Exclude trivial formatting or special identifiers
                if len(s) > 1 and not s.startswith("__") and "\n" not in s and len(s) < 100:
                    all_string_literals.append({
                        "line": node.lineno,
                        "text": node.value
                    })
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)

    return {
        "hardcoded_ui_strings": hardcoded_ui_strings,
        "all_string_literals": all_string_literals,
        "loc": len(content.splitlines())
    }

def scan_locales():
    locales = {}
    for lang in ["de", "en", "sv"]:
        p = LOCALES_DIR / f"{lang}.json"
        if p.exists():
            try:
                locales[lang] = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                locales[lang] = {"_error": str(e)}
        else:
            locales[lang] = {}

    def get_flat_keys(d, prefix=""):
        res = {}
        for k, v in d.items():
            full_k = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                res.update(get_flat_keys(v, full_k))
            else:
                res[full_k] = v
        return res

    flat = {lang: get_flat_keys(locales[lang]) for lang in locales}
    all_keys = set().union(*[flat[l].keys() for l in flat])

    missing_keys = {lang: [] for lang in flat}
    untranslated_sv = []
    untranslated_en = []

    for k in sorted(all_keys):
        for lang in ["de", "en", "sv"]:
            if k not in flat[lang]:
                missing_keys[lang].append(k)

        # Check if sv has german/english text or identical to de
        de_val = flat.get("de", {}).get(k, "")
        sv_val = flat.get("sv", {}).get(k, "")
        en_val = flat.get("en", {}).get(k, "")

        if de_val and sv_val and de_val == sv_val and len(de_val) > 4 and any(c.isalpha() for c in de_val):
            # Check if likely untranslated
            untranslated_sv.append((k, de_val, sv_val))
        if de_val and en_val and de_val == en_val and len(de_val) > 4 and any(c.isalpha() for c in de_val):
            untranslated_en.append((k, de_val, en_val))

    return {
        "counts": {lang: len(flat[lang]) for lang in flat},
        "all_keys_count": len(all_keys),
        "missing_keys": missing_keys,
        "untranslated_sv_sample": untranslated_sv[:30],
        "untranslated_sv_count": len(untranslated_sv),
        "untranslated_en_sample": untranslated_en[:30],
        "untranslated_en_count": len(untranslated_en),
    }

if __name__ == "__main__":
    files = get_all_py_files()
    file_results = {}
    total_hardcoded_ui = 0
    for f in files:
        rel = f.relative_to(PROJECT_ROOT).as_posix()
        res = analyze_ast(f)
        file_results[rel] = res
        total_hardcoded_ui += len(res.get("hardcoded_ui_strings", []))

    loc_info = scan_locales()

    output = {
        "total_files": len(files),
        "total_hardcoded_ui_elements": total_hardcoded_ui,
        "locales": loc_info,
        "file_results": file_results
    }

    out_path = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\scan_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scan complete. Total files: {len(files)}, Total Hardcoded UI Elements: {total_hardcoded_ui}")
    print(f"Locales: {loc_info['counts']}, Total distinct keys: {loc_info['all_keys_count']}")
    print(f"Missing in EN: {len(loc_info['missing_keys']['en'])}, Missing in SV: {len(loc_info['missing_keys']['sv'])}, Missing in DE: {len(loc_info['missing_keys']['de'])}")
