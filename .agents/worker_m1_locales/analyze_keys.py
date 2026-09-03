import ast
import os
import json
import re

def analyze():
    tr_calls = []
    dynamic_keys = []
    
    for root, dirs, files in os.walk('src'):
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8') as fh:
                    try:
                        tree = ast.parse(fh.read(), filename=p)
                    except Exception as e:
                        print(f'Error parsing {p}: {e}')
                        continue
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            func_name = None
                            if isinstance(node.func, ast.Name):
                                func_name = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                func_name = node.func.attr
                            if func_name == 'tr':
                                key = None
                                default = None
                                # positional
                                if len(node.args) >= 1:
                                    if isinstance(node.args[0], ast.Constant):
                                        key = node.args[0].value
                                    elif isinstance(node.args[0], ast.JoinedStr):
                                        # f-string key
                                        dynamic_keys.append({
                                            'file': p.replace('\\', '/'),
                                            'line': node.lineno,
                                            'ast': ast.unparse(node.args[0])
                                        })
                                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                                    default = node.args[1].value
                                # keywords
                                for kw in node.keywords:
                                    if kw.arg == 'key' and isinstance(kw.value, ast.Constant):
                                        key = kw.value.value
                                    elif kw.arg == 'default' and isinstance(kw.value, ast.Constant):
                                        default = kw.value.value
                                
                                tr_calls.append({
                                    'file': p.replace('\\', '/'),
                                    'line': node.lineno,
                                    'key': key,
                                    'default': default,
                                })

    de = json.load(open('locales/de.json', encoding='utf-8'))
    en = json.load(open('locales/en.json', encoding='utf-8'))
    sv = json.load(open('locales/sv.json', encoding='utf-8'))

    def get_all_keys(d, prefix=''):
        keys = {}
        for k, v in d.items():
            full = f'{prefix}.{k}' if prefix else k
            if isinstance(v, dict):
                keys.update(get_all_keys(v, full))
            else:
                keys[full] = v
        return keys

    de_keys = get_all_keys(de)
    en_keys = get_all_keys(en)
    sv_keys = get_all_keys(sv)

    keys_found = {}
    for c in tr_calls:
        k = c['key']
        if not k:
            continue
        if k not in keys_found:
            keys_found[k] = {'calls': [], 'defaults': set()}
        keys_found[k]['calls'].append(f"{c['file']}:{c['line']}")
        if c['default'] is not None:
            keys_found[k]['defaults'].add(c['default'])

    missing_in_de = {}
    for k, info in keys_found.items():
        if k not in de_keys:
            missing_in_de[k] = {
                'calls': info['calls'],
                'defaults': list(info['defaults'])
            }

    report = {
        'total_tr_calls': len(tr_calls),
        'distinct_static_keys': len(keys_found),
        'dynamic_keys': dynamic_keys,
        'missing_in_de_count': len(missing_in_de),
        'missing_in_de': missing_in_de,
        'existing_de_keys_count': len(de_keys)
    }

    with open('.agents/worker_m1_locales/key_analysis.json', 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print(f"Total tr calls: {len(tr_calls)}")
    print(f"Distinct static keys: {len(keys_found)}")
    print(f"Dynamic tr calls: {len(dynamic_keys)}")
    print(f"Missing in de.json: {len(missing_in_de)}")

if __name__ == '__main__':
    analyze()
