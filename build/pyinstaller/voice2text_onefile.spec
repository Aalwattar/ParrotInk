# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules("pynput")
hiddenimports += collect_submodules("pystray")
hiddenimports += collect_submodules("PIL")
hiddenimports += collect_submodules("websockets")
hiddenimports += collect_submodules("keyring")
hiddenimports += ["keyring.backends.Windows"]

datas = []
datas += collect_data_files("pystray")
datas += collect_data_files("PIL")
# Include assets
datas += [('assets', 'assets')]

binaries = []
binaries += collect_dynamic_libs("sounddevice")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Voice2Text",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
