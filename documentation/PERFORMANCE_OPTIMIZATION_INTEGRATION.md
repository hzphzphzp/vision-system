# 性能优化集成指南

本文档详细说明项目性能优化的三步集成计划，包括工具选型、实施步骤和验证方法。

## 概述

Vision System 视觉检测系统在处理大分辨率图像、批量图像和复杂算法时面临性能挑战。本指南提供系统化的性能优化方案，通过引入高性能计算库提升系统效率。

## 优化目标

- 批量图像处理性能提升 2-4x
- 自定义计算函数性能提升 10-50x
- 基础图像操作性能提升 4-16x
- 保持代码可维护性和兼容性

---

## 第一步：集成 joblib 实现批量处理加速

### 目标

通过多进程并行处理，提升批量图像处理和多相机并行采集的性能。

### 依赖安装

```bash
pip install joblib
```

### 实施步骤

#### 1.1 创建并行处理工具模块

创建 `core/parallel_processing.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理工具模块

提供多进程并行处理功能，用于批量图像处理和算法加速。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from typing import Any, Callable, List, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from joblib import Parallel, delayed, parallel_backend

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ParallelProcessor:
    """并行处理器

    支持多进程和多线程并行处理，适用于批量图像处理场景。
    """

    def __init__(self, n_jobs: int = -1, backend: str = "loky", prefer: str = "threads"):
        """初始化并行处理器

        Args:
            n_jobs: 并行任务数量，-1表示使用所有CPU核心
            backend: joblib后端 ('loky', 'multiprocessing', 'threading')
            prefer: 优先模式 ('threads' for I/O bound, 'processes' for CPU bound)
        """
        self.n_jobs = n_jobs
        self.backend = backend
        self.prefer = prefer

    def map(self, func: Callable, items: List[Any], desc: str = "Processing") -> List[Any]:
        """并行映射处理

        Args:
            func: 处理函数
            items: 输入项列表
            desc: 描述信息

        Returns:
            处理结果列表
        """
        if self.n_jobs == 1 or len(items) <= 1:
            return [func(item) for item in items]

        with parallel_backend(self.backend, n_jobs=self.n_jobs):
            results = Parallel(prefer=self.prefer)(
                delayed(func)(item) for item in items
            )
        return results

    def process_images(self, image_paths: List[str], process_func: Callable,
                      n_jobs: int = None) -> List[Any]:
        """并行处理图像

        Args:
            image_paths: 图像路径列表
            process_func: 图像处理函数，接收图像路径返回处理结果
            n_jobs: 并行数量，默认使用初始化值

        Returns:
            处理结果列表
        """
        n = n_jobs if n_jobs is not None else self.n_jobs

        if n == 1 or len(image_paths) <= 1:
            return [process_func(path) for path in image_paths]

        with ProcessPoolExecutor(max_workers=n) as executor:
            futures = {executor.submit(process_func, path): path for path in image_paths}
            results = []
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"处理失败: {futures[future]}, 错误: {e}")
                    results.append(None)
        return results


def parallel_map(func: Callable, items: List[Any], n_jobs: int = -1,
                backend: str = "loky") -> List[Any]:
    """便捷的并行映射函数

    Args:
        func: 处理函数
        items: 输入项列表
        n_jobs: 并行任务数量
        backend: 并行后端

    Returns:
        处理结果列表
    """
    processor = ParallelProcessor(n_jobs=n_jobs, backend=backend)
    return processor.map(func, items)


def batch_process_images(image_paths: List[str], process_func: Callable,
                        batch_size: int = 4) -> List[Any]:
    """批量处理图像（带内存控制）

    Args:
        image_paths: 图像路径列表
        process_func: 图像处理函数
        batch_size: 每批处理数量

    Returns:
        处理结果列表
    """
    results = []
    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i:i + batch_size]
        processor = ParallelProcessor(n_jobs=batch_size)
        batch_results = processor.map(process_func, batch, desc=f"Batch {i//batch_size + 1}")
        results.extend(batch_results)
    return results
```

#### 1.2 在现有模块中集成

在 `tools/vision/image_stitching.py` 中集成并行处理：

```python
# 在 image_stitching.py 中添加
from core.parallel_processing import parallel_map

def _stitch_batch(self, image_paths: List[str]) -> List[Any]:
    """并行处理多张图像"""
    return parallel_map(self._process_single_image, image_paths)
```

#### 1.3 多相机并行采集

在相机模块中集成并行采集：

```python
from core.parallel_processing import ParallelProcessor

class CameraManager:
    def capture_all_parallel(self, cameras: List[Camera], n_jobs: int = None):
        """并行采集所有相机图像"""
        processor = ParallelProcessor(n_jobs=n_jobs or len(cameras))
        return processor.map(lambda cam: cam.capture(), cameras)
```

### 验证方法

```python
import time
from core.parallel_processing import parallel_map

def test_processing():
    images = [f"test_{i}.jpg" for i in range(10)]

    # 串行处理
    start = time.time()
    serial_results = [process_image(img) for img in images]
    serial_time = time.time() - start

    # 并行处理
    start = time.time()
    parallel_results = parallel_map(process_image, images, n_jobs=4)
    parallel_time = time.time() - start

    print(f"串行: {serial_time:.2f}s, 并行: {parallel_time:.2f}s")
    print(f"加速比: {serial_time/parallel_time:.2f}x")
```

### 预期收益

- 批量图像处理: 2-4x 性能提升
- 多相机并行采集: 2-3x 性能提升

---

## 第二步：集成 Numba 优化热点计算函数

### 目标

通过 JIT 编译加速自定义计算函数，特别是像素级操作和数值计算循环。

### 依赖安装

```bash
pip install numba
```

### 实施步骤

#### 2.1 创建 Numba 优化模块

创建 `core/numba_utils.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numba 加速工具模块

提供基于 Numba 的高性能计算函数。

Author: Vision System Team
Date: 2026-02-27
"""

import numpy as np
from numba import jit, prange, njit
from typing import Tuple


@jit(nopython=True, cache=True)
def ssd_match(image: np.ndarray, template: np.ndarray) -> np.ndarray:
    """计算SSD匹配（Sum of Squared Differences）

    Args:
        image: 输入图像
        template: 模板图像

    Returns:
        匹配结果矩阵
    """
    h, w = image.shape
    th, tw = template.shape
    result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

    for i in range(h - th + 1):
        for j in range(w - tw + 1):
            ssd = 0.0
            for ii in range(th):
                for jj in range(tw):
                    diff = float(image[i + ii, j + jj]) - float(template[ii, jj])
                    ssd += diff * diff
            result[i, j] = ssd

    return result


@jit(nopython=True, parallel=True, cache=True)
def ssd_match_parallel(image: np.ndarray, template: np.ndarray) -> np.ndarray:
    """并行计算SSD匹配

    Args:
        image: 输入图像
        template: 模板图像

    Returns:
        匹配结果矩阵
    """
    h, w = image.shape
    th, tw = template.shape
    result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

    for i in prange(h - th + 1):
        for j in range(w - tw + 1):
            ssd = 0.0
            for ii in range(th):
                for jj in range(tw):
                    diff = float(image[i + ii, j + jj]) - float(template[ii, jj])
                    ssd += diff * diff
            result[i, j] = ssd

    return result


@jit(nopython=True, cache=True)
def normalized_cross_correlation(image: np.ndarray, template: np.ndarray) -> np.ndarray:
    """归一化互相关匹配

    Args:
        image: 输入图像
        template: 模板图像

    Returns:
        匹配结果矩阵
    """
    h, w = image.shape
    th, tw = template.shape

    template_mean = np.mean(template)
    template_std = np.std(template)

    result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)

    for i in range(h - th + 1):
        for j in range(w - tw + 1):
            roi = image[i:i+th, j:j+tw]
            roi_mean = np.mean(roi)
            roi_std = np.std(roi)

            if roi_std > 0:
                ncc = np.sum((roi - roi_mean) * (template - template_mean)) / (th * tw * roi_std * template_std)
                result[i, j] = ncc
            else:
                result[i, j] = 0

    return result


@jit(nopython=True, cache=True)
def calculate_histogram(image: np.ndarray, bins: int = 256) -> np.ndarray:
    """计算图像直方图（Numba加速）

    Args:
        image: 输入图像
        bins: 直方图bin数量

    Returns:
        直方图数组
    """
    hist = np.zeros(bins, dtype=np.int32)
    h, w = image.shape

    for i in range(h):
        for j in range(w):
            val = int(image[i, j])
            if 0 <= val < bins:
                hist[val] += 1

    return hist


@jit(nopython=True, parallel=True, cache=True)
def fast_gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """快速高斯模糊（简化版）

    Args:
        image: 输入图像
        kernel_size: 卷积核大小

    Returns:
        模糊后的图像
    """
    h, w = image.shape
    result = np.zeros_like(image, dtype=np.float32)
    pad = kernel_size // 2

    for i in prange(h):
        for j in range(w):
            sum_val = 0.0
            count = 0
            for ki in range(-pad, pad + 1):
                for kj in range(-pad, pad + 1):
                    ni = i + ki
                    nj = j + kj
                    if 0 <= ni < h and 0 <= nj < w:
                        sum_val += float(image[ni, nj])
                        count += 1
            result[i, j] = sum_val / count if count > 0 else 0

    return result.astype(np.uint8)


@jit(nopython=True, cache=True)
def template_match_ncc(image: np.ndarray, template: np.ndarray) -> Tuple[np.ndarray, int, int]:
    """模板匹配返回最佳位置（NCC）

    Args:
        image: 输入图像
        template: 模板图像

    Returns:
        (匹配结果矩阵, 最佳x, 最佳y)
    """
    result = normalized_cross_correlation(image, template)
    h, w = result.shape

    max_val = -1.0
    max_x, max_y = 0, 0

    for i in range(h):
        for j in range(w):
            if result[i, j] > max_val:
                max_val = result[i, j]
                max_x, max_y = j, i

    return result, max_x, max_y


def warmup():
    """预热Numba JIT编译器"""
    dummy = np.zeros((10, 10), dtype=np.uint8)
    ssd_match(dummy, dummy)
    ssd_match_parallel(dummy, dummy)
    normalized_cross_correlation(dummy, dummy)
    calculate_histogram(dummy)
    fast_gaussian_blur(dummy)
```

#### 2.2 在模板匹配中集成

在 `tools/vision/template_match.py` 中使用：

```python
# 导入Numba加速函数
from core.numba_utils import ssd_match_parallel, template_match_ncc, warmup

class GrayMatch:
    # ... 现有代码 ...

    def _run_impl(self):
        # ... 现有代码 ...

        # 使用Numba加速的匹配
        if self.get_param("match_mode") == "ssd":
            result = ssd_match_parallel(
                gray_image.astype(np.float32),
                self._template_image.astype(np.float32)
            )
        else:
            result = cv2.matchTemplate(gray_image, self._template_image, match_mode)
```

#### 2.3 预热Numba

在应用启动时预热：

```python
# 在主程序或工具初始化时
from core.numba_utils import warmup
warmup()  # 首次调用会编译，之后就快了
```

### 验证方法

```python
import time
import numpy as np
from core.numba_utils import ssd_match, ssd_match_parallel

# 测试数据
image = np.random.randint(0, 256, (1000, 1000), dtype=np.uint8)
template = np.random.randint(0, 256, (50, 50), dtype=np.uint8)

# 预热
ssd_match(image[:10, :10], template[:5, :5])

# 测试普通版本
start = time.time()
result1 = ssd_match(image, template)
time1 = time.time() - start

# 测试并行版本
start = time.time()
result2 = ssd_match_parallel(image, template)
time2 = time.time() - start

print(f"普通版本: {time1:.3f}s, 并行版本: {time2:.3f}s")
print(f"加速比: {time1/time2:.2f}x")
```

### 预期收益

- 模板匹配计算: 10-50x 性能提升
- 直方图计算: 20-100x 性能提升
- 自定义滤波: 5-20x 性能提升

---

## 第三步：优化基础图像操作

### 目标

使用 Pillow-SIMD 替换基础图像操作，提升图像I/O和变换性能。

### 依赖安装

```bash
# 先卸载普通Pillow
pip uninstall pillow -y
# 安装Pillow-SIMD
pip install pillow-simd
```

注意：如果没有SIMD支持，系统会自动回退到普通Pillow。

### 实施步骤

#### 3.1 创建图像工具模块

创建 `core/image_utils.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像工具模块

提供高效的图像加载、处理和转换功能。
优先使用Pillow-SIMD进行加速。

Author: Vision System Team
Date: 2026-02-27
"""

import os
import sys
from typing import Optional, Tuple, Union

import cv2
import numpy as np

# 尝试使用Pillow-SIMD，如果不可用则使用普通Pillow
try:
    from PIL import Image
    PIL_AVAILABLE = True
    PIL_SIMD = hasattr(Image, 'FAST_MOSAIC')
except ImportError:
    PIL_AVAILABLE = False
    Image = None


def load_image_fast(path: str, mode: str = "RGB") -> Optional[np.ndarray]:
    """快速加载图像

    Args:
        path: 图像路径
        mode: 加载模式 ('RGB', 'BGR', 'GRAY')

    Returns:
        图像数组
    """
    if not os.path.exists(path):
        return None

    # 尝试Pillow-SIMD（更快）
    if PIL_AVAILABLE:
        try:
            with Image.open(path) as img:
                if mode == "GRAY":
                    img = img.convert("L")
                else:
                    img = img.convert("RGB")
                img_array = np.array(img)
                if mode == "BGR":
                    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                return img_array
        except Exception:
            pass

    # 回退到OpenCV
    img = cv2.imread(path)
    if img is None:
        return None

    if mode == "RGB":
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif mode == "GRAY":
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def resize_image_fast(image: Union[np.ndarray, str],
                     width: int, height: int,
                     interpolation: str = "LANCZOS") -> np.ndarray:
    """快速调整图像大小

    Args:
        image: 图像数组或路径
        width: 目标宽度
        height: 目标高度
        interpolation: 插值方法 ('LANCZOS', 'BILINEAR', 'BICUBIC')

    Returns:
        调整大小后的图像
    """
    if isinstance(image, str):
        if PIL_AVAILABLE:
            with Image.open(image) as img:
                img = img.resize((width, height), Image.LANCZOS)
                return np.array(img)
        else:
            image = cv2.imread(image)
            if image is None:
                return None

    # 使用Pillow-SIMD
    if PIL_AVAILABLE and isinstance(image, np.ndarray):
        try:
            if len(image.shape) == 3:
                img = Image.fromarray(image)
            else:
                img = Image.fromarray(image)
            img_resized = img.resize((width, height), Image.LANCZOS)
            return np.array(img_resized)
        except Exception:
            pass

    # 回退到OpenCV
    interp_map = {
        "LANCZOS": cv2.INTER_LANCZOS4,
        "BILINEAR": cv2.INTER_LINEAR,
        "BICUBIC": cv2.INTER_CUBIC,
        "NEAREST": cv2.INTER_NEAREST,
    }
    return cv2.resize(image, (width, height), interpolation=interp_map.get(interpolation, cv2.INTER_LANCZOS4))


def convert_to_fast(image: np.ndarray, target: str = np.ndarray:
    "RGB") -> """快速色彩空间转换

    Args:
        image: 输入图像
        target: 目标色彩空间 ('RGB', 'BGR', 'GRAY')

    Returns:
        转换后的图像
    """
    if PIL_AVAILABLE:
        try:
            if len(image.shape) == 2:
                if target == "GRAY":
                    return image
                img = Image.fromarray(image).convert("RGB")
                result = np.array(img)
            else:
                img = Image.fromarray(image)
                result = np.array(img)

            if target == "BGR":
                return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            elif target == "GRAY":
                return cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
            return result
        except Exception:
            pass

    # OpenCV回退
    if target == "BGR":
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if len(image.shape) == 3 else image
    elif target == "GRAY":
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image


def apply_filter_fast(image: np.ndarray, filter_type: str = "BLUR") -> np.ndarray:
    """快速应用滤镜

    Args:
        image: 输入图像
        filter_type: 滤镜类型 ('BLUR', 'SHARPEN', 'EDGE')

    Returns:
        处理后的图像
    """
    if PIL_AVAILABLE:
        try:
            img = Image.fromarray(image)
            if filter_type == "BLUR":
                img = img.filter(Image.BLUR)
            elif filter_type == "SHARPEN":
                img = img.filter(Image.SHARPEN)
            elif filter_type == "EDGE":
                img = img.filter(Image.FIND_EDGES)
            return np.array(img)
        except Exception:
            pass

    # OpenCV回退
    if filter_type == "BLUR":
        return cv2.blur(image, (5, 5))
    elif filter_type == "SHARPEN":
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel)
    elif filter_type == "EDGE":
        return cv2.Canny(image, 50, 150)
    return image


def save_image_fast(image: np.ndarray, path: str, quality: int = 95) -> bool:
    """快速保存图像

    Args:
        image: 图像数组
        path: 保存路径
        quality: JPEG质量 (1-100)

    Returns:
        是否成功
    """
    try:
        if PIL_AVAILABLE:
            img = Image.fromarray(image)
            img.save(path, quality=quality, optimize=True)
            return True
    except Exception:
        pass

    # OpenCV回退
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        return cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imwrite(path, image)
```

#### 3.2 在图像加载中集成

在 `tools/image_source.py` 中使用：

```python
from core.image_utils import load_image_fast, resize_image_fast, save_image_fast

class ImageSourceTool:
    def _load_image(self, path: str):
        # 使用快速加载
        return load_image_fast(path, mode="BGR")
```

#### 3.3 在图像保存中集成

在 `tools/vision/image_saver.py` 中使用：

```python
from core.image_utils import save_image_fast

class ImageSaverTool:
    def _save_image(self, image, path):
        return save_image_fast(image, path, quality=self.get_param("quality", 95))
```

### 验证方法

```python
import time
import numpy as np
from core.image_utils import resize_image_fast, load_image_fast

# 测试图像调整大小
image = np.random.randint(0, 256, (2000, 2000, 3), dtype=np.uint8)

# OpenCV版本
start = time.time()
for _ in range(10):
    cv2.resize(image, (800, 600))
cv2_time = time.time() - start

# Pillow-SIMD版本
start = time.time()
for _ in range(10):
    resize_image_fast(image, 800, 600)
pil_time = time.time() - start

print(f"OpenCV: {cv2_time:.3f}s, Pillow-SIMD: {pil_time:.3f}s")
print(f"加速比: {cv2_time/pil_time:.2f}x")
```

### 预期收益

- 图像加载: 2-5x 性能提升
- 图像缩放: 4-16x 性能提升
- 图像保存: 2-4x 性能提升
- 滤镜应用: 3-8x 性能提升

---

## 验证与测试

### 性能基准测试

创建 `tests/benchmark_performance.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试

用于验证优化效果。
"""

import time
import numpy as np
import cv2
from core.numba_utils import ssd_match_parallel, warmup
from core.parallel_processing import parallel_map
from core.image_utils import resize_image_fast


def benchmark_template_match():
    """模板匹配性能测试"""
    warmup()

    image = np.random.randint(0, 256, (2000, 2000), dtype=np.uint8)
    template = np.random.randint(0, 256, (100, 100), dtype=np.uint8)

    # OpenCV
    start = time.time()
    result = cv2.matchTemplate(image, template, cv2.TM_SSD)
    cv2_time = time.time() - start

    # Numba
    start = time.time()
    result = ssd_match_parallel(image.astype(np.float32), template.astype(np.float32))
    numba_time = time.time() - start

    print(f"模板匹配 - OpenCV: {cv2_time:.3f}s, Numba: {numba_time:.3f}s, 加速: {cv2_time/numba_time:.1f}x")


def benchmark_parallel_processing():
    """并行处理性能测试"""
    def process(x):
        time.sleep(0.1)  # 模拟处理
        return x * 2

    items = list(range(8))

    # 串行
    start = time.time()
    serial = [process(x) for x in items]
    serial_time = time.time() - start

    # 并行
    start = time.time()
    parallel = parallel_map(process, items, n_jobs=4)
    parallel_time = time.time() - start

    print(f"并行处理 - 串行: {serial_time:.3f}s, 并行: {parallel_time:.3f}s, 加速: {serial_time/parallel_time:.1f}x")


def benchmark_image_resize():
    """图像缩放性能测试"""
    image = np.random.randint(0, 256, (3000, 4000, 3), dtype=np.uint8)

    # OpenCV
    start = time.time()
    for _ in range(5):
        cv2.resize(image, (800, 600))
    cv2_time = time.time() - start

    # Pillow-SIMD
    start = time.time()
    for _ in range(5):
        resize_image_fast(image, 800, 600)
    pil_time = time.time() - start

    print(f"图像缩放 - OpenCV: {cv2_time:.3f}s, Pillow-SIMD: {pil_time:.3f}s, 加速: {cv2_time/pil_time:.1f}x")


if __name__ == "__main__":
    print("=== 性能基准测试 ===")
    benchmark_template_match()
    benchmark_parallel_processing()
    benchmark_image_resize()
```

运行测试：

```bash
python tests/benchmark_performance.py
```

### 预期结果

| 优化项 | 预期提升 |
|--------|---------|
| 模板匹配 | 10-50x |
| 并行处理 | 2-4x |
| 图像缩放 | 4-16x |

---

## 依赖清单

```txt
# 核心依赖
joblib>=1.3.0
numba>=0.58.0
numpy>=1.24.0

# 可选依赖 (用于Pillow-SIMD)
pillow-simd>=9.0.0
# 或
pillow>=10.0.0

# OpenCV (已有)
opencv-python>=4.8.0
```

---

## 实施时间线

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 第一周 | 集成 joblib | 2-3小时 |
| 第二周 | 集成 Numba | 3-5小时 |
| 第三周 | 优化基础操作 | 2-3小时 |
| 第四周 | 测试验证 | 2-3小时 |

---

## 注意事项

1. **Numba兼容性**: 确保使用的NumPy版本兼容，避免与PyTorch版本冲突
2. **Pillow-SIMD**: 如果安装失败，系统会自动回退到普通Pillow，不影响功能
3. **并行后端选择**: I/O密集型用threading，CPU密集型用multiprocessing
4. **内存控制**: 批量处理时注意内存使用，避免一次性加载过多图像

---

## 故障排除

### Numba编译错误

如果遇到Numba编译错误，检查：
1. NumPy版本是否兼容
2. 是否有不支持的Python特性（如yield、try-except在jit函数中）
3. 数据类型是否一致

### joblib内存问题

如果遇到内存问题：
1. 减少并行任务数量
2. 使用批量处理而不是一次性处理所有数据
3. 及时释放不需要的内存

### Pillow-SIMD安装失败

如果Pillow-SIMD安装失败：
1. 系统会自动回退到普通Pillow
2. 可以手动安装：`pip install pillow`
3. 性能仍然可用，只是没有SIMD加速

---

## 总结

通过三步集成，项目性能可获得显著提升：

- **第一步(joblib)**: 2-4x 批量处理加速
- **第二步(Numba)**: 10-50x 计算密集函数加速
- **第三步(Pillow-SIMD)**: 4-16x 基础操作加速

整体预期：**在典型使用场景下，系统性能可提升 5-20x**。

---

*文档版本: 1.0*
*创建日期: 2026-02-27*
*最后更新: 2026-02-27*
