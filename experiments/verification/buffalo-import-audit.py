import ast
import importlib.util
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2] / 'experiments/work/buffalo'
search_roots = [root / 'flsim/FLSim', root / 'flsim/src', root / 'olympia', root / 'rlwe_sa']
sys.path[:0] = [str(path) for path in search_roots]
imports = {}
for source in root.rglob('*.py'):
    if '.git' in source.parts or any(part.startswith('bazel-') for part in source.parts):
        continue
    try:
        tree = ast.parse(source.read_text())
    except (SyntaxError, UnicodeDecodeError):
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            imports.setdefault(name, []).append(f'{source.relative_to(root)}:{node.lineno}')
for name, locations in sorted(imports.items()):
    top = name.split('.')[0]
    local = next((path / top for path in search_roots if (path / top).is_dir()), None)
    if local:
        relative = Path(*name.split('.'))
        found = any((path / relative).is_dir() or (path / relative).with_suffix('.py').exists() for path in search_roots)
        if not found:
            print('MISSING_LOCAL', name, *locations)
    elif importlib.util.find_spec(top) is None:
        print('MISSING_EXTERNAL', name, *locations)
print('Audited absolute imports:', len(imports))
