"""Interface language for TuringScreen: Russian or English.

LANGUAGE in config.yaml: auto (default, by the Windows display language), ru or en.
"""
import os
import re
import sys

_lang = None


def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def setting() -> str:
    try:
        with open(os.path.join(_app_dir(), 'config.yaml'), encoding='utf-8') as f:
            m = re.search(r'^\s*LANGUAGE:\s*"?([A-Za-z]*)"?', f.read(), re.M)
        v = (m.group(1) if m else 'auto').lower()
        return v if v in ('ru', 'en') else 'auto'
    except Exception:
        return 'auto'


def windows_is_russian() -> bool:
    try:
        import ctypes
        return (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x19
    except Exception:
        return False


def lang() -> str:
    global _lang
    if _lang is None:
        s = setting()
        _lang = s if s != 'auto' else ('ru' if windows_is_russian() else 'en')
    return _lang


def t(key: str) -> str:
    d = STR.get(lang(), STR['en'])
    return d.get(key) or STR['en'].get(key) or key


STR = {
    'ru': {
        'title': 'Экран Turing',
        'shortcut': 'Экран Turing.lnk',
        'tray_title': 'Экран Turing (щелчок: настройки)',
        'tray_settings': 'Настройки',
        'tray_exit': 'Выход',
        'msg_autostart_failed': 'Не удалось настроить автозапуск:\n',
        'msg_installed': ('Готово.\n\nПрограмма экрана будет запускаться сама при входе в Windows.\n'
                          'Ярлык «Экран Turing» на рабочем столе запускает её вручную.\n'
                          'Автозапуск штатной программы UsbMonitor отключён.\n\n'
                          'Сейчас откроется окно настроек: выберите диски и вентилятор.\n'
                          'Потом оно открывается щелчком по значку программы в трее.'),
        'msg_uninstalled': 'Автозапуск убран, ярлык удалён, автозапуск UsbMonitor включён обратно.',
        'msg_running': 'Программа экрана уже работает.\nЗначок в трее: щелчок открывает настройки, правая кнопка > Выход.',
        'msg_no_screen': ('Экран не найден на USB.\n\nВыньте USB-кабель экрана на полминуты, вставьте обратно '
                          'и запустите ярлык «Экран Turing» ещё раз.'),
        'msg_crashed': 'Программа экрана остановилась с ошибкой:\n%r\n\nПодробности в log.log',
        'msg_need_admin': 'Для первой настройки нужны права администратора.',
        'msg_run_failed': 'Не удалось запустить программу экрана:\n',
        'auto': 'Авто',
        'none': 'Не показывать',
        'used_pct': 'занято %.0f %%',
        'rpm': '%s   (%.0f об/мин)',
        'win_title': 'Экран Turing: настройки',
        'disks': 'Диски',
        'disks_hint': 'Рядом с каждым диском его текущая температура и заполненность. '
                      '«Авто»: первый и второй диск по порядку Windows.',
        'fan': 'Вентилятор процессора',
        'sensor': 'Датчик:',
        'fan_hint': 'Выберите датчик, обороты которого похожи на обороты кулера процессора.',
        'memory': 'Память',
        'ram_check': 'Показывать температуру памяти (DDR)',
        'ram_found': 'Найдено датчиков на планках: %d (%s). На экране: temp 1 и temp 2, первые две планки.',
        'ram_none': 'Датчик на планках не найден, на экране будут прочерки. '
                    'Датчик есть на всех DDR5, на большинстве DDR4 его нет.',
        'extra': 'Свой датчик температуры',
        'extra_hint': 'Слева подпись на экране (латиницей, до 7 знаков), справа датчик. '
                      'Какой датчик ваш? Зажмите его в пальцах на полминуты и нажмите «Обновить»: '
                      'у нужного температура заметно вырастет.',
        'refresh': 'Обновить',
        'screen': 'Экран',
        'brightness': 'Яркость:',
        'bright_hint': 'Выше 50 % экран заметно греется.',
        'reverse': 'Повернуть изображение на 180°',
        'autostart': 'Запускать при входе в Windows',
        'language': 'Язык / Language:',
        'lang_auto': 'Авто (как в Windows)',
        'save_failed': 'Не удалось сохранить config.yaml:\n%r',
        'cancel': 'Отмена',
        'save': 'Сохранить',
    },
    'en': {
        'title': 'Turing Screen',
        'shortcut': 'Turing Screen.lnk',
        'tray_title': 'Turing Screen (click: settings)',
        'tray_settings': 'Settings',
        'tray_exit': 'Exit',
        'msg_autostart_failed': 'Could not set up autostart:\n',
        'msg_installed': ('Done.\n\nThe screen program will start automatically when you sign in to Windows.\n'
                          'The "Turing Screen" shortcut on the desktop starts it manually.\n'
                          'Autostart of the stock UsbMonitor program is disabled.\n\n'
                          'The settings window will open now: choose your disks and fan.\n'
                          'Later it opens with a click on the program icon in the tray.'),
        'msg_uninstalled': 'Autostart removed, shortcut deleted, UsbMonitor autostart re-enabled.',
        'msg_running': 'The screen program is already running.\nTray icon: click for settings, right click > Exit.',
        'msg_no_screen': ('The screen was not found on USB.\n\nUnplug the screen USB cable for half a minute, '
                          'plug it back in and start the "Turing Screen" shortcut again.'),
        'msg_crashed': 'The screen program stopped with an error:\n%r\n\nDetails in log.log',
        'msg_need_admin': 'Administrator rights are needed for the first setup.',
        'msg_run_failed': 'Could not start the screen program:\n',
        'auto': 'Auto',
        'none': 'Do not show',
        'used_pct': '%.0f %% used',
        'rpm': '%s   (%.0f rpm)',
        'win_title': 'Turing Screen: settings',
        'disks': 'Disks',
        'disks_hint': 'Each disk shows its current temperature and used space. '
                      '"Auto": the first and second disk in Windows order.',
        'fan': 'CPU fan',
        'sensor': 'Sensor:',
        'fan_hint': 'Choose the sensor whose speed matches your CPU cooler.',
        'memory': 'Memory',
        'ram_check': 'Show memory (DDR) temperature',
        'ram_found': 'Module sensors found: %d (%s). On screen: temp 1 and temp 2, the first two modules.',
        'ram_none': 'No module sensor found, the screen will show dashes. '
                    'All DDR5 modules have one, most DDR4 modules do not.',
        'extra': 'Custom temperature sensor',
        'extra_hint': 'Left: label on the screen (Latin letters, up to 7 characters); right: the sensor. '
                      'Which one is yours? Hold the probe in your fingers for half a minute and press '
                      '"Refresh": its temperature will rise noticeably.',
        'refresh': 'Refresh',
        'screen': 'Screen',
        'brightness': 'Brightness:',
        'bright_hint': 'Above 50 % the screen gets noticeably warm.',
        'reverse': 'Rotate the image 180°',
        'autostart': 'Start when signing in to Windows',
        'language': 'Язык / Language:',
        'lang_auto': 'Auto (as in Windows)',
        'save_failed': 'Could not save config.yaml:\n%r',
        'cancel': 'Cancel',
        'save': 'Save',
    },
}
