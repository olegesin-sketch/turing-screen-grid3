# Third-party components

| Component | License | Where |
|---|---|---|
| [turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) by Matthieu Houdebine and contributors, commit `2b33ab4f00a096916dd6a1174441a53a7ec33b03` | GNU GPL 3.0 | base program; `src/main.py` and `src/library/sensors/sensors_custom.py` are modified copies of its files |
| [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) | MPL 2.0 | hardware sensors, shipped by the base program in `external/LibreHardwareMonitor` |
| [Oswald](https://github.com/googlefonts/OswaldFont) font, The Oswald Project Authors | SIL Open Font License 1.1 | `src/res/fonts/oswald` (labels) |
| GeForce, Roboto, Roboto Mono fonts | as distributed with the base program | `res/fonts` of the base program |
| Python libraries (pyserial, psutil, Pillow, numpy, pythonnet, pystray, babel, PyYAML and others) | their own licenses | bundled into the exe by PyInstaller |

The PawnIO driver is **not** included; it is installed separately by the user from [pawnio.eu](https://pawnio.eu).
