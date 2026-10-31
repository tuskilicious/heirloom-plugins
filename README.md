# Heirloom plugins

Plugins for [Heirloom](https://github.com/tuskilicious/heirloom), the Epic Games launcher. Heirloom lists the ones here
and downloads one only when you install it: in the window under **Customize**, or in a terminal with
`heirloom plugins install <name>`.

| Plugin | What it does |
|---|---|
| `close-epic-launcher` | Closes the Epic Games Launcher when a game starts |
| `discord-presence` | Shows the game you're playing in your Discord status ([details](discord-presence/README.md)) |
| `library-worth` | Adds up what your library costs on the Epic Games Store |
| `notifications` | A desktop notification when a game finishes installing or updating |
| `power-plan` | Switches Windows to the High performance power plan while a game runs |

Plugins run inside Heirloom with access to your Epic account and files. Everything here is reviewed before it's
added; only install plugins from elsewhere if you trust them.

## Writing a plugin

A plugin is a folder with a `plugin.json` and a Python backend:

```json
{
  "name": "my-plugin",
  "common_name": "My plugin",
  "description": "What it does, in one line",
  "version": "1.0.0",
  "actions": [{"title": "Do the thing", "command": "my-command"}]
}
```

- `name` is the folder's name: lowercase letters, digits, `-` and `_`.
- `backend` is the Python file to load (default `main.py`); `"useBackend": false` for a plugin without one.
- `actions` are buttons in the window's Customize panel. Each runs `heirloom <command>`, a command the plugin adds,
  and the window shows what it printed.
- `themes` names theme files the plugin brings along.

The backend's `setup(plugin)` subscribes to Heirloom's events and adds commands:

```python
def setup(plugin):
    plugin.on('game_launching', lambda event: plugin.log.info(f'Starting {event.game.title}'))

    def hello(args, core):
        print(f'{len(core.lgd.get_installed_list())} games installed')

    plugin.command('my-command', hello, help='Says how many games are installed')
```

| Event | When | Fields |
|---|---|---|
| `game_launching` | Right before a game starts; handlers may change the command, environment and working directory | `app_name`, `game`, `command`, `environment`, `working_directory` |
| `game_exited` | When a game started by `heirloom launch` exits | `app_name`, `session` |
| `game_installed` | After a game is installed | `app_name`, `game` |
| `game_updated` | After a game is updated | `app_name`, `game`, `previous_version` |

To add a plugin here, put its folder in the repository, run `python build_index.py` to update `index.json`, and open
a pull request. CI runs `python build_index.py --check` and the tests in `tests`, against Heirloom from GitHub.

Licensed under the GPL 3.0, as Heirloom is.
