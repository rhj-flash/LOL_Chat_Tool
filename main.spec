# -*- mode: python ; coding: utf-8 -*-


# main.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # 关键修改：在 datas 参数中添加要包含的非代码文件
    datas=[
        ('icon.ico', '.'),          # 将 icon.ico 文件包含到根目录
        ('messages.json', '.'),     # 将 messages.json 包含到根目录
        ('config.json', '.')        # 将 config.json 包含到根目录
    ],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='LOL友好交流器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 关键修改：在这里指定EXE的图标文件
    icon='icon.ico'
)
