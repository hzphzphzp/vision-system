#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像数据封装模块

提供统一的图像数据结构ImageData，封装图像及其元数据，
方便在工具之间传递和进行处理。

Author: Vision System Team
Date: 2025-01-04
"""

import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

# 导入cv2用于图像处理
try:
    import cv2
except ImportError:
    import warnings
    warnings.warn("OpenCV未安装，ImageData的某些功能将不可用")


class PixelFormat(Enum):
    """像素格式枚举"""

    MONO8 = "Mono8"
    RGB24 = "RGB24"
    BGR24 = "BGR24"
    RGBA32 = "RGBA32"
    BGRA32 = "BGRA32"


class ImageDataType(Enum):
    """图像数据类型"""

    GRAY = "gray"
    COLOR = "color"
    DEPTH = "depth"


@dataclass
class ROI:
    """感兴趣区域(ROI)"""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        """参数校验"""
        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        if self.width < 0:
            self.width = 0
        if self.height < 0:
            self.height = 0

    def copy(self) -> "ROI":
        """创建拷贝"""
        return ROI(self.x, self.y, self.width, self.height)

    def is_valid(self, image_width: int, image_height: int) -> bool:
        """检查ROI是否有效"""
        return (
            self.x >= 0
            and self.y >= 0
            and self.x + self.width <= image_width
            and self.y + self.height <= image_height
        )

    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "ROI":
        """从字典创建"""
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
        )


class ImageData:
    """
    图像数据结构，封装图像及其元数据

    特点：
    - 支持多种图像格式
    - 自动管理图像元数据
    - 线程安全的只读属性
    - 方便的数据转换方法

    示例：
        # 从文件加载图像
        image = ImageData.from_file("test.jpg")

        # 从相机获取图像
        image = ImageData(camera_frame)

        # 获取ROI区域
        roi_image = image.get_roi(ROI(100, 100, 200, 200))

        # 转换为灰度
        gray_image = image.to_gray()
    """

    __slots__ = (
        '_data', '_timestamp', '_roi', '_camera_id', '_pixel_format',
        '_image_type', '_metadata', '_height', '_width', '_channels'
    )

    def __init__(
        self,
        data: np.ndarray = None,
        width: int = None,
        height: int = None,
        channels: int = None,
        timestamp: float = None,
        roi: ROI = None,
        camera_id: str = None,
        pixel_format: PixelFormat = None,
        image_type: ImageDataType = None,
    ):
        """
        初始化图像数据

        Args:
            data: 图像数据，numpy数组，格式为BGR或灰度
            width: 图像宽度，如果为None则从data.shape[1]获取
            height: 图像高度，如果为None则从data.shape[0]获取
            channels: 通道数，如果为None则从data.shape推断
            timestamp: 时间戳，默认为当前时间
            roi: 感兴趣区域
            camera_id: 相机ID
            pixel_format: 像素格式
            image_type: 图像类型
        """
        self._data = data.copy() if data is not None else None
        self._timestamp = timestamp or time.time()
        self._roi = roi
        self._camera_id = camera_id
        self._pixel_format = pixel_format
        self._image_type = image_type
        self._metadata: Dict[str, Any] = {}

        # 自动推断元数据
        if self._data is not None:
            self._height = self._data.shape[0]
            self._width = self._data.shape[1]
            self._channels = (
                self._data.shape[2] if len(self._data.shape) > 2 else 1
            )

            # 如果提供了参数且不为None，使用提供的值
            if width is not None:
                self._width = width
            if height is not None:
                self._height = height
            if channels is not None:
                self._channels = channels

            # 推断图像类型
            if self._image_type is None:
                if self._channels == 1:
                    self._image_type = ImageDataType.GRAY
                else:
                    self._image_type = ImageDataType.COLOR

            # 推断像素格式
            if self._pixel_format is None:
                if self._channels == 1:
                    self._pixel_format = PixelFormat.MONO8
                elif self._channels == 3:
                    self._pixel_format = PixelFormat.BGR24
                elif self._channels == 4:
                    self._pixel_format = PixelFormat.BGRA32
        else:
            # 处理空数据的情况
            self._width = width if width is not None else 0
            self._height = height if height is not None else 0
            self._channels = channels if channels is not None else 1
            self._image_type = image_type or ImageDataType.GRAY
            self._pixel_format = pixel_format or PixelFormat.MONO8

    @property
    def data(self) -> np.ndarray:
        """获取图像数据"""
        return self._data if self._data is not None else np.array([])

    @data.setter
    def data(self, value: np.ndarray):
        """设置图像数据"""
        self._data = value.copy() if value is not None else None
        if value is not None:
            self._height = value.shape[0]
            self._width = value.shape[1]
            self._channels = value.shape[2] if len(value.shape) > 2 else 1

    def set_data(self, value: np.ndarray):
        """设置图像数据（兼容方法）"""
        self.data = value

    @property
    def width(self) -> int:
        """获取图像宽度"""
        return self._width

    @property
    def height(self) -> int:
        """获取图像高度"""
        return self._height

    @property
    def channels(self) -> int:
        """获取通道数"""
        return self._channels

    @property
    def shape(self) -> tuple:
        """获取图像形状 (height, width, channels)"""
        if self._channels == 1:
            return (self._height, self._width)
        return (self._height, self._width, self._channels)

    @property
    def timestamp(self) -> float:
        """获取时间戳"""
        return self._timestamp

    @property
    def roi(self) -> Optional[ROI]:
        """获取ROI"""
        return self._roi

    @roi.setter
    def roi(self, value: ROI):
        """设置ROI"""
        self._roi = value

    @property
    def camera_id(self) -> Optional[str]:
        """获取相机ID"""
        return self._camera_id

    @camera_id.setter
    def camera_id(self, value: str):
        """设置相机ID"""
        self._camera_id = value

    @property
    def pixel_format(self) -> PixelFormat:
        """获取像素格式"""
        return self._pixel_format

    @property
    def image_type(self) -> ImageDataType:
        """获取图像类型"""
        return self._image_type

    @property
    def is_gray(self) -> bool:
        """是否为灰度图像"""
        return self._channels == 1

    @property
    def is_color(self) -> bool:
        """是否为彩色图像"""
        return self._channels >= 3

    @property
    def is_valid(self) -> bool:
        """图像是否有效"""
        return self._data is not None and self._data.size > 0

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self._metadata[key] = value

    def copy(self) -> "ImageData":
        """创建深拷贝"""
        return ImageData(
            data=self._data.copy() if self._data is not None else None,
            width=self._width,
            height=self._height,
            channels=self._channels,
            timestamp=self._timestamp,
            roi=self._roi.copy() if self._roi else None,
            camera_id=self._camera_id,
            pixel_format=self._pixel_format,
            image_type=self._image_type,
        )

    def to_gray(self) -> "ImageData":
        """转换为灰度图像"""
        if not self.is_valid:
            return self.copy()

        if self.is_gray:
            return self.copy()

        if self._channels == 3:
            gray_data = cv2.cvtColor(self._data, cv2.COLOR_BGR2GRAY)
        else:
            gray_data = self._data.copy()

        return ImageData(
            data=gray_data,
            width=self._width,
            height=self._height,
            channels=1,
            timestamp=self._timestamp,
            roi=self._roi.copy() if self._roi else None,
            camera_id=self._camera_id,
            pixel_format=PixelFormat.MONO8,
            image_type=ImageDataType.GRAY,
        )

    def to_rgb(self) -> "ImageData":
        """转换为RGB图像"""
        if not self.is_valid:
            return self.copy()

        if self._channels == 1:
            rgb_data = cv2.cvtColor(self._data, cv2.COLOR_GRAY2RGB)
        elif self._channels == 3:
            rgb_data = cv2.cvtColor(self._data, cv2.COLOR_BGR2RGB)
        elif self._channels == 4:
            rgb_data = cv2.cvtColor(self._data, cv2.COLOR_BGRA2RGBA)
        else:
            return self.copy()

        return ImageData(
            data=rgb_data,
            width=self._width,
            height=self._height,
            channels=3,
            timestamp=self._timestamp,
            roi=self._roi.copy() if self._roi else None,
            camera_id=self._camera_id,
            pixel_format=PixelFormat.RGB24,
            image_type=ImageDataType.COLOR,
        )

    def to_bgr(self) -> "ImageData":
        """转换为BGR图像"""
        if not self.is_valid:
            return self.copy()

        if self._channels == 1:
            bgr_data = cv2.cvtColor(self._data, cv2.COLOR_GRAY2BGR)
        elif self._channels == 3:
            bgr_data = cv2.cvtColor(self._data, cv2.COLOR_RGB2BGR)
        elif self._channels == 4:
            bgr_data = cv2.cvtColor(self._data, cv2.COLOR_RGBA2BGRA)
        else:
            return self.copy()

        return ImageData(
            data=bgr_data,
            width=self._width,
            height=self._height,
            channels=3,
            timestamp=self._timestamp,
            roi=self._roi.copy() if self._roi else None,
            camera_id=self._camera_id,
            pixel_format=PixelFormat.BGR24,
            image_type=ImageDataType.COLOR,
        )

    def get_roi(self, roi: ROI = None) -> "ImageData":
        """获取ROI区域图像"""
        if not self.is_valid:
            return self.copy()

        target_roi = roi or self._roi
        if target_roi is None:
            return self.copy()

        # 检查ROI有效性
        if not target_roi.is_valid(self._width, self._height):
            return self.copy()

        # 提取ROI区域
        roi_data = self._data[
            target_roi.y : target_roi.y + target_roi.height,
            target_roi.x : target_roi.x + target_roi.width,
        ].copy()

        return ImageData(
            data=roi_data,
            width=target_roi.width,
            height=target_roi.height,
            channels=self._channels,
            timestamp=self._timestamp,
            roi=target_roi.copy(),
            camera_id=self._camera_id,
            pixel_format=self._pixel_format,
            image_type=self._image_type,
        )

    def resize(
        self, width: int, height: int, interpolation: int = None
    ) -> "ImageData":
        """
        调整图像大小

        Args:
            width: 目标宽度
            height: 目标高度
            interpolation: 插值方法，默认为cv2.INTER_LINEAR

        Returns:
            调整大小后的图像
        """
        if not self.is_valid:
            return self.copy()

        if interpolation is None:
            interpolation = cv2.INTER_LINEAR

        resized_data = cv2.resize(
            self._data, (width, height), interpolation=interpolation
        )

        return ImageData(
            data=resized_data,
            width=width,
            height=height,
            channels=self._channels,
            timestamp=self._timestamp,
            roi=None,  # ROI不保留
            camera_id=self._camera_id,
            pixel_format=self._pixel_format,
            image_type=self._image_type,
        )

    def clone(self) -> "ImageData":
        """创建深拷贝"""
        return self.copy()

    @classmethod
    def from_file(cls, file_path: str) -> "ImageData":
        """
        从文件加载图像

        Args:
            file_path: 文件路径

        Returns:
            ImageData对象，如果加载失败返回None
        """
        import cv2

        data = cv2.imread(file_path)
        if data is None:
            return None

        return cls(data=data)

    @classmethod
    def from_camera(cls, camera_id: str, frame: np.ndarray) -> "ImageData":
        """
        从相机帧创建ImageData

        Args:
            camera_id: 相机ID
            frame: 相机帧

        Returns:
            ImageData对象
        """
        return cls(data=frame, camera_id=camera_id, timestamp=time.time())

    @classmethod
    def create_empty(
        cls, width: int = 0, height: int = 0, channels: int = 1
    ) -> "ImageData":
        """
        创建空图像

        Args:
            width: 宽度
            height: 高度
            channels: 通道数

        Returns:
            ImageData对象
        """
        data = np.zeros((height, width, channels), dtype=np.uint8)
        return cls(data=data)

    def __del__(self):
        """析构函数"""
        if hasattr(self, "_data"):
            del self._data

    def __repr__(self) -> str:
        return (
            f"ImageData(width={self._width}, height={self._height}, "
            f"channels={self._channels}, timestamp={self._timestamp:.6f})"
        )


class DataType(Enum):
    """数据类型枚举"""

    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool"
    POINT = "point"
    RECT = "rect"
    LINE = "line"
    CIRCLE = "circle"
    POLYGON = "polygon"
    IMAGE = "image"
    ARRAY = "array"
    DICT = "dict"
    UNKNOWN = "unknown"


class ResultData:
    """
    结果数据类，封装算法检测结果

    支持多种结果类型：
    - 数值结果 (int, float)
    - 字符串结果 (str)
    - 几何结果 (点, 线, 圆, 矩形)
    - 图像结果

    支持数据类型信息记录
    """

    def __init__(self):
        self._values: Dict[str, Any] = {}
        self._value_types: Dict[str, DataType] = {}
        self._images: Dict[str, ImageData] = {}
        self._status = True
        self._message = "Success"
        self._error_code = None
        self._error_type = None
        self._timestamp = time.time()
        self._tool_name = ""
        self._result_category = ""

    @property
    def status(self) -> bool:
        """获取状态"""
        return self._status

    @status.setter
    def status(self, value: bool):
        """设置状态"""
        self._status = value

    @property
    def message(self) -> str:
        """获取消息"""
        return self._message

    @message.setter
    def message(self, value: str):
        """设置消息"""
        self._message = value

    @property
    def timestamp(self) -> float:
        """获取时间戳"""
        return self._timestamp

    @property
    def tool_name(self) -> str:
        """获取工具名称"""
        return self._tool_name

    @tool_name.setter
    def tool_name(self, value: str):
        """设置工具名称"""
        self._tool_name = value

    @property
    def result_category(self) -> str:
        """获取结果类别"""
        return self._result_category

    @result_category.setter
    def result_category(self, value: str):
        """设置结果类别"""
        self._result_category = value

    @property
    def error_code(self) -> Optional[int]:
        """获取错误代码"""
        return self._error_code

    @error_code.setter
    def error_code(self, value: Optional[int]):
        """设置错误代码"""
        self._error_code = value

    @property
    def error_type(self) -> Optional[str]:
        """获取错误类型"""
        return self._error_type

    @error_type.setter
    def error_type(self, value: Optional[str]):
        """设置错误类型"""
        self._error_type = value

    def _detect_data_type(self, value: Any) -> DataType:
        """自动检测数据类型"""
        if isinstance(value, bool):
            return DataType.BOOL
        elif isinstance(value, int):
            return DataType.INT
        elif isinstance(value, float):
            return DataType.FLOAT
        elif isinstance(value, str):
            return DataType.STRING
        elif isinstance(value, dict):
            if "x" in value and "y" in value and len(value) == 2:
                return DataType.POINT
            elif (
                "x" in value
                and "y" in value
                and "width" in value
                and "height" in value
            ):
                return DataType.RECT
            elif "cx" in value and "cy" in value and "r" in value:
                return DataType.CIRCLE
            elif (
                "x1" in value
                and "y1" in value
                and "x2" in value
                and "y2" in value
            ):
                return DataType.LINE
            elif "points" in value:
                return DataType.POLYGON
            return DataType.DICT
        elif isinstance(value, (list, tuple)):
            return DataType.ARRAY
        elif hasattr(value, "data"):
            return DataType.IMAGE
        return DataType.UNKNOWN

    def set_value(self, key: str, value: Any, data_type: DataType = None):
        """设置数值结果

        Args:
            key: 键名
            value: 值
            data_type: 数据类型（可选，自动检测）
        """
        if key == "message":
            self.message = str(value)
        else:
            self._values[key] = value
            if data_type is None:
                data_type = self._detect_data_type(value)
            self._value_types[key] = data_type

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取数值结果"""
        return self._values.get(key, default)

    def get_value_type(self, key: str) -> DataType:
        """获取值的类型"""
        return self._value_types.get(key, DataType.UNKNOWN)

    def get_all_values(self) -> Dict[str, Any]:
        """获取所有数值结果"""
        return self._values.copy()

    def get_all_value_types(self) -> Dict[str, DataType]:
        """获取所有值类型"""
        return self._value_types.copy()

    def get_values_with_types(self) -> List[Tuple[str, Any, DataType]]:
        """获取所有值及其类型"""
        return [
            (k, v, self._value_types.get(k, DataType.UNKNOWN))
            for k, v in self._values.items()
        ]

    def set_image(self, key: str, image: ImageData):
        """设置图像结果"""
        self._images[key] = image
        self._value_types[key] = DataType.IMAGE

    def get_image(self, key: str) -> Optional[ImageData]:
        """获取图像结果"""
        return self._images.get(key)

    def has_value(self, key: str) -> bool:
        """检查是否存在值"""
        return key in self._values

    def has_image(self, key: str) -> bool:
        """检查是否存在图像"""
        return key in self._images

    def clear(self):
        """清空结果"""
        self._values.clear()
        self._value_types.clear()
        self._images.clear()
        self._status = True
        self._message = ""
        self._error_code = None
        self._error_type = None
        self._timestamp = time.time()
        self._tool_name = ""
        self._result_category = ""

    def copy(self) -> "ResultData":
        """创建拷贝"""
        result = ResultData()
        result._values = self._values.copy()
        result._value_types = self._value_types.copy()
        result._images = {k: v.copy() for k, v in self._images.items()}
        result._status = self._status
        result._message = self._message
        result._error_code = self._error_code
        result._error_type = self._error_type
        result._tool_name = self._tool_name
        result._result_category = self._result_category
        return result

    @property
    def is_valid(self) -> bool:
        """结果是否有效"""
        return self._status
