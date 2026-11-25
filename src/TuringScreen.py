"""TuringScreen.exe: standalone launcher + system monitor for the Turing 3.5" screen (rev. A).

TuringScreen.exe                 normal start (double click, shortcut):
                                   - "TuringScreen" task exists  -> run it (admin rights, no UAC prompt) and exit
                                   - no task yet                 -> ask admin rights once and run --install
TuringScreen.exe --install       create the task (logon autostart), disable UsbMonitor autostart,
                                 desktop shortcut, then start
TuringScreen.exe --uninstall     remove the task and the shortcut, re-enable UsbMonitor autostart
TuringScreen.exe --run           the monitor itself (started by the task): single instance,
                                 closes UsbMonitor, waits for the screen on USB, runs main.py
"""
import ctypes
import os
import runpy
import subprocess
import sys
import tempfile
import time
from xml.sax.saxutils import escape

TASK = 'TuringScreen'
TITLE = 'Экран Turing'
SHORTCUT = 'Экран Turing.lnk'
WAIT_SCREEN_SECONDS = 120
CREATE_NO_WINDOW = 0x08000000

EXE = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
HERE = os.path.dirname(EXE)
os.chdir(HERE)


def log(msg: str):
    try:
        with open(os.path.join(HERE, 'launcher.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%d.%m.%Y %H:%M:%S ') + msg + '\n')
    except Exception:
        pass


def message(text: str, warning: bool = False):
    flags = (0x30 if warning else 0x40) | 0x40000  # icon + topmost
    ctypes.windll.user32.MessageBoxW(None, text, TITLE, flags)


def run(args, timeout=60):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except Exception as e:
        return -1, repr(e)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def task_ok() -> bool:
    # the task must exist AND start this very exe (not an older version / another folder)
    code, out = run(['schtasks', '/Query', '/TN', TASK, '/XML'])
    return code == 0 and EXE.lower() in out.lower()


def elevate(arg: str):
    # ShellExecuteW returns > 32 on success
    r = ctypes.windll.shell32.ShellExecuteW(None, 'runas', EXE, arg, HERE, 1)
    return r > 32


# ---------------------------------------------------------------- install / uninstall
def task_xml() -> str:
    user = '%s\\%s' % (os.environ.get('USERDOMAIN', ''), os.environ.get('USERNAME', ''))
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Turing 3.5" screen: system monitor</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{escape(user)}</UserId>
      <Delay>PT10S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{escape(user)}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>Parallel</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(EXE)}</Command>
      <Arguments>--run</Arguments>
      <WorkingDirectory>{escape(HERE)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''


def shortcut(create: bool):
    if create:
        ps = ('$d=[Environment]::GetFolderPath("Desktop");'
              f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d "{SHORTCUT}"));'
              f'$s.TargetPath="{EXE}";$s.WorkingDirectory="{HERE}";$s.IconLocation="{EXE},0";$s.Save()')
    else:
        ps = f'$d=[Environment]::GetFolderPath("Desktop");Remove-Item -ErrorAction SilentlyContinue (Join-Path $d "{SHORTCUT}")'
    return run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps])


def install():
    path = os.path.join(tempfile.gettempdir(), 'TuringScreen_task.xml')
    with open(path, 'w', encoding='utf-16') as f:
        f.write(task_xml())
    code, out = run(['schtasks', '/Create', '/TN', TASK, '/XML', path, '/F'])
    try:
        os.remove(path)
    except OSError:
        pass
    log('install: task %s %s' % (code, out.strip()))
    if code != 0:
        message('Не удалось настроить автозапуск:\n' + out.strip(), warning=True)
        return False
    c2, _ = run(['schtasks', '/Change', '/TN', 'UsbMonitor', '/DISABLE'])
    log('install: UsbMonitor autostart disabled' if c2 == 0 else 'install: UsbMonitor task not found')
    c3, out3 = shortcut(True)
    log('install: shortcut %s %s' % (c3, out3.strip()))
    try:
        open(os.path.join(HERE, 'first_run.flag'), 'w').close()
    except OSError:
        pass
    message('Готово.\n\nПрограмма экрана будет запускаться сама при входе в Windows.\n'
            'Ярлык «Экран Turing» на рабочем столе запускает её вручную.\n'
            'Автозапуск штатной программы UsbMonitor отключён.\n\n'
            'Сейчас откроется окно настроек: выберите диски и вентилятор.\n'
            'Потом оно открывается щелчком по значку программы в трее.')
    run(['schtasks', '/Run', '/TN', TASK])
    return True


def uninstall():
    run(['schtasks', '/Delete', '/TN', TASK, '/F'])
    run(['schtasks', '/Change', '/TN', 'UsbMonitor', '/ENABLE'])
    shortcut(False)
    log('uninstall done')
    message('Автозапуск убран, ярлык удалён, автозапуск UsbMonitor включён обратно.')


# ---------------------------------------------------------------- monitor
def find_screen():
    from serial.tools.list_ports import comports
    for p in comports():
        if p.serial_number == 'USB35INCHIPSV2' or (p.vid == 0x1A86 and p.pid == 0x5722):
            return p.device
    return None


def select_background():
    # compose background.png: base + labels of the optional rows switched on in config.yaml
    try:
        import json
        import re
        with open(os.path.join(HERE, 'config.yaml'), encoding='utf-8') as f:
            cfg = f.read()

        def val(key):
            m = re.search(r'^\s*%s:\s*(.*?)\s*(#.*)?$' % key, cfg, re.M)
            return m.group(1).strip().strip('"\'') if m else ''

        theme = os.path.join(HERE, 'res', 'themes', 'Grid3_2SSD')
        from PIL import Image, ImageDraw, ImageFont
        bg = Image.open(os.path.join(theme, 'background_base.png')).convert('RGBA')
        ram_on = val('RAM_TEMP').lower() in ('true', '1', 'yes')
        if ram_on:
            bg.alpha_composite(Image.open(os.path.join(theme, 'overlay_ramtemp.png')).convert('RGBA'))
        with open(os.path.join(theme, 'extra_rows.json'), encoding='utf-8') as f:
            spec = json.load(f)
        font = ImageFont.truetype(os.path.join(HERE, 'res', spec['font']), spec['size'])
        d = ImageDraw.Draw(bg)
        shown = []
        for n, row in enumerate(spec['rows'], 1):
            if val('EXTRA_SENSOR_%d' % n) in ('', '-'):
                continue
            lab = re.sub(r'[^A-Za-z0-9 ._-]', '', val('EXTRA_LABEL_%d' % n))[:7] or 'air'
            col = tuple(spec['color'])
            d.text((row['label_x'], row['baseline']), lab + ':', font=font, fill=col, anchor='ls')
            d.text((row['unit_x'], row['baseline']), '°C', font=font, fill=col, anchor='ls')
            shown.append(lab)
        bg.convert('RGB').save(os.path.join(theme, 'background.png'))
        log('background: ram=%s extra=%s' % (ram_on, shown))
    except Exception as e:
        log('background composition failed: %r' % e)


def monitor():
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    global _mutex
    _mutex = kernel32.CreateMutexW(None, False, 'Local\\TuringScreenMonitor')
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        log('already running, exit')
        message('Программа экрана уже работает.\nЗначок в трее: щелчок открывает настройки, правая кнопка > Выход.')
        return

    log('start')
    code, _ = run(['taskkill', '/F', '/IM', 'UsbMonitor.exe'])
    if code == 0:
        log('UsbMonitor.exe closed')
        time.sleep(3)

    if not os.environ.get('TURING_NO_PORT_WAIT'):
        port = None
        deadline = time.monotonic() + WAIT_SCREEN_SECONDS
        while time.monotonic() < deadline:
            try:
                port = find_screen()
            except Exception as e:
                log('port scan error: %r' % e)
            if port:
                break
            time.sleep(1)
        if not port:
            log('screen not found')
            message('Экран не найден на USB.\n\nВыньте USB-кабель экрана на полминуты, вставьте обратно '
                    'и запустите ярлык «Экран Turing» ещё раз.', warning=True)
            return
        log('screen on %s' % port)
        time.sleep(2)

    select_background()
    sys.argv = [EXE]
    try:
        runpy.run_module('main', run_name='__main__', alter_sys=True)
    except SystemExit:
        pass
    except Exception as e:
        log('main crashed: %r' % e)
        message('Программа экрана остановилась с ошибкой:\n%r\n\nПодробности в log.log' % e, warning=True)
    log('stop')


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg == '--run':
        monitor()
    elif arg == '--install':
        if is_admin():
            install()
        elif not elevate('--install'):
            message('Для первой настройки нужны права администратора.', warning=True)
    elif arg == '--uninstall':
        if is_admin():
            uninstall()
        else:
            elevate('--uninstall')
    else:
        if task_ok():
            code, out = run(['schtasks', '/Run', '/TN', TASK])
            if code != 0:
                log('task run failed: %s' % out.strip())
                message('Не удалось запустить программу экрана:\n' + out.strip(), warning=True)
        elif is_admin():
            install()
        elif not elevate('--install'):
            message('Для первой настройки нужны права администратора.', warning=True)
