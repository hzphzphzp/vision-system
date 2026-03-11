# -*- mode: python ; coding: utf-8 -*-
"""
Vision System PyInstaller 打包配置文件

使用方法:
    pyinstaller vision_system.spec

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from pathlib import Path

block_cipher = None

# 项目根目录 (当前目录)
ROOT_DIR = os.getcwd()

# 查找系统DLL
def find_dll(dll_name):
    """从系统路径查找DLL"""
    for path in os.environ.get('PATH', '').split(os.pathsep):
        dll_path = os.path.join(path, dll_name)
        if os.path.exists(dll_path):
            return dll_path
    return None

# 需要收集的关键DLL和PYD列表
required_dlls = [
    # Visual C++运行时
    'vcruntime140.dll',
    'vcruntime140_1.dll',
    'msvcp140.dll',
    'msvcp140_1.dll',
    'msvcp140_2.dll',
    'python3.dll',
    # OpenMP
    'libiomp5md.dll',
    # 压缩库
    'libbz2-1.dll',
    'libbz2-1.dll',
    'zlib1.dll',
    # 其他运行时
    'python3.dll',
    'python311.dll',
]

# 收集需要的二进制文件
binaries = []

for dll_name in required_dlls:
    dll_path = find_dll(dll_name)
    if dll_path:
        binaries.append((dll_path, '.'))
        print(f"Found: {dll_path}")
    else:
        print(f"Not found: {dll_name}")

# 数据文件 (只包含存在的目录)
datas = [
    (os.path.join(ROOT_DIR, 'config'), 'config'),
]

if os.path.exists(os.path.join(ROOT_DIR, 'resources')):
    datas.append((os.path.join(ROOT_DIR, 'resources'), 'resources'))

# 排除不需要的模块（这些模块有严重的打包问题）
excludes = [
    # 已有排除
    'matplotlib',
    'pandas',
    'pytest',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'tkinter',
    'PyQt5',
    'PyQt6',
    # 排除有问题的PIL插件
    'PIL_avif',
    'PIL.BmpImagePlugin',
    # 排除导致打包问题的重量级库
    'torch',
    'torchvision',
    'torchaudio',
    'tensorflow',
    'keras',
    'easyocr',
    'ultralytics',
    # 排除numba（依赖MKL）
    'numba',
    'llvmlite',
]

# 添加隐藏导入 (某些模块在运行时才导入)
hiddenimports = [
    'cv2',
    'numpy',
    'PIL',
    'PySide6',
    'yaml',
    # 可选的深度学习模块（如果被排除则不需要）
    # 'easyocr',
    # 'torch',
    # 'torchvision',
    # 'ultralytics',
    # 'sklearn',
    # 'skimage',
]

a = Analysis(
    [os.path.join(ROOT_DIR, 'run.py')],
    pathex=[ROOT_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='VisionSystem',
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
    icon=None,
)
