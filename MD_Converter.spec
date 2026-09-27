# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

# Packaging rules shared by both build profiles (WP-P12-08-02 / WP-P12-08-04).
_PROJECT_ROOT = os.path.abspath(globals().get('SPECPATH') or os.getcwd())
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'packaging', 'windows'))

from pyi_support import (  # noqa: E402  (import path set up above)
    read_project_version,
    strip_development_material,
    strip_shadowed_system_dlls,
    write_version_resource,
)

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
# Operating-system libraries must come from Windows, never from the bundle
# (WinError 127), and developer/test data must not ship (WP-P12-08-04).
a.binaries = strip_shadowed_system_dlls(a.binaries)
a.datas = strip_development_material(a.datas)

# The executable's version resource is generated from the authoritative
# project version, so the packaged metadata cannot drift from pyproject.toml.
_VERSION = read_project_version(_PROJECT_ROOT)
_VERSION_RESOURCE = write_version_resource(
    os.path.join(_PROJECT_ROOT, 'build', 'MD_Converter', 'version_info.txt'),
    _VERSION,
    product_name='MD Converter',
    original_filename='MD_Converter.exe',
    file_description='Markdown to Microsoft Word DOCX Converter',
    company_name='Quansheng2022',
    copyright_text='Copyright (C) 2026 Quansheng2022',
)

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
    version=_VERSION_RESOURCE,
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
