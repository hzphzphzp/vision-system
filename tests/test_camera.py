#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海康相机连接测试（SDK相关）

此文件保留在根目录因为它需要特定的SDK路径配置。

主要测试已移至 tests/test_camera.py

Usage:
    # SDK路径测试
    python test_camera.py
    
    # 完整功能测试
    python tests/test_camera.py
"""

import sys

mvimport_path = r"D:\MVS\MVS\Development\Samples\Python\MvImport"
if mvimport_path not in sys.path:
    sys.path.append(mvimport_path)

try:
    from MvCameraControl_class import MvCamera, MV_CC_DEVICE_INFO_LIST, MV_GIGE_DEVICE, MV_USB_DEVICE
    from ctypes import byref, sizeof, pointer

    print("初始化SDK...")
    ret = MvCamera.MV_CC_Initialize()
    print(f"初始化结果: 0x{ret:x}")

    print("\n开始枚举设备...")
    deviceList = MV_CC_DEVICE_INFO_LIST()
    stDeviceList = pointer(deviceList)
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, stDeviceList)
    print(f"枚举结果: 0x{ret:x}")
    print(f"发现设备数量: {deviceList.nDeviceNum}")

    if deviceList.nDeviceNum > 0:
        print(f"\n发现 {deviceList.nDeviceNum} 个设备:")
        for i in range(deviceList.nDeviceNum):
            device_info = deviceList.pDeviceInfo[i]
            if device_info.nTLayerType == MV_GIGE_DEVICE:
                model_name = device_info.SpecialInfo.stGigEInfo.chModelName.decode('utf-8').rstrip('\x00')
                ip = device_info.SpecialInfo.stGigEInfo.chCurrentIp
                print(f"  [{i}] GigE: {model_name} @ {ip}")
            elif device_info.nTLayerType == MV_USB_DEVICE:
                model_name = device_info.SpecialInfo.stUsb3VInfo.chModelName.decode('utf-8').rstrip('\x00')
                print(f"  [{i}] USB: {model_name}")
    else:
        print("\n未发现任何设备!")
        print("可能的原因:")
        print("1. 相机未打开电源")
        print("2. GigE相机网络未连接或IP配置不正确")
        print("3. 相机被其他程序占用")
        print("4. 需要设置静态IP与相机在同一网段")

except ImportError as e:
    print(f"无法导入SDK模块: {e}")
    print("请确保已安装MVS SDK并配置正确的路径")
