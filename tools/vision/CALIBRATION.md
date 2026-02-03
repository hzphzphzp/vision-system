# 标定工具使用指南

> Vision System 标定工具 (CalibrationTool) 文档

## 1. 概述

标定工具用于将图像中的像素坐标和尺寸转换为实际物理尺寸。支持多种标定方法：

- **手动标定**：通过输入参考物体尺寸进行标定
- **棋盘格标定**：自动检测棋盘格角点进行标定
- **圆点标定**：自动检测圆点阵列进行标定

## 2. 功能特性

### 2.1 坐标转换

- 像素坐标 → 物理坐标
- 物理坐标 → 像素坐标
- 像素尺寸 → 物理尺寸

### 2.2 单位支持

- **mm** (毫米)
- **inch** (英寸)
- **um** (微米)

### 2.3 标定参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| calibration_type | 标定类型 (manual/chessboard/circles) | manual |
| pixel_per_mm_x | X方向像素/毫米比例 | 10.0 |
| pixel_per_mm_y | Y方向像素/毫米比例 | 10.0 |
| reference_width | 参考物体宽度 (mm) | 100.0 |
| reference_height | 参考物体高度 (mm) | 100.0 |
| pattern_width | 棋盘格内角点宽度 | 9 |
| pattern_height | 棋盘格内角点高度 | 6 |
| square_size | 棋盘格方块尺寸 (mm) | 25.0 |
| output_unit | 输出单位 (mm/inch/um) | mm |

## 3. 使用方法

### 3.1 手动标定

```python
from tools.vision import CalibrationTool
from data.image_data import ImageData
import numpy as np

# 创建标定工具
calib = CalibrationTool(name="标定")

# 创建测试图像
image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
input_data = ImageData(data=image)

# 设置手动标定参数
calib.set_param('calibration_type', 'manual')
calib.set_param('pixel_per_mm_x', 10.0)
calib.set_param('pixel_per_mm_y', 10.0)
calib.set_param('reference_width', 100.0)
calib.set_param('reference_height', 100.0)

# 执行标定
calib.set_input(input_data)
result = calib.run()

# 检查标定状态
print("标定成功:", calib.is_calibrated)

# 像素坐标转物理坐标
phys_x, phys_y = calib.pixel_to_physical(100, 200)
print("像素 (100, 200) -> 物理 (mm):", (phys_x, phys_y))

# 物理坐标转像素坐标
px, py = calib.physical_to_pixel(10.0, 20.0)
print("物理 (10, 20) mm -> 像素:", (px, py))
```

### 3.2 棋盘格标定

```python
import cv2

# 创建标定工具
calib = CalibrationTool(name="标定")

# 加载棋盘格图像
image = cv2.imread("calibration_pattern.jpg")

# 设置棋盘格参数
calib.set_param('calibration_type', 'chessboard')
calib.set_param('pattern_width', 9)
calib.set_param('pattern_height', 6)
calib.set_param('square_size', 25.0)

# 执行自动标定
input_data = ImageData(data=image)
calib.set_input(input_data)
result = calib.run()

print("标定成功:", calib.is_calibrated)
print("X方向比例:", calib.pixel_per_mm_x)
print("Y方向比例:", calib.pixel_per_mm_y)
```

### 3.3 单位转换

```python
# 设置输出单位为英寸
calib.set_param('output_unit', 'inch')

# 转换像素到英寸
phys_x, phys_y = calib.pixel_to_physical(254, 508)  # 254像素 @ 10px/mm = 10英寸
print("像素 (254, 508) -> 英寸:", (phys_x, phys_y))

# 设置输出单位为微米
calib.set_param('output_unit', 'um')

# 转换像素到微米
phys_x, phys_y = calib.pixel_to_physical(10, 20)  # 10像素 @ 10px/mm = 1000微米
print("像素 (10, 20) -> 微米:", (phys_x, phys_y))
```

## 4. 与其他工具集成

### 4.1 与卡尺测量工具配合使用

```python
from tools.vision import CalibrationTool
from tools.analysis import Caliper

# 先进行标定
calib = CalibrationTool(name="标定")
# ... 设置标定参数 ...

# 创建卡尺工具
caliper = Caliper(name="卡尺测量")

# 使用标定结果进行测量
if calib.is_calibrated:
    # 获取标定比例
    pixel_per_mm = calib.pixel_per_mm_x

    # 执行卡尺测量
    # ... 测量代码 ...

    # 将测量结果转换为物理尺寸
    pixel_length = 100  # 卡尺测量的像素长度
    physical_length = pixel_length / pixel_per_mm
    print("测量结果:", physical_length, "mm")
```

## 5. API 参考

### CalibrationTool 类

```python
class CalibrationTool(ToolBase):
    def calibrate_with_reference(
        self,
        pixel_width: float,
        pixel_height: float,
        actual_width: float,
        actual_height: float
    ) -> bool:
        """手动标定（使用参考物体）"""

    def calibrate_with_chessboard(self, image: np.ndarray) -> bool:
        """棋盘格自动标定"""

    def pixel_to_physical(
        self,
        pixel_x: float,
        pixel_y: float
    ) -> Tuple[float, float]:
        """像素坐标转物理坐标"""

    def physical_to_pixel(
        self,
        physical_x: float,
        physical_y: float
    ) -> Tuple[float, float]:
        """物理坐标转像素坐标"""

    def pixel_to_physical_size(
        self,
        pixel_width: float,
        pixel_height: float
    ) -> Tuple[float, float]:
        """像素尺寸转物理尺寸"""

    @property
    def is_calibrated(self) -> bool:
        """是否已标定"""

    @property
    def pixel_per_mm(self) -> Tuple[float, float]:
        """像素/毫米比例 (x, y)"""
```

## 6. 常见问题

### Q: 标定失败怎么办？

1. 检查图像是否清晰
2. 确保参考物体完整可见
3. 对于棋盘格标定，确保角点清晰可检测
4. 调整光照条件，减少反光和阴影

### Q: 如何提高标定精度？

1. 使用高质量的标定板
2. 拍摄多张不同角度的标定图像
3. 确保标定板平整放置
4. 标定后验证几个已知尺寸的物体

### Q: 标定结果如何保存？

标定参数可以通过 `save_params()` 和 `load_params()` 方法保存和加载：

```python
# 保存标定参数
calib.save_params("calibration_params.npz")

# 加载标定参数
calib2 = CalibrationTool(name="标定2")
calib2.load_params("calibration_params.npz")
```

## 7. 测试

标定工具的测试用例位于 `tests/test_calibration.py`，包含以下测试：

- `test_calibration_tool_creation` - 测试工具创建
- `test_calibration_manual` - 测试手动标定
- `test_pixel_to_physical` - 测试像素到物理坐标转换
- `test_pixel_to_physical_size` - 测试像素尺寸到物理尺寸转换
- `test_physical_to_pixel` - 测试物理坐标到像素坐标转换
- `test_calibration_with_chessboard` - 测试棋盘格标定
- `test_calibration_tool_run` - 测试工具运行
- `test_unit_conversion` - 测试单位转换

运行测试：

```bash
pytest tests/test_calibration.py -v
```

## 8. 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-02-03 | 1.0 | 初始版本 |
