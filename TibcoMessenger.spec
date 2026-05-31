# -*- mode: python -*-
"""PyInstaller spec for Tibco Messenger."""

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect presets.json and helpers
datas = [
    (os.path.join(SPECPATH, 'presets.json'), '.'),
    (os.path.join(SPECPATH, 'tibco_request.sh'), '.'),
    (os.path.join(SPECPATH, 'TibcoRequest.class'), '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
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
    [],
    exclude_binaries=True,
    name='TibcoMessenger',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TibcoMessenger',
)

app = BUNDLE(
    coll,
    name='Tibco Messenger.app',
    icon=None,
    bundle_identifier='com.glory.tibco-messenger',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'CFBundleName': 'Tibco Messenger',
        'CFBundleDisplayName': 'Tibco Messenger',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': 'com.glory.tibco-messenger',
        'NSHighResolutionCapable': True,
        'LSEnvironment': {
            'DYLD_LIBRARY_PATH': '/opt/tibco/tibrv/8.7/lib',
        },
    },
)
