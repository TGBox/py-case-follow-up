import ast
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up")
SRC_DIR = PROJECT_ROOT / "src"

def analyze_all_files_deep():
    results = {}
    
    for root, dirs, files in os.walk(SRC_DIR):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            rel = path.relative_to(SRC_DIR).as_posix()
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Find all string literals that look like German or user-facing text
            # e.g., german words, sentences with punctuation, labels, titles, messages, placeholders
            user_facing_candidates = []
            
            # Use AST to inspect string constants and where they appear
            try:
                tree = ast.parse(content, filename=str(path))
            except Exception as e:
                results[rel] = {"error": str(e)}
                continue

            class DeepVisitor(ast.NodeVisitor):
                def visit_Call(self, node):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    # Check all keyword args
                    for kw in node.keywords:
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            val = kw.value.value.strip()
                            if val and len(val) > 1 and not val.startswith("__") and not val.isupper() and not re.match(r"^[a-z0-9_]+$", val):
                                user_facing_candidates.append({
                                    "line": kw.value.lineno,
                                    "context": f"Call({func_name}, {kw.arg}='...')",
                                    "text": kw.value.value
                                })
                        elif isinstance(kw.value, ast.JoinedStr): # f-string
                            user_facing_candidates.append({
                                "line": kw.value.lineno,
                                "context": f"Call({func_name}, {kw.arg}=f'...)",
                                "text": "[F-String]"
                            })

                    # Check positional args
                    for idx, arg in enumerate(node.args):
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            val = arg.value.strip()
                            if val and len(val) > 2 and (" " in val or any(c in "äöüÄÖÜß!?:." for c in val)):
                                user_facing_candidates.append({
                                    "line": arg.lineno,
                                    "context": f"Call({func_name}, arg{idx}='...')",
                                    "text": arg.value
                                })

                    self.generic_visit(node)

                def visit_Assign(self, node):
                    # Check top-level or class-level assignments with strings
                    for target in node.targets:
                        target_name = ""
                        if isinstance(target, ast.Name):
                            target_name = target.id
                        elif isinstance(target, ast.Attribute):
                            target_name = target.attr

                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            val = node.value.value.strip()
                            if val and len(val) > 2 and (" " in val or any(c in "äöüÄÖÜß!?:." for c in val)):
                                user_facing_candidates.append({
                                    "line": node.value.lineno,
                                    "context": f"Assign({target_name} = '...')",
                                    "text": node.value.value
                                })
                    self.generic_visit(node)

            DeepVisitor().visit(tree)

            # Deduplicate candidates by line and text
            seen = set()
            unique_candidates = []
            for c in user_facing_candidates:
                key = (c["line"], c["text"])
                if key not in seen:
                    seen.add(key)
                    unique_candidates.append(c)

            results[rel] = {
                "loc": len(lines),
                "candidates_count": len(unique_candidates),
                "candidates": unique_candidates
            }

    return results

if __name__ == "__main__":
    res = analyze_all_files_deep()
    out_p = Path(r"c:\Users\DaniBani\Documents\VisualStudioCodeProjects\py-case-follow-up\.agents\explorer_survey_src\deep_scan.json")
    out_p.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    
    total_candidates = sum(v.get("candidates_count", 0) for v in res.values())
    print(f"Deep scan completed across {len(res)} files. Total candidates: {total_candidates}")
    for k, v in sorted(res.items(), key=lambda x: x[1].get("candidates_count", 0), reverse=True):
        if v.get("candidates_count", 0) > 0:
            print(f"  {k}: {v['candidates_count']} items (lines: {v['loc']})")
