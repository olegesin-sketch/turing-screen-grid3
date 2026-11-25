# -*- mode: python ; coding: utf-8 -*-
# Standalone build of turing-smart-screen-python + Grid3_2SSD theme + launcher (TuringScreen.py)

a = Analysis(
    ['TuringScreen.py'],
    pathex=['.'],
    binaries=[],
    datas=[('build_res\\res', 'res'), ('config.yaml', '.'), ('external', 'external')],
    hiddenimports=['main', 'win32evtlog', 'settings_gui', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', 'pystray._win32',
                   'clr', 'clr_loader', 'pythonnet', 'serial.tools.list_ports_windows',
                   'library.sensors.sensors_librehardwaremonitor', 'library.sensors.sensors_python',
                   'library.sensors.sensors_stub_static', 'library.sensors.sensors_stub_random',
                   'library.sensors.sensors_custom', 'babel.numbers', 'babel.dates'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TuringScreen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['res\\icons\\monitor-icon-17865\\icon.ico'],
    contents_directory='.',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='TuringScreen',
)
