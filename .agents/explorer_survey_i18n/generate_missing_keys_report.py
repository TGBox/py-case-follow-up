import json

with open(".agents/explorer_survey_i18n/tr_calls_audit.json", "r", encoding="utf-8") as f:
    data = json.load(f)

missing = data["missing_keys"]
all_calls = data["all_tr_calls"]

lines = []
lines.append("# Audit of `tr(...)` Calls and Missing Keys in `locales/*.json`\n")
lines.append(f"**Total `tr(...)` Calls Found in `src/`:** {data['total_tr_calls']}\n")
lines.append(f"**Total `tr(...)` Keys Missing from `locales/de.json`:** {len(missing)}\n")

# Group missing by prefix or namespace
namespaces = {}
for m in missing:
    k = m["key"]
    ns = k.split(".")[0] if "." in k else "root"
    namespaces.setdefault(ns, []).append(m)

lines.append("## Missing Keys by Namespace / Prefix\n")
lines.append("| Namespace | Missing Keys Count | Example Keys |")
lines.append("| :--- | :---: | :--- |")

for ns, items in sorted(namespaces.items(), key=lambda x: len(x[1]), reverse=True):
    unique_keys = list(set(it["key"] for it in items))
    examples = ", ".join(f"`{k}`" for k in unique_keys[:3])
    if len(unique_keys) > 3:
        examples += f", ... (+{len(unique_keys)-3} more)"
    lines.append(f"| `{ns}` | {len(unique_keys)} | {examples} |")

lines.append("\n---\n")
lines.append("## Detailed List of Missing Keys (with File, Line, and Default Fallback)\n")

for ns, items in sorted(namespaces.items(), key=lambda x: len(x[1]), reverse=True):
    lines.append(f"### Namespace: `{ns}`\n")
    lines.append("| Key | File:Line | Default Text (German Fallback) |")
    lines.append("| :--- | :--- | :--- |")
    seen = set()
    for it in items:
        entry = (it["key"], it["file"], it["line"])
        if entry in seen:
            continue
        seen.add(entry)
        def_text = str(it.get("default") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{it['key']}` | `{it['file']}:{it['line']}` | \"{def_text}\" |")
    lines.append("")

with open(".agents/explorer_survey_i18n/missing_keys_audit.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Saved missing keys audit: {len(missing)} missing calls.")
