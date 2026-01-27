#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读码工具模块

提供条码和二维码识别功能。

Author: Vision System Team
Date: 2025-01-04
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from core.tool_base import RecognitionToolBase, ToolRegistry, ToolParameter
from data.image_data import ImageData, ResultData
from utils.exceptions import ToolException


class BarcodeType(Enum):
    """条码类型"""
    CODE_128 = "code128"
    CODE_39 = "code39"
    EAN_13 = "ean13"
    EAN_8 = "ean8"
    UPC_A = "upca"
    UPC_E = "upce"
    QR_CODE = "qrcode"
    DATA_MATRIX = "datamatrix"
    ALL = "all"


@ToolRegistry.register
class BarcodeReader(RecognitionToolBase):
    """
    条码识别工具
    
    支持Code128、Code39、EAN13等一维码识别。
    
    参数说明：
    - barcode_type: 条码类型
    - use_angle: 是否使用角度信息
    """
    
    tool_name = "条码识别"
    tool_category = "Recognition"
    tool_description = "识别一维条码"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "barcode_type": ToolParameter(
            name="条码类型",
            param_type="enum",
            default="all",
            description="条码类型",
            options=["all", "code128", "code39", "ean13", "ean8", "upca", "upce"]
        ),
        "use_angle": ToolParameter(
            name="使用角度",
            param_type="boolean",
            default=False,
            description="是否使用角度信息"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("barcode_type", "all")
        self.set_param("use_angle", False)
    
    def _run_impl(self):
        """执行条码识别"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        
        # 转换为灰度
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        # 使用pyzbar进行条码识别
        try:
            from pyzbar.pyzbar import decode as decode_barcode
            barcodes = decode_barcode(gray_image)
        except ImportError:
            # 如果没有pyzbar，尝试使用OpenCV的条形码检测器
            barcodes = self._detect_with_opencv(gray_image)
        
        # 处理结果
        self._result_data = ResultData()
        
        if barcodes:
            results = []
            output_image = input_image.copy()
            
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8') if isinstance(barcode.data, bytes) else barcode.data
                barcode_type = barcode.type
                
                # 过滤：条码识别只处理一维码，跳过二维码
                if barcode_type in ['QRCODE', 'DATA_MATRIX']:
                    continue
                
                # 获取位置信息
                points = barcode.polygon
                if len(points) >= 4:
                    rect = cv2.boundingRect(np.array(points))
                    x, y, w, h = rect
                    
                    result = {
                        "data": barcode_data,
                        "type": barcode_type,
                        "rect": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                        "confidence": 1.0
                    }
                    results.append(result)
                    
                    # 绘制检测框
                    pts = np.array(points, np.int32)
                    cv2.polylines(output_image, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                    
                    # 绘制文本
                    cv2.putText(output_image, f"{barcode_type}: {barcode_data}", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            self._result_data.set_value("count", len(results))
            self._result_data.set_value("barcodes", results)
            self._result_data.set_value("status", "OK")
            self._logger.info(f"识别到 {len(results)} 个条码")
            
        else:
            self._result_data.set_value("count", 0)
            self._result_data.set_value("barcodes", [])
            self._result_data.set_value("status", "No barcode found")
            output_image = input_image.copy()
            self._logger.info("未识别到条码")
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
    
    def _detect_with_opencv(self, gray_image: np.ndarray) -> list:
        """使用OpenCV的条形码检测器"""
        try:
            # OpenCV 4.x 以上的版本有条形码检测器
            detector = cv2.barcode_BarcodeDetector()
            if detector is not None:
                ret, decoded_info, decoded_type, corners = detector.detectAndDecode(gray_image)
                
                if ret and len(decoded_info) > 0:
                    barcodes = []
                    for i, (info, type_id) in enumerate(zip(decoded_info, decoded_type)):
                        if info:
                            # 创建模拟的barcode对象
                            class MockBarcode:
                                def __init__(self, data, btype, corner):
                                    self.data = data.encode() if isinstance(data, str) else data
                                    self.type = btype
                                    self.polygon = corner
                            
                            barcodes.append(MockBarcode(info, type_id, corners[i] if corners is not None else []))
                    
                    return barcodes
        except Exception:
            pass
        
        return []


@ToolRegistry.register
class QRCodeReader(RecognitionToolBase):
    """
    二维码识别工具
    
    识别QR Code和Data Matrix二维码。
    
    参数说明：
    - qr_type: QR码类型
    - use_angle: 是否使用角度信息
    """
    
    tool_name = "二维码识别"
    tool_category = "Recognition"
    tool_description = "识别二维码"
    
    # 中文参数定义
    PARAM_DEFINITIONS = {
        "qr_type": ToolParameter(
            name="QR码类型",
            param_type="enum",
            default="all",
            description="QR码类型",
            options=["all", "qrcode", "datamatrix"]
        ),
        "use_angle": ToolParameter(
            name="使用角度",
            param_type="boolean",
            default=False,
            description="是否使用角度信息"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("qr_type", "all")
        self.set_param("use_angle", False)
    
    def _run_impl(self):
        """执行二维码识别"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        
        # 转换为灰度
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        # 使用pyzbar进行二维码识别
        try:
            from pyzbar.pyzbar import decode as decode_barcode
            objects = decode_barcode(gray_image)
            
            # 筛选二维码
            qr_objects = [obj for obj in objects if obj.type == 'QRCODE']
        except ImportError:
            qr_objects = []
        
        # 尝试使用OpenCV的QRCode检测器
        if not qr_objects:
            try:
                detector = cv2.QRCodeDetector()
                ret, decoded_info, decoded_type, corners = detector.detectAndDecodeMulti(gray_image)
                
                if ret:
                    qr_objects = []
                    for i, info in enumerate(decoded_info):
                        if info:
                            class MockQRCode:
                                def __init__(self, data, corner):
                                    self.data = data
                                    self.type = 'QRCODE'
                                    self.polygon = corner
                            
                            qr_objects.append(MockQRCode(info, corners[i] if corners is not None else []))
            except Exception:
                pass
        
        # 处理结果
        self._result_data = ResultData()
        
        if qr_objects:
            results = []
            output_image = input_image.copy()
            
            for qr in qr_objects:
                qr_data = qr.data.decode('utf-8') if isinstance(qr.data, bytes) else qr.data
                
                # 获取位置信息
                if hasattr(qr, 'polygon') and len(qr.polygon) >= 4:
                    rect = cv2.boundingRect(np.array(qr.polygon))
                    x, y, w, h = rect
                    
                    result = {
                        "data": qr_data,
                        "type": qr.type,
                        "rect": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                        "confidence": 1.0
                    }
                    results.append(result)
                    
                    # 绘制检测框
                    pts = np.array(qr.polygon, np.int32)
                    cv2.polylines(output_image, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
                    
                    # 绘制文本
                    cv2.putText(output_image, f"QR: {qr_data[:20]}...", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            self._result_data.set_value("count", len(results))
            self._result_data.set_value("qrcodes", results)
            self._result_data.set_value("status", "OK")
            self._logger.info(f"识别到 {len(results)} 个二维码")
            
        else:
            self._result_data.set_value("count", 0)
            self._result_data.set_value("qrcodes", [])
            self._result_data.set_value("status", "No QR code found")
            output_image = input_image.copy()
            self._logger.info("未识别到二维码")
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image


@ToolRegistry.register
class CodeReader(RecognitionToolBase):
    """
    综合读码工具
    
    同时支持一维码和二维码识别。
    
    参数说明：
    - read_barcode: 是否识别一维码
    - read_qrcode: 是否识别二维码
    - max_count: 最大识别数量
    """
    
    tool_name = "读码"
    tool_category = "Recognition"
    tool_description = "综合条码和二维码识别"
    
    PARAM_DEFINITIONS = {
        "read_barcode": ToolParameter(
            name="识别一维码",
            param_type="boolean",
            default=True,
            description="是否识别一维条码"
        ),
        "read_qrcode": ToolParameter(
            name="识别二维码",
            param_type="boolean",
            default=True,
            description="是否识别二维码"
        ),
        "max_count": ToolParameter(
            name="最大数量",
            param_type="integer",
            default=10,
            description="最大识别数量"
        )
    }
    
    def _init_params(self):
        """初始化默认参数"""
        self.set_param("read_barcode", True)
        self.set_param("read_qrcode", True)
        self.set_param("max_count", 10)
    
    def _run_impl(self):
        """执行综合读码"""
        if not self.has_input():
            raise ToolException("无输入图像")
        
        input_image = self._input_data.data
        output_image = input_image.copy()
        
        read_barcode = self.get_param("read_barcode", True)
        read_qrcode = self.get_param("read_qrcode", True)
        max_count = self.get_param("max_count", 10)
        
        all_results = []
        
        # 转换为灰度
        if len(input_image.shape) == 3:
            gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = input_image
        
        # 使用pyzbar识别所有码
        try:
            from pyzbar.pyzbar import decode as decode_barcode
            barcodes = decode_barcode(gray_image)
            
            for barcode in barcodes:
                if len(all_results) >= max_count:
                    break
                
                barcode_type = barcode.type
                data = barcode.data.decode('utf-8') if isinstance(barcode.data, bytes) else barcode.data
                
                # 判断是一维码还是二维码
                is_qrcode = barcode_type in ['QRCODE', 'DATA_MATRIX']
                
                # 根据参数过滤
                if is_qrcode and not read_qrcode:
                    continue
                if not is_qrcode and not read_barcode:
                    continue
                
                # 绘制识别框
                if len(barcode.polygon) >= 4:
                    rect = cv2.boundingRect(np.array(barcode.polygon))
                    x, y, w, h = rect
                    
                    pts = np.array(barcode.polygon, np.int32)
                    
                    # 二维码用黄色，一维码用绿色
                    color = (0, 255, 255) if is_qrcode else (0, 255, 0)
                    label = f"QR: {data}" if is_qrcode else f"{barcode_type}: {data}"
                    
                    cv2.polylines(output_image, [pts], isClosed=True, color=color, thickness=2)
                    cv2.putText(output_image, label, 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    all_results.append({
                        "data": data,
                        "type": barcode_type,
                        "rect": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                    })
                    
        except ImportError:
            self._logger.warning("pyzbar未安装，无法使用综合读码功能")
        
        # 如果pyzbar没有识别到，尝试用OpenCV作为备选
        if not all_results:
            # 用OpenCV的条形码检测器尝试
            if read_barcode:
                try:
                    barcodes = self._detect_with_opencv(gray_image)
                    for barcode in barcodes:
                        if len(all_results) >= max_count:
                            break
                        
                        data, barcode_type = barcode
                        is_qrcode = barcode_type in ['QRCODE', 'DATA_MATRIX']
                        
                        if is_qrcode and not read_qrcode:
                            continue
                        if not is_qrcode and not read_barcode:
                            continue
                        
                        # 绘制矩形框
                        x, y, w, h = barcode['rect']
                        color = (0, 255, 255) if is_qrcode else (0, 255, 0)
                        label = f"QR: {data}" if is_qrcode else f"{barcode_type}: {data}"
                        
                        cv2.rectangle(output_image, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(output_image, label, (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        all_results.append({
                            "data": data,
                            "type": barcode_type,
                            "rect": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                        })
                except Exception:
                    pass
        
        # 保存结果
        self._result_data = ResultData()
        self._result_data.set_value("count", len(all_results))
        self._result_data.set_value("codes", all_results)
        self._result_data.set_value("status", "OK" if all_results else "No code found")
        
        self._output_data = self._input_data.copy()
        self._output_data.data = output_image
        
        self._logger.info(f"综合读码完成: 识别到 {len(all_results)} 个码")
