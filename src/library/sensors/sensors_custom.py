# SPDX-License-Identifier: GPL-3.0-or-later
#
# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/
#
# Copyright (C) 2021 Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file allows to add custom data source as sensors and display them in System Monitor themes
# There is no limitation on how much custom data source classes can be added to this file
# See CustomDataExample theme for the theme implementation part

import math
import platform
from abc import ABC, abstractmethod
from typing import List


# Custom data classes must be implemented in this file, inherit the CustomDataSource and implement its 2 methods
class CustomDataSource(ABC):
    @abstractmethod
    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # If there is no numeric value, keep this function empty
        pass

    @abstractmethod
    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        pass

    @abstractmethod
    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        # If you do not want to draw a line graph or if your custom data has no numeric values, keep this function empty
        pass


# Example for a custom data class that has numeric and text values
class ExampleCustomNumericData(CustomDataSource):
    # This list is used to store the last 10 values to display a line graph
    last_val = [math.nan] * 10  # By default, it is filed with math.nan values to indicate there is no data stored

    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # Here a Python function from another module can be called to get data
        # Example: self.value = my_module.get_rgb_led_brightness() / audio.system_volume() ...
        self.value = 75.845

        # Store the value to the history list that will be used for line graph
        self.last_val.append(self.value)
        # Also remove the oldest value from history list
        self.last_val.pop(0)

        return self.value

    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text.
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        # Example here: format numeric value: add unit as a suffix, and keep 1 digit decimal precision
        return f'{self.value:>5.1f}%'
        # Important note! If your numeric value can vary in size, be sure to display it with a default size.
        # E.g. if your value can range from 0 to 9999, you need to display it with at least 4 characters every time.
        # --> return f'{self.as_numeric():>4}%'
        # Otherwise, part of the previous value can stay displayed ("ghosting") after a refresh

    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        return self.last_val


# Example for a custom data class that only has text values
class ExampleCustomTextOnlyData(CustomDataSource):
    def as_numeric(self) -> float:
        # If there is no numeric value, keep this function empty
        pass

    def as_string(self) -> str:
        # If a custom data class only has text values, it won't be possible to display graph or radial bars
        return "Python: " + platform.python_version()

    def last_values(self) -> List[float]:
        # If a custom data class only has text values, it won't be possible to display line graph
        pass


# =====================================================================================================================
# Grid3_2SSD theme: custom sensors (two SSDs, CPU power, fan speeds in rpm, total network speed)
# Data come from LibreHardwareMonitor, which the program already uses on Windows (HW_SENSORS: AUTO or LHM).
# =====================================================================================================================

# Defaults; the values SSD1_MATCH, SSD2_MATCH, CPU_FAN_SENSOR in config.yaml take precedence.
# Which disk is "SSD 1" and which is "SSD 2". Leave empty to use the first and the second disk found.
# To pin them, write a part of the model name, e.g. SSD1_MATCH = "970 EVO", SSD2_MATCH = "990 PRO".
# Model names are printed in the log at startup ("Found Storage: ...").
SSD1_MATCH = "970 EVO"
SSD2_MATCH = "SSD 1TB"

# Motherboard sensor used as the CPU fan (name as shown by LibreHardwareMonitor, e.g. "CPU Fan", "Fan #2").
# If not found, the first fan that is spinning is used.
CPU_FAN_SENSOR = "CPU Fan"

import sys as _sys
import ctypes
import time as _time


def _setting(key: str, default: str) -> str:
    try:
        from library import config as _cfg
        v = _cfg.CONFIG_DATA['config'].get(key)
        return default if v is None else str(v)
    except Exception:
        return default


def _demo_mode() -> bool:
    try:
        from library import config as _cfg
        return _cfg.CONFIG_DATA['config'].get('HW_SENSORS') in ('STATIC', 'STUB')
    except Exception:
        return False


def _lhm():
    # Use LibreHardwareMonitor only if the program has already loaded it (never initialise it from here)
    return _sys.modules.get('library.sensors.sensors_librehardwaremonitor')


def _value(hw, sensor_type_name, names=None, update=True):
    try:
        lhm = _lhm()
        stype = getattr(lhm.Hardware.SensorType, sensor_type_name)
        if update:
            hw.Update()
        sensors_list = [s for s in hw.Sensors if s.SensorType == stype and s.Value is not None]
        if names:
            for name in names:
                for s in sensors_list:
                    if str(s.Name) == name:
                        return float(s.Value)
            return math.nan
        return float(sensors_list[0].Value) if sensors_list else math.nan
    except Exception:
        return math.nan


def _disks():
    lhm = _lhm()
    if lhm is None:
        return []
    try:
        return [h for h in lhm.handle.Hardware if h.HardwareType == lhm.Hardware.HardwareType.Storage]
    except Exception:
        return []


def _ssd(n: int):
    disks = _disks()

    def find(match):
        for h in disks:
            if match.lower() in str(h.Name).lower():
                return h
        return None

    m1, m2 = _setting('SSD1_MATCH', SSD1_MATCH), _setting('SSD2_MATCH', SSD2_MATCH)
    if (n == 0 and m1 == '-') or (n == 1 and m2 == '-'):  # "do not show"
        return None
    first = find(m1) if m1 else (disks[0] if disks else None)
    if n == 0:
        return first
    if m2:
        return find(m2)
    for h in disks:
        if first is None or str(h.Identifier) != str(first.Identifier):
            return h
    return None


def _fmt(v, width, digits=0):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return '--'.rjust(width)
    return f'{v:>{width}.{digits}f}'


class _Numeric(CustomDataSource):
    width = 3
    digits = 0
    demo = 0.0

    def read(self) -> float:
        return math.nan

    def as_numeric(self) -> float:
        try:
            self.value = self.demo if _demo_mode() else self.read()
        except Exception:
            self.value = math.nan
        return self.value

    def as_string(self) -> str:
        return _fmt(getattr(self, 'value', math.nan), self.width, self.digits)

    def last_values(self) -> List[float]:
        pass


class _SsdTemp(_Numeric):
    index = 0

    def read(self) -> float:
        hw = _ssd(self.index)
        if hw is None:
            return math.nan
        return _value(hw, 'Temperature', ['Composite Temperature', 'Temperature', 'Temperature #1'])


class _SsdUsed(_Numeric):
    index = 0

    def read(self) -> float:
        hw = _ssd(self.index)
        if hw is None:
            return math.nan
        return _value(hw, 'Load', ['Used Space'])


class Ssd1Temp(_SsdTemp):
    index, demo = 0, 38.0


class Ssd1Used(_SsdUsed):
    index, demo = 0, 36.0


class Ssd2Temp(_SsdTemp):
    index, demo = 1, 33.0


class Ssd2Used(_SsdUsed):
    index, demo = 1, 61.0


class CpuPower(_Numeric):
    width, demo = 3, 34.0

    def read(self) -> float:
        lhm = _lhm()
        cpu = lhm.get_hw_and_update(lhm.Hardware.HardwareType.Cpu)
        v = _value(cpu, 'Power', ['CPU Package', 'Package'], update=False)
        return v if not math.isnan(v) else _value(cpu, 'Power', update=False)


class CpuFanRpm(_Numeric):
    width, demo = 4, 755.0

    def read(self) -> float:
        lhm = _lhm()
        mb = lhm.get_hw_and_update(lhm.Hardware.HardwareType.Motherboard)
        fans = []
        for sh in mb.SubHardware:
            sh.Update()
            for s in sh.Sensors:
                if s.SensorType == lhm.Hardware.SensorType.Fan and s.Value is not None:
                    fans.append((str(s.Name), float(s.Value)))
        wanted = _setting('CPU_FAN_SENSOR', CPU_FAN_SENSOR).lower()
        for name, v in fans:
            if name.lower() == wanted:
                return v
        for name, v in fans:
            if v > 0:
                return v
        return math.nan


class GpuFanRpm(_Numeric):
    width, demo = 4, 0.0

    def read(self) -> float:
        lhm = _lhm()
        gpu = lhm.Gpu.get_gpu_to_use()
        if gpu is None:
            return math.nan
        return _value(gpu, 'Fan', update=False)


class _Net:
    # total traffic of all network adapters, MB/s (1 MB = 1 000 000 bytes)
    t = None
    sent = recv = 0
    up = down = 0.0

    @classmethod
    def update(cls):
        import psutil
        now = _time.monotonic()
        if cls.t is not None and now - cls.t < 0.5:
            return
        c = psutil.net_io_counters()
        if cls.t is not None:
            dt = now - cls.t
            cls.up = max(0.0, (c.bytes_sent - cls.sent) / dt / 1e6)
            cls.down = max(0.0, (c.bytes_recv - cls.recv) / dt / 1e6)
        cls.t, cls.sent, cls.recv = now, c.bytes_sent, c.bytes_recv


class NetUp(_Numeric):
    width, digits, demo = 5, 1, 0.1

    def read(self) -> float:
        _Net.update()
        return _Net.up


class NetDown(_Numeric):
    width, digits, demo = 5, 1, 12.4

    def read(self) -> float:
        _Net.update()
        return _Net.down


def ram_temp_enabled() -> bool:
    return str(_setting('RAM_TEMP', 'false')).strip().lower() in ('true', '1', 'yes')


def read_ram_temps() -> list:
    """Temperatures of memory modules with a thermal sensor (DIMM #0, #1, ... in slot order)."""
    lhm = _lhm()
    if lhm is None:
        return []
    found = []
    try:
        for h in lhm.handle.Hardware:
            if h.HardwareType != lhm.Hardware.HardwareType.Memory:
                continue
            h.Update()
            for s in h.Sensors:
                name = str(s.Name)
                if (s.SensorType == lhm.Hardware.SensorType.Temperature and s.Value is not None
                        and name.startswith('DIMM')):
                    try:
                        idx = int(name.split('#')[-1])
                    except ValueError:
                        idx = 99
                    found.append((idx, float(s.Value)))
    except Exception:
        pass
    return [v for _, v in sorted(found)]


def read_ram_temp() -> float:
    t = read_ram_temps()
    return max(t) if t else math.nan


class _RamTempN(_Numeric):
    width = 3
    index = 0

    def read(self) -> float:
        t = read_ram_temps()
        return t[self.index] if len(t) > self.index else math.nan

    def as_numeric(self) -> float:
        if not ram_temp_enabled():
            self.value = math.nan
            return self.value
        return super().as_numeric()

    def as_string(self) -> str:
        if not ram_temp_enabled():
            return ' ' * self.width  # an empty string would stop the drawing of the next custom values
        return super().as_string()


class RamTemp1(_RamTempN):
    index, demo = 0, 41.0


class RamTemp2(_RamTempN):
    index, demo = 1, 43.0


# ---------------------------------------------------------------- uptime
def _boot_times():
    """(power-on time, last restart time) as epoch seconds.
    Restart = last full start of Windows (GetTickCount64, same as Task Manager).
    Power-on = latest Kernel-Boot event 27 (written at every start, including Fast Startup
    and resume from hibernation, but not after sleep); never earlier than the last restart."""
    now = _time.time()
    try:
        restart = now - ctypes.windll.kernel32.GetTickCount64() / 1000.0
    except Exception:
        import psutil
        restart = psutil.boot_time()
    on = restart
    try:
        import win32evtlog
        q = win32evtlog.EvtQuery('System', win32evtlog.EvtQueryReverseDirection,
                                 "*[System[Provider[@Name='Microsoft-Windows-Kernel-Boot'] and (EventID=27)]]")
        ev = win32evtlog.EvtNext(q, 1)
        if ev:
            xml = win32evtlog.EvtRender(ev[0], win32evtlog.EvtRenderEventXml)
            import re, datetime
            m = re.search(r"SystemTime='([^']+)'", xml) or re.search(r'SystemTime="([^"]+)"', xml)
            if m:
                ts = m.group(1).rstrip('Z')[:26]
                t = datetime.datetime.fromisoformat(ts).replace(tzinfo=datetime.timezone.utc).timestamp()
                if restart - 120 <= t <= now:
                    on = max(on, t)
    except Exception:
        pass
    return on, restart


class _Boot:
    t = 0.0
    on = restart = None

    @classmethod
    def get(cls):
        now = _time.monotonic()
        if cls.on is None or now - cls.t > 60:  # the event log is read at most once a minute
            cls.on, cls.restart = _boot_times()
            cls.t = now
        return cls.on, cls.restart


def _fmt_duration(sec) -> str:
    if sec is None or (isinstance(sec, float) and math.isnan(sec)) or sec < 0:
        return '--'
    m = int(sec // 60)
    d, m = divmod(m, 1440)
    h, m = divmod(m, 60)
    return ('%dd %d:%02d' % (d, h, m)) if d else ('%d:%02d' % (h, m))


class _Uptime(_Numeric):
    which = 0
    demo = 0.0

    def read(self) -> float:
        on, restart = _Boot.get()
        return _time.time() - (on if self.which == 0 else restart)

    def as_string(self) -> str:
        return _fmt_duration(getattr(self, 'value', math.nan)).rjust(9)


class UptimeOn(_Uptime):
    which, demo = 0, 3 * 3600 + 25 * 60


class UptimeReboot(_Uptime):
    which, demo = 1, 4 * 86400 + 6 * 3600 + 10 * 60


# ---------------------------------------------------------------- user temperature sensor
def extra_sensor_id(n: int) -> str:
    v = str(_setting('EXTRA_SENSOR_%d' % n, '')).strip()
    return '' if v in ('', '-') else v


def _all_hw():
    lhm = _lhm()
    if lhm is None:
        return []
    out = []
    try:
        for h in lhm.handle.Hardware:
            out.append(h)
            out.extend(list(h.SubHardware))
    except Exception:
        pass
    return out


def list_temperature_sensors() -> list:
    """[(identifier, hardware name, sensor name, value)] of motherboard and controller temperatures."""
    lhm = _lhm()
    if lhm is None:
        return []
    kinds = (lhm.Hardware.HardwareType.Motherboard, lhm.Hardware.HardwareType.SuperIO,
             lhm.Hardware.HardwareType.EmbeddedController, lhm.Hardware.HardwareType.Cooler)
    out = []
    for h in _all_hw():
        try:
            if h.HardwareType not in kinds:
                continue
            h.Update()
            for s in h.Sensors:
                if s.SensorType == lhm.Hardware.SensorType.Temperature and s.Value is not None:
                    out.append((str(s.Identifier), str(h.Name), str(s.Name), float(s.Value)))
        except Exception:
            pass
    return out


def read_sensor_by_id(ident: str) -> float:
    if _lhm() is None or not ident:
        return math.nan
    for h in _all_hw():
        try:
            for s in h.Sensors:
                if str(s.Identifier) == ident:
                    h.Update()
                    return float(s.Value) if s.Value is not None else math.nan
        except Exception:
            pass
    return math.nan


class _ExtraTemp(_Numeric):
    width, digits = 5, 1
    n = 1

    def _on(self) -> bool:
        return bool(extra_sensor_id(self.n))

    def read(self) -> float:
        return read_sensor_by_id(extra_sensor_id(self.n))

    def as_numeric(self) -> float:
        if not self._on():
            self.value = math.nan
            return self.value
        return super().as_numeric()

    def as_string(self) -> str:
        if not self._on():
            return ' ' * self.width  # hidden row; an empty string would stop the next custom values
        return super().as_string()


class ExtraTemp1(_ExtraTemp):
    n, demo = 1, 24.5

