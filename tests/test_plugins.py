"""The plugins of this repository, loaded by Heirloom's plugin manager as they are when installed."""
import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest

from heirloom.models.game import InstalledGame, PlaytimeSession
from heirloom.plugins import GameExited, GameInstalled, GameLaunching, PluginManager

ROOT = Path(__file__).parent.parent
GAME = InstalledGame(app_name='Fish', install_path='C:/Games/Fish', title='Fish Game', version='2')


def load_store(tmp_path):
    """Every plugin here but Discord's (tested on its own), enabled and loaded"""
    folder = tmp_path / 'plugins'
    for plugin in ('close-epic-launcher', 'library-worth', 'notifications', 'power-plan'):
        shutil.copytree(ROOT / plugin, folder / plugin)
    manager = PluginManager(folder)
    for name in manager.discover():
        manager.set_enabled(name, True)
    manager.load(argparse.ArgumentParser().add_subparsers())
    return manager


def test_store_plugins_load(tmp_path):
    manager = load_store(tmp_path)
    assert set(manager.discover()) == {'notifications', 'power-plan', 'close-epic-launcher', 'library-worth'}
    assert manager.errors == {}


def test_notification_names_the_game(tmp_path, monkeypatch):
    shown = []
    monkeypatch.setattr('subprocess.run', lambda command, **options: shown.append((command, options.get('env', {}))))
    load_store(tmp_path).emit(GameInstalled('Fish', GAME))
    (command, env), = shown
    assert 'Fish Game is installed' in [*command, *env.values()], 'the title, outside any script'


@pytest.mark.skipif(sys.platform != 'win32', reason='power plans are Windows only')
def test_power_plan_switches_back_after_playing(tmp_path, monkeypatch):
    calls = []

    def powercfg(command, **options):
        calls.append(command)
        return type('Result', (), {'stdout': 'Power Scheme GUID: 381b4222-f694-41f0-9685-ff5bb260df2e  (Balanced)',
                                   'returncode': 1})()

    monkeypatch.setattr('subprocess.run', powercfg)
    manager = load_store(tmp_path)
    manager.emit(GameLaunching('Fish', GAME, ['fish.exe'], {}, 'C:/Games/Fish'))
    manager.emit(GameExited('Fish', PlaytimeSession(datetime.now(), datetime.now(), 0)))
    plan_calls = [call[1:] for call in calls if call[0] == 'powercfg']
    assert plan_calls == [['/getactivescheme'], ['/setactive', 'SCHEME_MIN'],
                          ['/setactive', '381b4222-f694-41f0-9685-ff5bb260df2e']]


def test_library_worth(tmp_path, monkeypatch, capsys):
    def offer(title, kind, full, today):
        return {'title': title, 'offerType': kind, 'price': {'totalPrice': {
            'originalPrice': full, 'discountPrice': today, 'currencyCode': 'GBP', 'currencyInfo': {'decimals': 2}}}}

    asked = []

    def post(url, json, **options):
        asked.append(json['query'])
        catalog = {'n0': {'elements': [offer('Fish Game Soundtrack', 'ADD_ON', 499, 499),
                                       offer('Fish Game', 'BASE_GAME', 2999, 1499)]},
                   'n1': {'elements': [offer('Goo Deluxe', 'EDITION', 3999, 3999)]}}
        return type('Response', (), {'raise_for_status': lambda self: None,
                                     'json': lambda self: {'data': {'Catalog': catalog}}})()

    monkeypatch.setattr('requests.post', post)
    games = {'Fish': ('Fish Game', 'fishns', False), 'FishOST': ('fish game soundtrack', 'fishns', True),
             'Goo': ('World of Goo', 'goons', False), 'Odd': ('Odd', 'not-hex"}', False)}
    lgd = type('Lgd', (), {'get_game_app_names': lambda self: list(games), 'get_game_meta': lambda self, name: type(
        'Game', (), {'app_title': games[name][0], 'namespace': games[name][1], 'is_dlc': games[name][2]})()})()
    core = type('Core', (), {'lgd': lgd, 'country_code': 'GB', 'language_code': 'en'})()

    manager = load_store(tmp_path)
    plugin, run = manager.commands['worth']
    run(argparse.Namespace(top=1, json=True), core)
    output = capsys.readouterr().out
    assert 'not-hex' not in asked[0], "only Epic's ids go into the query"
    assert '34.98 GBP' in output and '19.98 GBP' in output, "base game and DLC, at full and today's price"
    assert '29.99 GBP  Fish Game' in output
    assert 'not in your country: 2 (Odd, World of Goo)' in output
