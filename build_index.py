"""
Writes index.json, the list of plugins Heirloom offers to install, from each folder's plugin.json.
With --check it writes nothing and fails if a plugin.json is broken or index.json is out of date, as CI runs it.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
NAME = re.compile(r'[a-z0-9][a-z0-9_-]*')
COMMAND = re.compile(r'[a-z0-9][a-z0-9-]*')


def read(folder: Path) -> dict:
    data = json.loads((folder / 'plugin.json').read_text(encoding='utf-8'))
    name = data.get('name')
    if not isinstance(name, str) or not NAME.fullmatch(name) or name != folder.name:
        raise ValueError(f'"name" must be the folder\'s name in lowercase letters, digits, "-" and "_", got {name!r}')
    if not data.get('common_name') or not data.get('description') or not data.get('version'):
        raise ValueError('"common_name", "description" and "version" are needed for the store')
    backend = folder / (data.get('backend') or 'main.py')
    if data.get('useBackend', True) and not backend.is_file():
        raise ValueError(f'no backend at {backend.name}')
    for action in data.get('actions', []):
        if not isinstance(action.get('title'), str) or not COMMAND.fullmatch(str(action.get('command'))):
            raise ValueError(f'an action needs a "title" and a "command" of lowercase letters, digits and "-", '
                             f'got {action!r}')
    return {'name': name, 'common_name': data['common_name'], 'description': data['description'],
            'version': data['version'], 'folder': folder.name}


def main() -> int:
    plugins, failed = [], False
    for folder in sorted(path for path in ROOT.iterdir() if (path / 'plugin.json').is_file()):
        try:
            plugins.append(read(folder))
        except (ValueError, OSError) as e:
            print(f'{folder.name}: {e}', file=sys.stderr)
            failed = True
    index = json.dumps({'plugins': plugins}, indent=2, ensure_ascii=False) + '\n'
    if '--check' in sys.argv:
        if (ROOT / 'index.json').read_text(encoding='utf-8') != index:
            print('index.json is out of date: run python build_index.py', file=sys.stderr)
            failed = True
    elif not failed:
        (ROOT / 'index.json').write_text(index, encoding='utf-8')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
