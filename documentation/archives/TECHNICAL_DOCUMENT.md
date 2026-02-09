# VisionMaster Python重构技术文档

## 1. 项目概述

### 1.1 项目目标
基于海康VisionMaster V4.4.0算法开发平台的架构，使用Python语言实现一个完整的视觉检测系统，支持图像采集、算法处理、流程控制等功能。

### 1.2 参考架构
- **原始系统**: 海康VisionMaster V4.4.0 (C++)
- **目标系统**: Python + PyQt5 + OpenCV
- **开发环境**: Python 3.7+, PyQt5, OpenCV, NumPy

### 1.3 最新更新 (2026-01-30)
- ✅ 完成代码复用与模块化优化
- ✅ 创建图像处理工具函数库 (utils/image_processing_utils.py)
- ✅ 优化相机模块目录结构 (modules/camera/)
- ✅ 重构工具模块为子包结构 (vision/communication/analysis)
- ✅ 修复相机软触发失败问题，增加重试机制
- ✅ 更新所有相关文档，反映代码结构变化

## 2. 系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    MainWindow (主窗口)                      │  │
│  │  - 菜单栏 (文件/编辑/运行/视图/帮助)                        │  │
│  │  - 工具栏 (运行控制/图像控制)                               │  │
│  │  - 停靠窗口 (项目浏览器/工具库/属性面板/结果面板)            │  │
│  │  - 中央区域 (图像视图/算法编辑器)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      核心层 (Core Layer)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Solution (方案)                       │  │
│  │  - 管理多个流程 (Procedure)                                │  │
│  │  - 执行控制 (单次运行/连续运行/停止)                       │  │
│  │  - 方案保存/加载                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Procedure (流程)                       │  │
│  │  - 管理多个工具 (Tool)                                     │  │
│  │  - 数据流转 (输入/输出)                                    │  │
│  │  - 流程控制 (条件分支/循环)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     工具层 (Tool Layer)                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐  │
│  │ 图像源模块  │ 图像处理模块│ 视觉算法模块│   通信模块       │  │
│  ├─────────────┼─────────────┼─────────────┼─────────────────┤  │
│  │ ImageSource │ BoxFilter   │ GrayMatch   │ ReadDatas       │  │
│  │ Camera      │ Morphology  │ BlobFind    │ SendDatas       │  │
│  │             │ Resize      │ Bcr         │ DynamicIO       │  │
│  │             │             │ Caliper     │                 │  │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     数据层 (Data Layer)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     ImageData (图像数据)                   │  │
│  │  - 图像数组 (numpy.ndarray)                                │  │
│  │  - 元数据 (宽度/高度/通道/时间戳)                          │  │
│  │  - ROI信息                                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    ResultData (结果数据)                   │  │
│  │  - 数值结果 (int/float)                                    │  │
│  │  - 几何形状 (点/线/圆/矩形)                                │  │
│  │  - 字符串结果                                              │  │
│  │  - 图像结果                                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 UI布局设计

#### 2.2.1 主窗口布局
```
┌─────────────────────────────────────────────────────────────────┐
│  菜单栏                                                          │
├─────────────────────────────────────────────────────────────────┤
│  工具栏                                                          │
├──────────┬──────────────────────────────┬───────────────────────┤
│          │                              │                       │
│  项目    │      中央区域                │      右侧区域         │
│  浏览器  │   (图像视图/算法编辑器)       │   ┌───────────────┐   │
│          │                              │   │   图像区域    │   │
│          │                              │   │   (50%)       │   │
│          │                              │   ├───────────────┤   │
│          │                              │   │   属性面板    │   │
│          │                              │   │   (40%)       │   │
│          │                              │   ├───────────────┤   │
│          │                              │   │   结果面板    │   │
│          │                              │   │   (10%)       │   │
│          │                              │   └───────────────┘   │
└──────────┴──────────────────────────────┴───────────────────────┘
```

#### 2.2.2 结果面板布局
```
┌─────────────────────────────┐
│ 📊 结果面板  [清空] [导出]  │
├─────────────────────────────┤
│ [全部 ▼] [搜索...]          │
├─────────────────────────────┤
│ 🕐 ✅ 📋 工具名称 1         │
│   ├── 结果详情 1            │
│   └── 结果详情 2            │
│ 🕐 ❌ 🔍 工具名称 2         │
│   └── 结果详情              │
├─────────────────────────────┤
│ 5 条结果                    │
└─────────────────────────────┘
```

### 2.3 核心类设计

#### 2.3.1 图像数据封装 (ImageData)

```python
class ImageData:
    """图像数据结构，封装图像及其元数据"""
    def __init__(self, 
                 data: np.ndarray,           # 图像数据
                 width: int = None,          # 图像宽度
                 height: int = None,         # 图像高度
                 channels: int = None,       # 通道数
                 timestamp: float = None,    # 时间戳
                 roi: ROI = None,            # ROI信息
                 camera_id: str = None):     # 相机ID
        self.data = data
        self.width = width or data.shape[1]
        self.height = height or data.shape[0]
        self.channels = channels or data.shape[2] if len(data.shape) > 2 else 1
        self.timestamp = timestamp or time.time()
        self.roi = roi
        self.camera_id = camera_id
    
    @property
    def shape(self):
        """返回图像形状 (height, width, channels)"""
        return self.data.shape
    
    def to_gray(self) -> 'ImageData':
        """转换为灰度图像"""
        if self.channels == 3:
            gray_data = cv2.cvtColor(self.data, cv2.COLOR_BGR2GRAY)
            return ImageData(gray_data, self.width, self.height, 1, self.timestamp, self.roi, self.camera_id)
        return self.copy()
    
    def copy(self) -> 'ImageData':
        """创建深拷贝"""
        return ImageData(
            self.data.copy(),
            self.width,
            self.height,
            self.channels,
            self.timestamp,
            self.roi.copy() if self.roi else None,
            self.camera_id
        )
```

#### 2.3.2 工具基类 (ToolBase)

```python
class ToolBase:
    """工具基类，所有算法工具的父类"""
    
    # 子类必须重写
    tool_name = "BaseTool"
    tool_category = "Base"
    
    def __init__(self, name: str = None):
        self.name = name or f"{self.tool_category}_{id(self)}"
        self.params = {}
        self.results = {}
        self.input_data: Optional[ImageData] = None
        self.output_data: Optional[ImageData] = None
        self.is_enabled = True
    
    def set_param(self, key: str, value: Any):
        """设置参数"""
        self.params[key] = value
    
    def get_param(self, key: str) -> Any:
        """获取参数"""
        return self.params.get(key)
    
    def set_input(self, image_data: ImageData):
        """设置输入数据"""
        self.input_data = image_data
    
    def get_output(self) -> ImageData:
        """获取输出数据"""
        return self.output_data
    
    def run(self):
        """执行工具处理，必须由子类重写"""
        raise NotImplementedError("子类必须重写run方法")
    
    def reset(self):
        """重置工具状态"""
        self.output_data = None
        self.results = {}
```

#### 2.3.3 ROI工具混入类 (ROIToolMixin)

```python
class ROIToolMixin:
    """
    ROI工具混入类
    
    为需要ROI功能的工具类提供通用的ROI支持。
    使用方法:
        class MyTool(ROIToolMixin, VisionAlgorithmToolBase):
            tool_name = "MyTool"
            
            def _run_impl(self):
                roi = self.get_roi_from_params(image.shape[1], image.shape[0])
                if roi:
                    roi_x, roi_y, roi_width, roi_height = roi
                    # 使用ROI区域
                    pass
    """
    
    def _init_roi_params(self):
        """初始化ROI相关参数"""
        self._roi_x = 0
        self._roi_y = 0
        self._roi_width = 100
        self._roi_height = 100
        self._is_roi_set = False
    
    def set_roi(self, x: int, y: int, width: int, height: int):
        """设置ROI区域"""
        self._roi_x = x
        self._roi_y = y
        self._roi_width = width
        self._roi_height = height
        self._is_roi_set = True
    
    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """获取当前ROI区域"""
        if self._is_roi_set:
            return (self._roi_x, self._roi_y, self._roi_width, self._roi_height)
        return None
    
    def get_roi_from_params(self, image_width: int = None, image_height: int = None):
        """从参数中获取ROI区域"""
        roi_data = self.get_param("roi", None)
        
        # 优先从参数中的roi字典获取
        if roi_data and isinstance(roi_data, dict) and "x" in roi_data:
            roi_x = int(roi_data.get("x", 0))
            roi_y = int(roi_data.get("y", 0))
            roi_width = int(roi_data.get("width", 100))
            roi_height = int(roi_data.get("height", 100))
            
            # 边界检查
            if image_width is not None:
                roi_x = max(0, min(roi_x, image_width - 1))
                roi_y = max(0, min(roi_y, image_height - 1))
                roi_width = max(1, min(roi_width, image_width - roi_x))
                roi_height = max(1, min(roi_height, image_height - roi_y))
            
            return (roi_x, roi_y, roi_width, roi_height)
        
        # 从内部变量获取（向后兼容）
        if self._is_roi_set:
            return (self._roi_x, self._roi_y, self._roi_width, self._roi_height)
        
        return None
```

**使用ROIToolMixin的工具类**：
- GrayMatch (灰度匹配)
- ShapeMatch (形状匹配)
- LineFind (直线查找)
- CircleFind (圆查找)

**代码优化效果**：
- 减少约100行重复代码
- ROI功能集中管理，易于维护
- 保持向后兼容性

#### 2.3.4 可缩放图像组件 (ZoomableImage)

```python
from core.zoomable_image import ZoomableGraphicsView, ZoomableFrameMixin

# 方式1: 直接使用ZoomableGraphicsView
class MyImageView(ZoomableGraphicsView):
    def __init__(self, parent=None):
        super().__init__(QGraphicsScene(), parent)

# 方式2: 继承ZoomableFrameMixin（适用于QFrame子类）
class MyCanvas(ZoomableFrameMixin, QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_zoomable()
```

**通用功能**：
- ✅ 鼠标滚轮缩放
- ✅ 拖拽平移
- ✅ 缩放范围限制
- ✅ 缩放变化信号

**使用位置**：
- `ui/main_window.py`: ImageView类继承ZoomableGraphicsView
- `ui/roi_selection_dialog.py`: ROIEditorCanvas混入ZoomableFrameMixin

**文件位置**: `core/zoomable_image.py`

#### 2.3.5 ROI编辑器 (ROISelectionDialog)

```python
from ui.roi_selection_dialog import ROISelectionDialog, show_roi_editor

# 方法1: 使用对话框类
dialog = ROISelectionDialog(self, "选择ROI区域", roi_type="rect")
dialog.set_image(image)
dialog.set_roi_data(existing_roi)
if dialog.exec() == QDialog.Accepted:
    roi_data = dialog.get_roi_data()

# 方法2: 使用便捷函数
roi_data = show_roi_editor(parent, image, "选择ROI区域", "rect")
```

**ROI编辑器功能**：
- ✅ 绘制ROI（矩形、直线、圆）
- ✅ 拖拽ROI整体移动位置
- ✅ 拖拽ROI边界/角点调整大小
- ✅ 键盘微调（方向键）
- ✅ Ctrl+Z撤销编辑
- ✅ 滚轮缩放图像（10%~1000%）
- ✅ 实时显示ROI位置和尺寸信息

**文件位置**: `ui/roi_selection_dialog.py`

**代码结构**：
- `ROIEditorCanvas`: 画布组件，处理绘制和编辑逻辑
- `ROISelectionDialog`: 对话框UI
- `show_roi_editor()`: 便捷函数

#### 2.3.6 连续运行控制

```python
class MainWindow:
    def run_continuous(self):
        """连续运行 - 使用QTimer实现"""
        if not self.solution.procedures:
            self.update_status("没有可执行的流程")
            return
        
        if not self.current_procedure:
            self.update_status("请先选择一个流程")
            return
        
        if hasattr(self, '_continuous_running') and self._continuous_running:
            self.update_status("已经在连续运行中")
            return
        
        self._continuous_running = True
        self.update_status("连续运行中...")
        
        # 使用QTimer实现连续运行，避免线程安全问题
        self._continuous_timer = QTimer(self)
        self._continuous_timer.timeout.connect(self._on_continuous_timer)
        self._continuous_timer.start(1000)  # 1秒间隔
        
        # 立即执行第一次
        self._on_continuous_timer()
    
    def _on_continuous_timer(self):
        """连续运行定时器回调"""
        if not self._continuous_running:
            return
        
        try:
            # 执行单次运行
            self.run_once()
        except Exception as e:
            self._logger.error(f"连续运行出错: {e}")
    
    def stop_run(self):
        """停止运行"""
        if not hasattr(self, '_continuous_running') or not self._continuous_running:
            self.update_status("未在连续运行")
            return
        
        self._continuous_running = False
        
        # 停止定时器
        if hasattr(self, '_continuous_timer'):
            self._continuous_timer.stop()
            delattr(self, '_continuous_timer')
        
        self.update_status("连续运行已停止")
```

**优势**：
- ✅ 使用QTimer代替多线程，避免Qt线程安全问题
- ✅ 所有操作在主线程执行，UI更新流畅
- ✅ 简单易用，易于控制

#### 2.3.7 流程类 (Procedure)

```python
class Procedure:
    """流程类，管理一组工具的执行"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = []  # 工具列表
        self.connections = []  # 工具连接关系
        self.is_enabled = True
    
    def add_tool(self, tool: ToolBase, position: tuple = None):
        """添加工具到流程"""
        self.tools.append(tool)
        if position:
            tool.position = position
    
    def remove_tool(self, tool: ToolBase):
        """从流程移除工具"""
        if tool in self.tools:
            self.tools.remove(tool)
    
    def connect(self, from_tool: ToolBase, to_tool: ToolBase, 
                from_port: str = "output", to_port: str = "input"):
        """连接两个工具"""
        self.connections.append({
            "from_tool": from_tool,
            "to_tool": to_tool,
            "from_port": from_port,
            "to_port": to_port
        })
    
    def run(self, input_data: ImageData = None) -> dict:
        """执行流程"""
        # 按依赖顺序执行工具
        execution_order = self._get_execution_order()
        
        results = {}
        for tool in execution_order:
            if tool.is_enabled:
                # 获取输入
                if tool == self.tools[0] and input_data is not None:
                    tool.set_input(input_data)
                else:
                    # 从前一个工具获取输出
                    pass
                
                # 执行工具
                tool.run()
                
                # 保存结果
                results[tool.name] = tool.get_output()
        
        return results
    
    def _get_execution_order(self) -> list:
        """获取执行顺序（拓扑排序）"""
        return self.tools.copy()
```

#### 2.3.8 方案类 (Solution)

```python
class Solution:
    """方案类，管理多个流程"""
    
    def __init__(self, name: str = "Solution"):
        self.name = name
        self.procedures = []
        self.solution_path = None
        self.solution_password = None
        self.is_running = False
        self.run_interval = 100  # ms
    
    def add_procedure(self, procedure: Procedure):
        """添加流程"""
        self.procedures.append(procedure)
    
    def remove_procedure(self, procedure: Procedure):
        """移除流程"""
        if procedure in self.procedures:
            self.procedures.remove(procedure)
    
    def run(self):
        """执行方案"""
        self.is_running = True
        for procedure in self.procedures:
            if procedure.is_enabled:
                procedure.run()
        self.is_running = False
    
    def stop_run(self):
        """停止运行"""
        self.is_running = False
    
    def save(self, path: str = None, password: str = None):
        """保存方案"""
        path = path or self.solution_path
        password = password or self.solution_password
        # 实现保存逻辑
        pass
    
    def load(self, path: str, password: str = None):
        """加载方案"""
        self.solution_path = path
        self.solution_password = password
        # 实现加载逻辑
        pass
```

## 3. 模块详细设计

### 3.1 图像源模块

```python
class ImageSource(ToolBase):
    """图像源工具，支持本地图像和相机"""
    tool_name = "图像读取器"
    tool_category = "ImageSource"
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self.source_type = "local"  # local/camera/sdk
        self.image_path = None
        self.camera_id = None
        self.pixel_format = "BGR"
    
    def run(self):
        if self.source_type == "local":
            self._load_local_image()
        elif self.source_type == "camera":
            self._capture_camera()
    
    def _load_local_image(self):
        """加载本地图像"""
        image = cv2.imread(self.image_path)
        if image is not None:
            self.output_data = ImageData(image)
```

### 3.2 相机管理模块

```python
class CameraManager:
    """相机管理器，支持海康MVS SDK"""
    
    _instance = None  # 单例模式
    _lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraManager, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化"""
        self._logger = logging.getLogger("CameraManager")
        self._cameras = {}
        self._camera_list = []
        self._lock = threading.RLock()
    
    def discover_devices(self) -> list:
        """发现可用相机"""
        pass
    
    def connect(self, camera_id: str) -> 'Camera':
        """连接相机"""
        pass
    
    def disconnect(self, camera_id: str):
        """断开相机"""
        pass
    
    def get_camera(self, camera_id: str) -> Optional['HikCamera']:
        """获取已连接的相机"""
        return self._cameras.get(camera_id)
```

**内存泄漏修复**：
```python
def get_one_frame(self, timeout_ms: int = 1000) -> Optional[np.ndarray]:
    """获取一帧图像"""
    # ... 省略其他代码 ...
    
    # 创建numpy数组的副本，避免原始缓冲区被释放后访问无效内存
    temp = np.ctypeslib.as_array(pData, shape=(frame_len,)).copy()
    image = temp.reshape((height, width))
    
    self._camera.MV_CC_FreeImageBuffer(stOutFrame)
    
    return image
```

### 3.3 算法工具模块

根据VisionMaster的SDK，以下是主要的算法工具分类：

#### 3.3.1 图像处理工具
- BoxFilter (方框滤波)
- MeanFilter (均值滤波)
- GaussFilter (高斯滤波)
- MedianFilter (中值滤波)
- Morphology (形态学)
- Resize (尺寸调整)

#### 3.3.2 视觉定位工具
- GrayMatch (灰度匹配)
- ShapeMatch (形状匹配)
- LineFind (直线查找)
- CircleFind (圆查找)
- CornerFind (角点查找)

#### 3.3.3 图像分析工具
- BlobFind (斑点分析)
- PixelCount (像素计数)
- Histogram (直方图)

**内存泄漏修复**：
```python
def _run_impl(self):
    """执行斑点分析"""
    # ... 省略其他代码 ...
    
    # 分析每个轮廓 - 设置最大数量限制以避免内存问题
    max_blobs = 1000  # 最多保留1000个斑点
    blobs = []
    blob_count = 0
    
    for i, contour in enumerate(contours):
        # ... 省略其他代码 ...
        
        # 保存斑点信息 - 只存储必要的信息，不存储完整轮廓以避免内存泄漏
        blob = {
            "id": i,
            "area": float(area),
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "aspect_ratio": float(aspect_ratio),
            "circularity": float(circularity) if circularity else 0.0,
            "cx": int(cx),
            "cy": int(cy)
            # 不保存 "contour": contour，避免内存泄漏
        }
        blobs.append(blob)
        blob_count += 1
        
        # 达到最大数量后停止保存
        if blob_count >= max_blobs:
            self._logger.warning(f"斑点数量已达到最大限制 {max_blobs}，停止保存")
            break
```

#### 3.3.4 测量工具
- Caliper (卡尺测量)
- FitLine (直线拟合)
- FitCircle (圆拟合)

#### 3.3.5 识别工具
- BarcodeRec (条码识别)
- QRCodeRec (二维码识别)
- OCR (字符识别)

## 4. 数据流转设计

### 4.1 图像数据流

```
┌─────────────┐    ImageData     ┌─────────────┐    ImageData     ┌─────────────┐
│ ImageSource │ ───────────────▶ │   Filter    │ ───────────────▶ │  Algorithm  │
│  (图像源)    │                  │   (滤波)     │                  │   (算法)     │
└─────────────┘                  └─────────────┘                  └─────────────┘
```

### 4.2 工具连接

每个工具具有输入端口和输出端口，支持以下连接：
- **图像连接**: 图像数据从前一个工具的输出端口传输到下一个工具的输入端口
- **数据连接**: 检测结果（如位置、角度）可以作为参数传递给下一个工具
- **触发连接**: 一个工具的完成可以触发下一个工具的执行

## 5. API接口设计

### 5.1 工具创建

```python
# 创建工具
tool = ImageSource("MyCamera")
tool.set_param("source_type", "camera")
tool.set_param("camera_id", "0")

# 执行工具
tool.run()
result = tool.get_output()
```

### 5.2 流程创建

```python
# 创建流程
procedure = Procedure("检测流程")

# 添加工具
camera = ImageSource("Camera1")
filter = BoxFilter("Filter1")
matcher = GrayMatch("Matcher1")

procedure.add_tool(camera)
procedure.add_tool(filter)
procedure.add_tool(matcher)

# 连接工具
procedure.connect(camera, filter)
procedure.connect(filter, matcher)

# 执行流程
results = procedure.run()
```

### 5.3 方案管理

```python
# 创建方案
solution = Solution("我的方案")

# 添加流程
solution.add_procedure(procedure)

# 保存方案
solution.save("my_solution.vmsol")

# 运行方案
solution.run()  # 单次运行
solution.runing()  # 连续运行
solution.stop_run()  # 停止运行
```

## 6. 异常处理设计

```python
class VisionMasterException(Exception):
    """视觉检测异常基类"""
    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class CameraException(VisionMasterException):
    """相机异常"""

class ToolException(VisionMasterException):
    """工具异常"""

class ParameterException(VisionMasterException):
    """参数异常"""
```

## 7. 性能优化设计

### 7.1 多线程处理
- 图像采集在独立线程
- 工具执行可以并行化
- 结果回调异步处理

### 7.2 内存管理
- 图像数据复用
- 结果数据及时释放
- 大图像分块处理
- **修复内存泄漏**：
  - 斑点分析：限制blob数量，不存储完整轮廓数据
  - 相机模块：共享相机管理器，图像缓冲区复制
  - 结果面板：优化数据结构，避免数据累积

### 7.3 GPU加速
- OpenCV CUDA支持
- 深度学习模型GPU推理

## 8. 文件结构

```
vision_system/
├── main.py                 # 程序入口
├── professional_app.py     # 应用程序入口
├── run.py                  # 运行脚本
├── ui/
│   ├── main_window.py      # 主窗口
│   ├── tool_library.py     # 工具库
│   ├── algorithm_editor.py # 算法编辑器
│   ├── enhanced_result_panel.py  # 增强结果面板（树形结构）
│   ├── property_panel.py   # 属性面板
│   └── ...
├── core/
│   ├── solution.py         # 方案管理
│   ├── procedure.py        # 流程管理
│   ├── zoomable_image.py   # 可缩放图像组件
│   └── ...
├── tools/
│   ├── __init__.py
│   ├── image_source.py     # 图像源
│   ├── camera_parameter_setting.py # 相机参数设置
│   ├── vision/             # 视觉工具子包
│   │   ├── __init__.py
│   │   ├── template_match.py   # 模板匹配
│   │   ├── appearance_detection.py # 外观检测
│   │   ├── cpu_optimization.py # CPU优化
│   │   ├── image_filter.py     # 图像滤波
│   │   ├── image_stitching.py  # 图像拼接
│   │   ├── ocr.py              # OCR
│   │   └── recognition.py      # 识别
│   ├── communication/      # 通信工具子包
│   │   ├── __init__.py
│   │   └── communication.py    # 通信工具
│   └── analysis/           # 分析工具子包
│       ├── __init__.py
│       └── analysis.py         # 分析工具
├── modules/
│   ├── cpu_optimization/   # CPU优化模块
│   │   ├── core/
│   │   ├── models/
│   │   ├── api/
│   │   └── utils/
│   ├── camera/             # 相机模块
│   │   ├── __init__.py
│   │   ├── camera_manager.py   # 相机管理
│   │   ├── camera_adapter.py   # 相机适配器
│   │   └── basler_camera.py     # Basler相机
├── data/
│   ├── image_data.py       # 图像数据类
│   ├── result_data.py      # 结果数据类
│   └── roi.py              # ROI类
├── utils/
│   ├── error_management.py      # 错误管理
│   ├── error_recovery.py        # 错误恢复
│   ├── exceptions.py            # 异常定义
│   ├── hot_reload.py            # 热重载
│   ├── image_processing_utils.py # 图像处理工具函数库
│   ├── image_filter_utils.py    # 图像滤波工具
│   └── performance_optimization.py # 性能优化
└── config/
    └── config.yaml         # 配置文件
```

## 9. 后续开发计划

### 第一阶段: 核心框架 ✅
- [x] 实现ImageData数据结构
- [x] 实现ToolBase工具基类
- [x] 实现Procedure流程管理
- [x] 实现Solution方案管理

### 第二阶段: 图像源模块 ✅
- [x] 实现本地图像读取
- [x] 实现相机集成
- [x] 实现图像数据流

### 第三阶段: 基础算法 ✅
- [x] 图像滤波工具
- [x] 形态学工具
- [x] 几何变换工具

### 第四阶段: 视觉算法 ✅
- [x] 模板匹配
- [x] 边缘检测
- [x] 斑点分析

### 第五阶段: 通讯模块 ✅
- [x] 通讯模块架构设计
- [x] 通用协议接口定义
- [x] TCP/IP客户端/服务端
- [x] 串口通讯
- [x] WebSocket通讯
- [x] HTTP REST API客户端
- [x] 协议管理器

### 第六阶段: 性能优化 ✅
- [x] 修复斑点分析内存泄漏
- [x] 修复相机模块内存泄漏
- [x] 优化结果面板布局
- [x] 实现连续运行功能
- [x] 修复UI布局重复问题

### 第七阶段: 待完善功能
- [ ] 方案保存/加载功能完善
- [ ] 性能监控面板功能完善
- [ ] 实际相机设备完整测试

## 10. 更新日志

### 2026-01-29
- ✅ 优化结果面板布局（图像:属性:结果 = 5:4:1）
- ✅ 简化结果面板UI，使用树形结构显示
- ✅ 修复连续运行线程安全问题（使用QTimer）
- ✅ 修复斑点分析内存泄漏
- ✅ 修复相机模块内存泄漏
- ✅ 修复UI布局重复问题

### 2026-01-28
- ✅ 完成核心功能开发
- ✅ 集成测试通过
- ✅ 文档编写完成
