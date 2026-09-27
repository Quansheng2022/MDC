# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

datas = []
datas += collect_data_files('md_converter')
datas += copy_metadata('md_converter')


a = Analysis(
    ['packaging/windows/launcher_main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# ---------------------------------------------------------------------------
# Packaging-only correction (WP-P12-08-02): never ship shadowing OS libraries.
#
# PyInstaller resolves binary dependencies through PATH as well as through the
# build environment.  On a machine whose PATH contains portable tool runtimes
# this pulls third-party copies of operating-system DLLs into _internal, where
# they are found *before* System32 (the application directory is searched
# first).  The shadowing copies are older/incompatible and make Qt 6 fail with
# "The specified procedure could not be found" (WinError 127) while importing
# QtCore/QtWidgets:
#
#   * a stale ucrtbase.dll shadows the operating system UCRT;
#   * api-ms-win-*.dll stubs shadow the Windows API sets that Qt imports
#     (for example api-ms-win-core-synch-l1-2-0.dll must export WaitOnAddress);
#   * a portable icuuc.dll/icudt*.dll shadows the Windows ICU that Qt links
#     against (Qt needs the unversioned ucnv_* exports provided by Windows).
#
# Windows 10 and later - the supported product baseline - already provide all
# of these libraries, so none of them may be bundled.
# ---------------------------------------------------------------------------
_SHADOWED_SYSTEM_DLLS = ("ucrtbase.dll",)
_SHADOWED_SYSTEM_DLL_PREFIXES = ("api-ms-win-", "icu")


def _is_shadowed_system_dll(name):
    lower = os.path.basename(name).lower()
    if lower.endswith(".dll") is False:
        return False
    if lower in _SHADOWED_SYSTEM_DLLS:
        return True
    return lower.startswith(_SHADOWED_SYSTEM_DLL_PREFIXES)


a.binaries = [
    _entry for _entry in a.binaries if not _is_shadowed_system_dll(_entry[0])
]

pyz = PYZ(a.pure)

# Packaging decision (WP-P12-08-02): the packaged product is a desktop GUI
# application, so the executable is windowed.  A console build opened an
# unwanted console window next to the GUI; in the windowed build the process has
# no console, so the remaining Core print() diagnostics are simply no-ops.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MD_Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MD_Converter',
)
