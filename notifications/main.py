"""
A desktop notification when a game finishes installing or updating, from the window's updates too. Windows
only shows it with notifications turned on, in Settings, System, Notifications.
"""
import os
import subprocess
import sys

# a Windows toast, from the HL_* variables so no game title is ever part of the script. It comes from Heirloom,
# which Windows knows of once its app id is registered for the current user (with the icon in HL_ICON, if any)
TOAST = '''
$app = 'Heirloom.Heirloom'
$key = "HKCU:\\Software\\Classes\\AppUserModelId\\$app"
if (-not (Test-Path $key)) {
    New-Item -Path $key -Force > $null
    New-ItemProperty -Path $key -Name DisplayName -Value 'Heirloom' > $null
    if ($env:HL_ICON) { New-ItemProperty -Path $key -Name IconUri -Value $env:HL_ICON > $null }
}
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$toast = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
    [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$text = $toast.GetElementsByTagName('text')
$text.Item(0).AppendChild($toast.CreateTextNode($env:HL_TITLE)) > $null
$text.Item(1).AppendChild($toast.CreateTextNode($env:HL_TEXT)) > $null
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show(
    [Windows.UI.Notifications.ToastNotification]::new($toast))
'''


def notify(title, text):
    if sys.platform == 'win32':
        command = ['powershell', '-NoProfile', '-NonInteractive', '-Command', TOAST]
        # heirloom.exe, for the icon, when Heirloom runs as the Windows executable
        icon = sys.executable if getattr(sys, 'frozen', False) else ''
        options = {'env': os.environ | {'HL_TITLE': title, 'HL_TEXT': text, 'HL_ICON': icon},
                   'creationflags': subprocess.CREATE_NO_WINDOW}
    elif sys.platform == 'darwin':
        command = ['osascript', '-e', 'on run argv', '-e',
                   'display notification (item 2 of argv) with title (item 1 of argv)', '-e', 'end run', title, text]
        options = {}
    else:
        command, options = ['notify-send', '--app-name=Heirloom', title, text], {}
    subprocess.run(command, capture_output=True, timeout=30, check=True, **options)


def setup(plugin):
    def send(title, text):
        try:
            notify(title, text)
        except (OSError, subprocess.SubprocessError) as e:
            plugin.log.warning(f'Could not show a notification: {e!r}')

    plugin.on('game_installed', lambda event: send(f'{event.game.title} is installed', 'Ready to play.'))
    plugin.on('game_updated', lambda event: send(f'{event.game.title} is updated',
                                                 f'Version {event.game.version}, ready to play.'))
