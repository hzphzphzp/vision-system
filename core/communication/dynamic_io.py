#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态IO类型定义模块

参考海康VisionMaster SDK设计，完全自主实现：
- 支持多种数据类型：int, float, string, image, points, line, circle, rect等
- 统一的IO接口设计
- 动态数据转换

Author: Vision System Team
Date: 2026-02-03
"""

import os
import sys
import struct
import json
import numpy as np
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass


# IO类型枚举（参考海康SDK设计）
class IoType(Enum):
    """IO数据类型枚举"""
    NOTSUPPORT = 0
    INT = 1              # 整型
    FLOAT = 2            # 浮点型
    STRING = 3           # 字符串型
    IMAGE = 4            # 图像
    POINTSET = 5         # 点集（暂不对外开放）
    BYTE = 6             # 二进制
    POINT_F = 7          # 浮点型点
    POINT_I = 8          # 整型点
    LINE = 9             # 线
    CIRCLE = 10          # 圆
    RECT_F = 11          # 不带角度矩形（浮点）
    RECT_I = 12          # 不带角度矩形（整型）
    ROIBOX = 13          # 带角度矩形
    FIXTURE = 14         # 位置修正
    ANNULUS = 16         # 圆环
    CONTOURPOINTS = 17   # 轮廓点（暂不对外开放）
    CLASSINFO = 18       # 类别信息
    PIXELIMAGE = 19      # 带类别信息的图像
    POSTURE = 20         # 位姿
    POLYGON = 21         # 多边形
    ELLIPSE = 22         # 椭圆


# 数据结构定义
@dataclass
class PointF:
    """浮点型点"""
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PointF':
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0))


@dataclass
class PointI:
    """整型点"""
    x: int = 0
    y: int = 0

    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PointI':
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass
class Line:
    """线段"""
    start_x: float = 0.0
    start_y: float = 0.0
    end_x: float = 0.0
    end_y: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "start_x": self.start_x, "start_y": self.start_y,
            "end_x": self.end_x, "end_y": self.end_y
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Line':
        return cls(
            start_x=data.get("start_x", 0.0),
            start_y=data.get("start_y", 0.0),
            end_x=data.get("end_x", 0.0),
            end_y=data.get("end_y", 0.0)
        )


@dataclass
class Circle:
    """圆"""
    center_x: float = 0.0
    center_y: float = 0.0
    radius: float = 0.0

    def to_dict(self) -> Dict:
        return {"center_x": self.center_x, "center_y": self.center_y, "radius": self.radius}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Circle':
        return cls(
            center_x=data.get("center_x", 0.0),
            center_y=data.get("center_y", 0.0),
            radius=data.get("radius", 0.0)
        )


@dataclass
class RectF:
    """不带角度矩形（浮点）"""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RectF':
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0)
        )


@dataclass
class RectBox:
    """带角度矩形"""
    center_x: float = 0.0
    center_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "center_x": self.center_x, "center_y": self.center_y,
            "width": self.width, "height": self.height, "angle": self.angle
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RectBox':
        return cls(
            center_x=data.get("center_x", 0.0),
            center_y=data.get("center_y", 0.0),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            angle=data.get("angle", 0.0)
        )


@dataclass
class Fixture:
    """位置修正"""
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0

    def to_dict(self) -> Dict:
        return {
            "x": self.x, "y": self.y,
            "angle": self.angle,
            "scale_x": self.scale_x, "scale_y": self.scale_y
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Fixture':
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            angle=data.get("angle", 0.0),
            scale_x=data.get("scale_x", 1.0),
            scale_y=data.get("scale_y", 1.0)
        )


@dataclass
class Annulus:
    """圆环"""
    center_x: float = 0.0
    center_y: float = 0.0
    inner_radius: float = 0.0
    outer_radius: float = 0.0
    start_angle: float = 0.0
    angle_extend: float = 360.0

    def to_dict(self) -> Dict:
        return {
            "center_x": self.center_x, "center_y": self.center_y,
            "inner_radius": self.inner_radius, "outer_radius": self.outer_radius,
            "start_angle": self.start_angle, "angle_extend": self.angle_extend
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Annulus':
        return cls(
            center_x=data.get("center_x", 0.0),
            center_y=data.get("center_y", 0.0),
            inner_radius=data.get("inner_radius", 0.0),
            outer_radius=data.get("outer_radius", 0.0),
            start_angle=data.get("start_angle", 0.0),
            angle_extend=data.get("angle_extend", 360.0)
        )


@dataclass
class Posture:
    """位姿"""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "theta": self.theta}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Posture':
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            theta=data.get("theta", 0.0)
        )


@dataclass
class Polygon:
    """多边形"""
    vertices: List[PointF] = None

    def __post_init__(self):
        if self.vertices is None:
            self.vertices = []

    def to_dict(self) -> Dict:
        return {
            "vertex_num": len(self.vertices),
            "vertices": [v.to_dict() for v in self.vertices]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Polygon':
        vertices = [PointF.from_dict(v) for v in data.get("vertices", [])]
        return cls(vertices=vertices)


@dataclass
class Ellipse:
    """椭圆"""
    center_x: float = 0.0
    center_y: float = 0.0
    major_radius: float = 0.0
    minor_radius: float = 0.0
    angle: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "center_x": self.center_x, "center_y": self.center_y,
            "major_radius": self.major_radius, "minor_radius": self.minor_radius,
            "angle": self.angle
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Ellipse':
        return cls(
            center_x=data.get("center_x", 0.0),
            center_y=data.get("center_y", 0.0),
            major_radius=data.get("major_radius", 0.0),
            minor_radius=data.get("minor_radius", 0.0),
            angle=data.get("angle", 0.0)
        )


@dataclass
class ClassInfo:
    """类别信息"""
    class_name: str = ""
    gray_value: int = 0

    def to_dict(self) -> Dict:
        return {"class_name": self.class_name, "gray_value": self.gray_value}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClassInfo':
        return cls(
            class_name=data.get("class_name", ""),
            gray_value=data.get("gray_value", 0)
        )


class IoDataFactory:
    """IO数据类型工厂类

    提供统一的数据创建和转换接口。
    """

    @staticmethod
    def create_int_data(values: Union[int, List[int]]) -> Dict:
        """创建整型数据"""
        if isinstance(values, int):
            values = [values]
        return {
            "type": IoType.INT.value,
            "value_num": len(values),
            "values": values
        }

    @staticmethod
    def create_float_data(values: Union[float, List[float]]) -> Dict:
        """创建浮点型数据"""
        if isinstance(values, (int, float)):
            values = [values]
        return {
            "type": IoType.FLOAT.value,
            "value_num": len(values),
            "values": values
        }

    @staticmethod
    def create_string_data(value: str) -> Dict:
        """创建字符串数据"""
        return {
            "type": IoType.STRING.value,
            "value": value
        }

    @staticmethod
    def create_byte_data(value: bytes) -> Dict:
        """创建二进制数据"""
        return {
            "type": IoType.BYTE.value,
            "data": value,
            "data_len": len(value)
        }

    @staticmethod
    def create_point_f_data(x: float, y: float) -> Dict:
        """创建浮点型点数据"""
        return {
            "type": IoType.POINT_F.value,
            "x": x,
            "y": y
        }

    @staticmethod
    def create_circle_data(center_x: float, center_y: float, radius: float) -> Dict:
        """创建圆数据"""
        return {
            "type": IoType.CIRCLE.value,
            "center_x": center_x,
            "center_y": center_y,
            "radius": radius
        }

    @staticmethod
    def create_rect_box_data(center_x: float, center_y: float, 
                             width: float, height: float, angle: float) -> Dict:
        """创建带角度矩形数据"""
        return {
            "type": IoType.ROIBOX.value,
            "center_x": center_x,
            "center_y": center_y,
            "width": width,
            "height": height,
            "angle": angle
        }

    @staticmethod
    def create_posture_data(x: float, y: float, theta: float) -> Dict:
        """创建位姿数据"""
        return {
            "type": IoType.POSTURE.value,
            "x": x,
            "y": y,
            "theta": theta
        }

    @staticmethod
    def create_fixture_data(x: float, y: float, angle: float, 
                            scale_x: float = 1.0, scale_y: float = 1.0) -> Dict:
        """创建位置修正数据"""
        return {
            "type": IoType.FIXTURE.value,
            "x": x,
            "y": y,
            "angle": angle,
            "scale_x": scale_x,
            "scale_y": scale_y
        }

    @staticmethod
    def serialize(data: Dict, format_type: str = "json") -> bytes:
        """序列化IO数据

        Args:
            data: IO数据字典
            format_type: 序列化格式 ("json", "binary", "text")

        Returns:
            序列化后的字节数据
        """
        if format_type == "json":
            return json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif format_type == "text":
            return str(data).encode('utf-8')
        elif format_type == "binary":
            # 二进制序列化（简化版本）
            return json.dumps(data).encode('utf-8')
        else:
            raise ValueError(f"不支持的序列化格式: {format_type}")

    @staticmethod
    def deserialize(data: bytes, format_type: str = "json") -> Dict:
        """反序列化IO数据

        Args:
            data: 字节数据
            format_type: 反序列化格式 ("json", "binary", "text")

        Returns:
            IO数据字典
        """
        if format_type == "json":
            return json.loads(data.decode('utf-8'))
        elif format_type == "text":
            return {"raw": data.decode('utf-8', errors='ignore')}
        elif format_type == "binary":
            return json.loads(data.decode('utf-8'))
        else:
            raise ValueError(f"不支持的反序列化格式: {format_type}")


class DynamicOutputParser:
    """动态输出解析器

    解析海康VisionMaster风格的动态输出数据。
    """

    @staticmethod
    def parse_output(output_data: Dict, output_type: str) -> Any:
        """解析输出数据

        Args:
            output_data: 输出数据字典
            output_type: 输出类型名称

        Returns:
            解析后的数据对象
        """
        io_type = output_data.get("type", IoType.NOTSUPPORT.value)
        
        if io_type == IoType.INT.value:
            return output_data.get("values", [])
        elif io_type == IoType.FLOAT.value:
            return output_data.get("values", [])
        elif io_type == IoType.STRING.value:
            return output_data.get("value", "")
        elif io_type == IoType.POINT_F.value:
            return PointF(
                x=output_data.get("x", 0.0),
                y=output_data.get("y", 0.0)
            )
        elif io_type == IoType.CIRCLE.value:
            return Circle(
                center_x=output_data.get("center_x", 0.0),
                center_y=output_data.get("center_y", 0.0),
                radius=output_data.get("radius", 0.0)
            )
        elif io_type == IoType.ROIBOX.value:
            return RectBox(
                center_x=output_data.get("center_x", 0.0),
                center_y=output_data.get("center_y", 0.0),
                width=output_data.get("width", 0.0),
                height=output_data.get("height", 0.0),
                angle=output_data.get("angle", 0.0)
            )
        elif io_type == IoType.POSTURE.value:
            return Posture(
                x=output_data.get("x", 0.0),
                y=output_data.get("y", 0.0),
                theta=output_data.get("theta", 0.0)
            )
        elif io_type == IoType.FIXTURE.value:
            return Fixture(
                x=output_data.get("x", 0.0),
                y=output_data.get("y", 0.0),
                angle=output_data.get("angle", 0.0),
                scale_x=output_data.get("scale_x", 1.0),
                scale_y=output_data.get("scale_y", 1.0)
            )
        else:
            return output_data


# 导出
__all__ = [
    'IoType',
    'PointF', 'PointI', 'Line', 'Circle', 'RectF', 'RectBox',
    'Fixture', 'Annulus', 'Posture', 'Polygon', 'Ellipse', 'ClassInfo',
    'IoDataFactory',
    'DynamicOutputParser'
]
