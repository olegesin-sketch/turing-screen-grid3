"""Settings window for TuringScreen (opened from the tray icon menu, runs inside the monitor process).

Lets the user pick, with live sensor values shown for identification:
  - which physical disk is "SSD 1" and "SSD 2";
  - which motherboard fan is the CPU fan;
  - brightness (applied immediately), screen rotation 180 degrees, autostart.
Disk and fan choices apply immediately; rotation and the RAM temperature row need a restart (done automatically).
"""
import os
import re
import subprocess
import sys
import threading

CREATE_NO_WINDOW = 0x08000000
TASK = 'TuringScreen'
from i18n import t as _

AUTO = _('auto')
NONE = _('none')

_window_open = threading.Lock()


# ------------------------------------------------------------------ data from the running monitor
def _lhm():
    return sys.modules.get('library.sensors.sensors_librehardwaremonitor')


def _val(hw, type_name, names=None):
    lhm = _lhm()
    try:
        st = getattr(lhm.Hardware.SensorType, type_name)
        for s in hw.Sensors:
            if s.SensorType == st and s.Value is not None and (names is None or str(s.Name) in names):
                return float(s.Value)
    except Exception:
        pass
    return None


def list_disks():
    """[(model name, description with live values)]"""
    out = []
    lhm = _lhm()
    if lhm is not None:
        try:
            for h in lhm.handle.Hardware:
                if h.HardwareType != lhm.Hardware.HardwareType.Storage:
                    continue
                h.Update()
                t = _val(h, 'Temperature', ['Composite Temperature', 'Temperature', 'Temperature #1'])
                u = _val(h, 'Load', ['Used Space'])
                info = []
                if t is not None:
                    info.append('%.0f °C' % t)
                if u is not None:
                    info.append(_('used_pct') % u)
                name = str(h.Name).strip()
                out.append((name, name + ('   (' + ', '.join(info) + ')' if info else '')))
        except Exception:
            pass
    if not out:  # fallback without LibreHardwareMonitor: models from Windows
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-Command',
                                '(Get-CimInstance Win32_DiskDrive).Model'],
                               capture_output=True, text=True, timeout=20, creationflags=CREATE_NO_WINDOW)
            out = [(m.strip(), m.strip()) for m in r.stdout.splitlines() if m.strip()]
        except Exception:
            pass
    return out


def list_fans():
    """[(sensor name, description with live rpm)]"""
    out = []
    lhm = _lhm()
    if lhm is None:
        return out
    try:
        for h in lhm.handle.Hardware:
            if h.HardwareType != lhm.Hardware.HardwareType.Motherboard:
                continue
            h.Update()
            for sh in h.SubHardware:
                sh.Update()
                for s in sh.Sensors:
                    if s.SensorType == lhm.Hardware.SensorType.Fan and s.Value is not None:
                        out.append((str(s.Name), _('rpm') % (s.Name, float(s.Value))))
    except Exception:
        pass
    return out


# ------------------------------------------------------------------ config.yaml
def _config_path():
    from library import config
    return os.path.join(str(config.MAIN_DIRECTORY), 'config.yaml')


def _set_line(text, key, value_repr):
    pat = re.compile(r'^(\s*%s:\s*)(.*?)(\s*#.*)?$' % re.escape(key), re.M)
    if pat.search(text):
        return pat.sub(lambda m: m.group(1) + value_repr + (m.group(3) or ''), text, count=1)
    # key absent: add it to the "config:" section
    return re.sub(r'^config:\s*$', 'config:\n  %s: %s' % (key, value_repr), text, count=1, flags=re.M)


def save_config(values: dict):
    path = _config_path()
    with open(path, encoding='utf-8') as f:
        text = f.read()
    for key, v in values.items():
        if isinstance(v, bool):
            rep = 'true' if v else 'false'
        elif isinstance(v, int):
            rep = str(v)
        else:
            rep = '"%s"' % str(v).replace('"', '')
        text = _set_line(text, key, rep)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def autostart_enabled():
    try:
        r = subprocess.run(['schtasks', '/Query', '/TN', TASK, '/XML'], capture_output=True, text=True,
                           timeout=20, creationflags=CREATE_NO_WINDOW)
        return r.returncode == 0 and '<Enabled>false</Enabled>' not in r.stdout.split('<Settings>')[-1]
    except Exception:
        return True


def set_autostart(on: bool):
    subprocess.run(['schtasks', '/Change', '/TN', TASK, '/ENABLE' if on else '/DISABLE'],
                   capture_output=True, timeout=20, creationflags=CREATE_NO_WINDOW)


# ------------------------------------------------------------------ window
def open_settings(restart_cb=None):
    """Open the window in its own thread (no-op if it is already open)."""
    if not _window_open.acquire(blocking=False):
        return
    threading.Thread(target=_run, args=(restart_cb,), daemon=True).start()


def _run(restart_cb):
    try:
        _window(restart_cb)
    finally:
        _window_open.release()


def _window(restart_cb):
    import tkinter as tk
    from tkinter import ttk, messagebox
    from library import config

    cfg = config.CONFIG_DATA['config']
    disp = config.CONFIG_DATA['display']

    disks = list_disks()
    fans = list_fans()

    root = tk.Tk()
    root.title(_('win_title'))
    root.resizable(False, False)
    try:
        root.iconbitmap(os.path.join(str(config.MAIN_DIRECTORY), 'res', 'icons', 'monitor-icon-17865', 'icon.ico'))
    except Exception:
        pass
    root.attributes('-topmost', True)
    root.after(500, lambda: root.attributes('-topmost', False))

    pad = {'padx': 10, 'pady': 6}
    frm = ttk.Frame(root, padding=14)
    frm.grid(sticky='nsew')

    def choice_list(items, extra):
        labels = list(extra) + [d for _, d in items]
        values = [''] * len(extra) + [n for n, _ in items]
        if NONE in extra:
            values[extra.index(NONE)] = '-'
        return labels, values

    def current_label(labels, values, current):
        if current is None or current == '':
            return labels[0]
        if current == '-' and NONE in labels:
            return NONE
        for lab, val in zip(labels, values):
            if val and current.lower() in val.lower():
                return lab
        return labels[0]

    # disks
    ttk.Label(frm, text=_('disks'), font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w')
    d1_labels, d1_values = choice_list(disks, [AUTO])
    d2_labels, d2_values = choice_list(disks, [AUTO, NONE])
    ttk.Label(frm, text='SSD 1:').grid(row=1, column=0, sticky='w', **pad)
    ssd1 = ttk.Combobox(frm, values=d1_labels, state='readonly', width=58)
    ssd1.set(current_label(d1_labels, d1_values, cfg.get('SSD1_MATCH', '')))
    ssd1.grid(row=1, column=1, sticky='w', **pad)
    ttk.Label(frm, text='SSD 2:').grid(row=2, column=0, sticky='w', **pad)
    ssd2 = ttk.Combobox(frm, values=d2_labels, state='readonly', width=58)
    ssd2.set(current_label(d2_labels, d2_values, cfg.get('SSD2_MATCH', '')))
    ssd2.grid(row=2, column=1, sticky='w', **pad)
    ttk.Label(frm, text=_('disks_hint'),
              foreground='#666', wraplength=430).grid(row=3, column=1, sticky='w', padx=10)

    # fan
    ttk.Label(frm, text=_('fan'), font=('Segoe UI', 10, 'bold')).grid(
        row=4, column=0, columnspan=2, sticky='w', pady=(14, 0))
    f_labels, f_values = choice_list(fans, [AUTO])
    ttk.Label(frm, text=_('sensor')).grid(row=5, column=0, sticky='w', **pad)
    fan = ttk.Combobox(frm, values=f_labels, state='readonly', width=58)
    cur_fan = cfg.get('CPU_FAN_SENSOR', '')
    fan.set(next((lab for lab, val in zip(f_labels, f_values) if val and val.lower() == str(cur_fan).lower()),
                 f_labels[0]))
    fan.grid(row=5, column=1, sticky='w', **pad)
    ttk.Label(frm, text=_('fan_hint'),
              foreground='#666', wraplength=430).grid(row=6, column=1, sticky='w', padx=10)

    # memory temperature
    ttk.Label(frm, text=_('memory'), font=('Segoe UI', 10, 'bold')).grid(
        row=7, column=0, columnspan=2, sticky='w', pady=(14, 0))
    ram_initial = str(cfg.get('RAM_TEMP', False)).strip().lower() in ('true', '1', 'yes')
    ram = tk.BooleanVar(value=ram_initial)
    ttk.Checkbutton(frm, text=_('ram_check'), variable=ram).grid(
        row=8, column=1, sticky='w', **pad)
    try:
        from library.sensors.sensors_custom import read_ram_temps
        temps = read_ram_temps()
    except Exception:
        temps = []
    if temps:
        ram_hint = (_('ram_found')
                    % (len(temps), ', '.join('%.0f °C' % t for t in temps)))
    else:
        ram_hint = _('ram_none')
    ttk.Label(frm, text=ram_hint, foreground='#666', wraplength=430).grid(row=9, column=1, sticky='w', padx=10)

    # user temperature sensors
    ttk.Label(frm, text=_('extra'), font=('Segoe UI', 10, 'bold')).grid(
        row=10, column=0, columnspan=2, sticky='w', pady=(14, 0))
    temp_items = []

    def load_temps():
        try:
            from library.sensors.sensors_custom import list_temperature_sensors
            temp_items[:] = list_temperature_sensors()
        except Exception:
            temp_items[:] = []

    load_temps()
    extra = []  # (label entry var, combobox, ids list, initial id)
    for n in (1,):
        rowf = ttk.Frame(frm)
        rowf.grid(row=10 + n, column=1, sticky='w', **pad)
        ttk.Label(frm, text=_('sensor')).grid(row=10 + n, column=0, sticky='w', **pad)
        lab = tk.StringVar(value=str(cfg.get('EXTRA_LABEL_%d' % n, 'air') or 'air'))
        ttk.Entry(rowf, textvariable=lab, width=8).pack(side='left')
        cb = ttk.Combobox(rowf, state='readonly', width=46)
        cb.pack(side='left', padx=(8, 0))
        ids = []
        cur = str(cfg.get('EXTRA_SENSOR_%d' % n, '') or '')
        extra.append([lab, cb, ids, cur])

    def fill_temps(keep_current=True):
        for item in extra:
            lab, cb, ids, cur = item
            if keep_current and cb.current() >= 0 and ids:
                cur = ids[cb.current()]
            ids[:] = [''] + [i for i, _, _, _ in temp_items]
            cb['values'] = [NONE] + ['%s, %s   (%.1f °C)' % (nm, hw, v) for _, hw, nm, v in temp_items]
            cb.current(ids.index(cur) if cur in ids else 0)

    fill_temps(keep_current=False)
    for item in extra:
        item[3] = item[2][item[1].current()] if item[1].current() >= 0 else ''

    hint = ttk.Frame(frm)
    hint.grid(row=12, column=1, sticky='w', padx=10)
    ttk.Label(hint, text=_('extra_hint'),
              foreground='#666', wraplength=330).pack(side='left')
    ttk.Button(hint, text=_('refresh'), command=lambda: (load_temps(), fill_temps())).pack(side='left', padx=8)

    # screen
    ttk.Label(frm, text=_('screen'), font=('Segoe UI', 10, 'bold')).grid(
        row=13, column=0, columnspan=2, sticky='w', pady=(14, 0))
    ttk.Label(frm, text=_('brightness')).grid(row=14, column=0, sticky='w', **pad)
    bright_frame = ttk.Frame(frm)
    bright_frame.grid(row=14, column=1, sticky='w', **pad)
    bright = tk.IntVar(value=int(disp.get('BRIGHTNESS', 20)))
    bright_lbl = ttk.Label(bright_frame, width=5)

    def on_bright(_=None):
        v = int(float(bright.get()))
        bright.set(v)
        bright_lbl.config(text='%d %%' % v)
        try:
            from library.display import display
            display.lcd.SetBrightness(v)
        except Exception:
            pass

    ttk.Scale(bright_frame, from_=0, to=100, variable=bright, length=300,
              command=lambda _=None: bright_lbl.config(text='%d %%' % int(float(bright.get())))
              ).pack(side='left')
    bright_lbl.pack(side='left', padx=8)
    bright_lbl.config(text='%d %%' % bright.get())
    bright_frame.bind_all('<ButtonRelease-1>', lambda e: on_bright() if e.widget.winfo_class() == 'TScale' else None)
    ttk.Label(frm, text=_('bright_hint'), foreground='#666').grid(row=15, column=1, sticky='w', padx=10)

    reverse = tk.BooleanVar(value=bool(disp.get('DISPLAY_REVERSE', False)))
    ttk.Checkbutton(frm, text=_('reverse'), variable=reverse).grid(
        row=16, column=1, sticky='w', **pad)

    autostart_initial = autostart_enabled()
    autostart = tk.BooleanVar(value=autostart_initial)
    ttk.Checkbutton(frm, text=_('autostart'), variable=autostart).grid(
        row=17, column=1, sticky='w', **pad)

    import i18n
    lang_values = ['auto', 'ru', 'en']
    lang_labels = [_('lang_auto'), 'Русский', 'English']
    lang_initial = i18n.setting()
    ttk.Label(frm, text=_('language')).grid(row=18, column=0, sticky='w', **pad)
    lang_cb = ttk.Combobox(frm, values=lang_labels, state='readonly', width=24)
    lang_cb.current(lang_values.index(lang_initial))
    lang_cb.grid(row=18, column=1, sticky='w', **pad)

    def save():
        m1 = d1_values[d1_labels.index(ssd1.get())] if ssd1.get() in d1_labels else ''
        m2 = d2_values[d2_labels.index(ssd2.get())] if ssd2.get() in d2_labels else ''
        fv = f_values[f_labels.index(fan.get())] if fan.get() in f_labels else ''
        b = int(float(bright.get()))
        rev = bool(reverse.get())
        ram_on = bool(ram.get())
        extra_vals = {}
        extra_changed = False
        for n, (lab, cb, ids, initial) in enumerate(extra, 1):
            sid = ids[cb.current()] if cb.current() >= 0 and ids else ''
            label = re.sub(r'[^A-Za-z0-9 ._-]', '', lab.get())[:7] or 'air'
            extra_vals['EXTRA_SENSOR_%d' % n] = sid
            extra_vals['EXTRA_LABEL_%d' % n] = label
            if bool(sid) != bool(initial) or (sid and label != str(cfg.get('EXTRA_LABEL_%d' % n, '')) ):
                extra_changed = True
        lang_new = lang_values[lang_cb.current()] if lang_cb.current() >= 0 else 'auto'
        need_restart = (rev != bool(disp.get('DISPLAY_REVERSE', False)) or ram_on != ram_initial
                        or extra_changed or lang_new != lang_initial)
        try:
            save_config({'SSD1_MATCH': m1, 'SSD2_MATCH': m2, 'CPU_FAN_SENSOR': fv,
                         'BRIGHTNESS': b, 'DISPLAY_REVERSE': rev, 'RAM_TEMP': ram_on,
                         'LANGUAGE': lang_new, **extra_vals})
        except Exception as e:
            messagebox.showerror(_('title'), _('save_failed') % e, parent=root)
            return
        # apply at once (custom sensors read these values on every update)
        cfg['SSD1_MATCH'], cfg['SSD2_MATCH'], cfg['CPU_FAN_SENSOR'] = m1, m2, fv
        cfg['RAM_TEMP'] = ram_on
        cfg.update(extra_vals)
        disp['BRIGHTNESS'] = b
        if autostart.get() != autostart_initial:
            set_autostart(bool(autostart.get()))
        root.destroy()
        if need_restart and restart_cb:
            restart_cb()

    btns = ttk.Frame(frm)
    btns.grid(row=19, column=0, columnspan=2, sticky='e', pady=(16, 0))

    def cancel():
        try:  # restore brightness if it was changed but not saved
            from library.display import display
            display.lcd.SetBrightness(int(disp.get('BRIGHTNESS', 20)))
        except Exception:
            pass
        root.destroy()

    ttk.Button(btns, text=_('cancel'), command=cancel).pack(side='right', padx=4)
    ttk.Button(btns, text=_('save'), command=save).pack(side='right', padx=4)
    root.protocol('WM_DELETE_WINDOW', cancel)
    root.mainloop()


def restart_program():
    """Ask Windows to start the monitor again in a few seconds (after this process has exited)."""
    subprocess.Popen('cmd /c ping -n 5 127.0.0.1 >nul & schtasks /Run /TN "%s"' % TASK,
                     creationflags=CREATE_NO_WINDOW | 0x00000008, close_fds=True)  # DETACHED_PROCESS
