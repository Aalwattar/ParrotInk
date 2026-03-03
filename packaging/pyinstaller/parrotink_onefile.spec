# -*- mode: python ; coding: utf-8 -*-
import os
import skia
import glob
import warnings
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
APP_NAME = "ParrotInk"

# SPECPATH is defined by PyInstaller at runtime
repo_root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

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

skia_dir = os.path.dirname(skia.__file__)
icu_source = os.path.join(skia_dir, "icudtl.dat")
if os.path.exists(icu_source):
    datas += [(icu_source, ".")]
else:
    parent_icu = os.path.join(os.path.dirname(skia_dir), "icudtl.dat")
    if os.path.exists(parent_icu):
        datas += [(parent_icu, ".")]
    else:
        warnings.warn("icudtl.dat not found")

datas += [(os.path.join(repo_root, "assets"), "assets")]
datas += [(os.path.join(repo_root, "pyproject.toml"), ".")]
datas += [(os.path.join(repo_root, "config.example.toml"), ".")]

binaries = []
sibling_dlls = glob.glob(os.path.join(skia_dir, "*.dll"))
binaries += [(dll, ".") for dll in sibling_dlls]

a = Analysis(
    [os.path.join(repo_root, "main.py")],
    pathex=[repo_root],
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
    name=APP_NAME,
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
    version=os.path.join(SPECPATH, "version_info.txt"),
    icon=os.path.join(repo_root, "assets", "icons", "icon.ico"),
)
