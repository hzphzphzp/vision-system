#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NumPy兼容性升级脚本

将所有包升级到支持NumPy 2.x的版本

Author: Vision System Team
Date: 2026-02-03
"""

import subprocess
import sys


def run_command(cmd, description):
    """运行命令并显示描述"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"执行命令: {cmd}")
    print()
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode


def main():
    print("\n" + "="*60)
    print("NumPy 2.x 兼容性升级")
    print("="*60)
    
    commands = [
        ("pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cpu", 
         "升级 PyTorch 到 2.2+ (支持 NumPy 2.x)"),
        
        ("pip install --upgrade ultralytics", 
         "升级 Ultralytics 到 8.3.0+ (支持 NumPy 2.x)"),
        
        ("pip install --upgrade pandas", 
         "升级 pandas 到 2.0+ (支持 NumPy 2.x)"),
        
        ("pip install --upgrade pillow scikit-image", 
         "升级 Pillow 和 scikit-image (支持 NumPy 2.x)"),
        
        ("pip install --upgrade opencv-python opencv-contrib-python", 
         "升级 OpenCV (支持 NumPy 2.x)"),
        
        ("pip install --upgrade matplotlib", 
         "升级 matplotlib (支持 NumPy 2.x)"),
        
        ("pip show numpy | grep Version", 
         "确认 NumPy 版本"),
        
        ("pip show torch | grep Version", 
         "确认 PyTorch 版本"),
        
        ("pip show ultralytics | grep Version", 
         "确认 Ultralytics 版本"),
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc)
    
    print("\n" + "="*60)
    print("升级完成!")
    print("="*60)
    print("\n如果遇到问题，请尝试:")
    print("1. 重启 Python 环境")
    print("2. 重新运行: pip install --force-reinstall -r requirements.txt")
    print("3. 或者创建一个新的 Conda 环境")


if __name__ == "__main__":
    main()
