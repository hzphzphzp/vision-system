# AGENTS.md - Vision System Development Guide

This document provides essential information for AI coding agents working on the Vision System codebase.

## Project Overview

Vision System is a Python-based computer vision application with PyQt5 GUI, inspired by HikVision VisionMaster V4.4.0. It provides a visual programming interface for image processing and analysis tools.

**Tech Stack**: Python 3.7+, PyQt5, OpenCV, NumPy, PyTorch (CPU), pytest

## Build/Lint/Test Commands

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_core.py -v
pytest tests/test_integration.py -v

# Run a specific test function
pytest tests/test_tool_registry.py::test_tool_categories -v

# Run tests with coverage
pytest tests/ --cov=core --cov=data --cov=tools --cov-report=html

# Alternative: Run tests as Python module
python -m pytest tests/test_integration.py -v
```

### Code Quality
```bash
# Format code with Black
black .

# Check code style with Flake8
flake8

# Sort imports with isort
isort .

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the Application
```bash
# Start the main GUI
python ui/main_window.py

# Or use the run script
python run.py --gui
```

## Code Style Guidelines

### Imports
- **Order**: Standard library → Third-party → Local modules
- **Path setup**: Always add `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` at the top
- **Example**:
```python
import os
import sys
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tool_base import ToolBase, ToolParameter
from data.image_data import ImageData
```

### Formatting
- **Line length**: 79 characters (Black, Flake8, isort configured)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Use in multi-line structures
- Use Black for automatic formatting

### Naming Conventions
- **Classes**: PascalCase (e.g., `ImageData`, `ToolBase`)
- **Functions/Methods**: snake_case (e.g., `process_image`, `get_param`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `PARAM_CHINESE_NAMES`)
- **Private members**: Prefix with underscore (e.g., `_file_path`, `_run_impl`)
- **Chinese UI labels**: Use Chinese parameter names (e.g., `"设备名称"`, `"匹配分数"`)

### Type Hints
- Use type hints for function signatures
- Use `from typing import ...` for complex types
- Use `Any` sparingly, prefer specific types

### Error Handling
- Use custom exceptions from `utils.exceptions`
- Base exception: `VisionMasterException`
- Common exceptions: `CameraException`, `ToolException`, `ParameterException`
- Log errors using `utils.error_management.log_error()`
- Example:
```python
from utils.exceptions import ParameterException
from utils.error_management import log_error

if threshold < 0 or threshold > 1:
    raise ParameterException("阈值必须在0-1之间")
```

### Documentation
- **Module docstring**: Purpose, author, date at the top
- **Function docstrings**: Args, Returns, Raises
- **Encoding**: UTF-8 with `# -*- coding: utf-8 -*-`
- **Shebang**: `#!/usr/bin/env python3` for executable files

## Project Structure

```
vision_system/
├── core/              # Core logic (ToolBase, Solution, Procedure)
├── data/              # Data structures (ImageData, ResultData)
├── tools/             # Algorithm tools (image_source, vision/, communication/)
├── ui/                # PyQt5 UI components
├── modules/           # Feature modules (camera/, cpu_optimization/)
├── utils/             # Utilities (error_management, exceptions)
├── tests/             # Test files (all tests go here)
└── config/            # Configuration files
```

## Tool Development Pattern

Tools inherit from `ToolBase` and use the `@ToolRegistry.register` decorator:

```python
@ToolRegistry.register
class MyTool(ToolBase):
    tool_name = "工具名称"  # Chinese name for UI
    tool_category = "Category"
    tool_description = "Description"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._init_params()

    def _init_params(self):
        """Initialize parameters with Chinese labels"""
        self.set_param("threshold", 0.5, description="阈值")

    def _run_impl(self):
        """Main implementation logic"""
        threshold = self.get_param("threshold")
        # Process...
        return {"OutputImage": image_data}
```

## Testing Patterns

- All tests in `tests/` directory
- Use fixtures from `conftest.py`
- Test files named `test_*.py`
- Use pytest fixtures for common setup
- Mock external dependencies (cameras, files)

## Pre-commit Hooks

Configured in `.pre-commit-config.yaml`:
- Black (code formatting)
- Flake8 (linting)
- isort (import sorting)

Run manually: `pre-commit run --all-files`

## Lessons Learned & Common Pitfalls

### 1. Tool Registration Category Mismatch

**Problem**: Tool appears in UI but cannot be created ("未找到工具" error)

**Root Cause**: `tool_category` in class definition doesn't match the category in `ui/tool_library.py`

**Solution**:
```python
# In tools/vision/calibration.py
class CalibrationTool(ToolBase):
    tool_name = "标定"
    tool_category = "Vision"  # Must match ui/tool_library.py category

# In ui/tool_library.py _load_tools()
ToolItemData(
    "Vision",  # Must match tool_category above
    "标定",
    "标定",
    "📐",
    "像素坐标和尺寸转换为物理尺寸"
)
```

**Verification**:
```bash
python -c "import tools; from core.tool_base import ToolRegistry; print(ToolRegistry.get_all_tools().keys())"
```

### 2. NumPy Version Compatibility

**Problem**: "Numpy is not available" or "numpy.dtype size changed" errors

**Root Cause**: 
- PyTorch 2.1.2 requires NumPy 1.x
- scikit-image 0.20.0 compiled against NumPy 1.x
- OpenCV may have binary incompatibilities

**Solution**:
```bash
# Upgrade PyTorch to support NumPy 2.x
pip install torch==2.10.0 ultralytics==8.4.10

# Or force reinstall scikit-image for NumPy 2.x
pip install --force-reinstall scikit-image
```

**Prevention**: Always check version compatibility in requirements.txt

### 3. Qt Threading Issues

**Problem**: "QObject::~QObject: Timers cannot be stopped from another thread"

**Root Cause**: Using QTimer/QEventLoop from non-Qt threads (daemon threads)

**Solution**: Use `time.sleep()` instead of QTimer in daemon threads:
```python
# Wrong - causes thread error
from PyQt5.QtCore import QTimer, QEventLoop
timer = QTimer()
timer.singleShot(1000, callback)
loop = QEventLoop()
loop.exec_()

# Correct - safe for daemon threads
import time
time.sleep(1.0)
```

### 4. Circular Import Prevention

**Problem**: ImportError or circular import issues

**Root Cause**: Modules importing each other at module level

**Solution**:
```python
# In modules/__init__.py and modules/camera/__init__.py
# Use lazy imports or avoid importing submodules at package level

# Good: Import only what's needed
from .camera_manager import CameraManager

# Avoid: Importing everything
# from . import *  # This can cause circular imports
```

### 5. Tool Deletion Bug

**Problem**: Deleting tool from UI doesn't remove it from Procedure._tools

**Root Cause**: Passing tool object instead of tool name string to `remove_tool()`

**Solution**:
```python
# In ui/main_window.py line ~2212
# Wrong
self.current_procedure.remove_tool(tool)  # tool is object

# Correct
self.current_procedure.remove_tool(tool.name)  # tool.name is string
```

### 6. Testing Strategy

**Case Tests vs Field Tests**:
- **Case Tests**: Unit tests with mock data (e.g., `test_calibration.py`)
- **Field Tests**: Real-world usage with actual hardware/images

**Important**: Always document test coverage:
```python
# In README.md Known Issues section
"""
**标定模块**: ⚠️ 仅通过案例测试 (test_calibration.py 8/8 passed)，
未进行实际现场测试验证
"""
```

### 7. Import Order Standards

**Required Pattern**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module docstring
Author, Date
"""

# 1. Standard library
import os
import sys
from typing import Any, Dict, List, Optional

# 2. Third-party
import cv2
import numpy as np

# 3. Path setup (before local imports)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 4. Local modules
from core.tool_base import ToolBase
from data.image_data import ImageData
```

### 8. Memory Management

**ImageBufferPool Usage**:
```python
from core.memory_pool import ImageBufferPool

# Get buffer from pool instead of creating new
pool = ImageBufferPool.get_instance()
buffer = pool.acquire(width, height, channels)

# Use buffer...

# Release back to pool (automatic in ImageData destructor)
pool.release(buffer)
```

### 9. Documentation Updates

**When adding new features, update**:
1. `README.md` - Project structure, features list, known issues
2. `documentation/INDEX.md` - Add new documentation links
3. `AGENTS.md` - Add lessons learned if it's a common pattern
4. Tool-specific docs in `tools/vision/CALIBRATION.md` format

### 10. Git Workflow

**Before committing**:
```bash
# 1. Run tests
pytest tests/ -v

# 2. Check code style
flake8
black . --check

# 3. Review changes
git diff

# 4. Commit with meaningful message
git commit -m "type: description

Detailed explanation of changes"
```

**Commit message types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring

### 11. Property Panel Signal Connection Issues

**Problem**: Tool parameters (like "目标连接" and "数据内容") not being saved when user selects values from dropdown/combobox

**Error Messages**:
```
ERROR - 未选择连接
ERROR - 可用参数: ['目标连接', '__type_目标连接', ...]
目标连接: '' (类型: str)
```

**Root Cause**: 
1. `QComboBox` using `currentTextChanged` signal sends display text instead of actual value (userData)
2. `DataContentSelector` signal `data_selected` not connected to property panel's parameter change handler
3. Empty string values triggering unnecessary signal emissions

**Solution**:
```python
# In ui/property_panel.py

# 1. Change signal from currentTextChanged to currentIndexChanged
elif isinstance(widget, QComboBox):
    widget.currentIndexChanged.connect(
        lambda index, w=widget, p=param_name: self._on_combobox_changed(p, w)
    )
    # Add activated signal as backup for manual selection
    widget.activated.connect(
        lambda index, w=widget, p=param_name: self._on_combobox_activated(p, w)
    )

# 2. Create handler to get userData instead of display text
def _on_combobox_changed(self, param_name: str, combobox: QComboBox):
    current_data = combobox.currentData()  # Get actual value
    current_text = combobox.currentText()  # Get display text
    value = current_data if current_data is not None else current_text
    self._on_parameter_changed(param_name, value)

# 3. Connect DataContentSelector signal
else:
    if hasattr(widget, 'data_selected') and hasattr(widget, 'text_edit'):
        widget.data_selected.connect(
            partial(self._on_parameter_changed, param_name)
        )
        widget.text_edit.textChanged.connect(
            partial(self._on_parameter_changed, param_name)
        )

# 4. Avoid setting empty values
if value is not None and str(value).strip():
    # Set current index or text
else:
    # Skip setting empty values
```

**Debugging Tips**:
- Add detailed logging at each step: signal connection → signal emission → parameter change → parameter save
- Use `print()` in static methods (like `ParameterWidgetFactory`) where `self` is not available
- Check signal connection order: widget creation → signal connection → value setting
- Verify parameter persistence: tool creation → parameter initialization → user selection → parameter save → tool execution

**Verification**:
```bash
# Check logs for these patterns:
【属性面板】下拉框激活(activated): 目标连接, index=0, currentText='...', currentData='...'
【属性面板】参数变更: 目标连接 = '...' (类型: str)
【set_param】设置参数: 工具名.目标连接 = '...' (旧值: '')
【调试】最终目标连接: '...'
```

### 12. Communication Tool Data Collection Logic

**Problem**: SendDataTool sending entire upstream data dictionary instead of specific field selected by user

**Received Data**:
```python
{'data': {'OutputImage': ImageData(...), 'Width': 3072, 'Height': 2048, 'Channels': 3}}
```

**Expected Data** (when user selects "Width"):
```python
{'Width': 3072}
```

**Root Cause**: `_collect_input_data()` method sending entire `upstream_values` dict instead of extracting specific field

**Solution**:
```python
# In tools/communication/enhanced_communication.py

if "." in data_content and not data_content.startswith("{"):
    parts = data_content.split(".", 1)
    if len(parts) == 2:
        module_name, field_name = parts
        if upstream_values:
            # Extract specific field value
            if field_name in upstream_values:
                field_value = upstream_values[field_name]
                input_data = {field_name: field_value}
            else:
                # Field not found, send all data with warning
                input_data = {"data": upstream_values}
```

**Key Insight**: User selection format is "ModuleName.FieldName" (e.g., "图像读取器_1.Width"), need to parse and extract specific field from upstream data.

### 13. ReceiveDataTool Input Validation

**Problem**: ReceiveDataTool throws "输入数据无效" (Input data invalid) error when executing

**Error Message**:
```
ErrorManager - ERROR - [ERROR] 工具执行错误: 接收数据_1: [400] 输入数据无效
```

**Root Cause**: 
`ReceiveDataTool` inherits default `_check_input()` from `ToolBase`, which checks if `_input_data` (input image) exists and is valid. But receive data tool doesn't need input image - it receives data from external connection.

**Solution**:
```python
# In ReceiveDataTool class

def _check_input(self) -> bool:
    """Check input data validity
    
    Receive data tool doesn't need input image data,
    it receives data from external connection, so always return True
    """
    return True
```

**Important**: Tools that don't need input image data (like communication tools) must override `_check_input()` to return `True`.

### 14. Connection List Format Consistency

**Problem**: SendDataTool and ReceiveDataTool use different formats for connection list, causing "connection not found" errors

**SendDataTool Format**: `device_id: display_name` (e.g., `conn_123: [conn_123] TCP客户端 - Name`)
**ReceiveDataTool Format (Old)**: `display_name` only (e.g., `[conn_123] TCP客户端 - Name`)

**Root Cause**: Inconsistent `_get_available_connections()` implementation between tools

**Solution**:
```python
# Unified format for both tools
def _get_available_connections(self) -> List[str]:
    """Get available connections (unified format: device_id: display_name)"""
    try:
        conn_manager = _get_comm_manager()
        connections = conn_manager.get_available_connections()
        result = []
        for conn in connections:
            if conn.get("connected"):
                device_id = conn.get("device_id", conn.get("name", ""))
                display_name = conn.get("display_name", "")
                if device_id and display_name:
                    result.append(f"{device_id}: {display_name}")
                elif display_name:
                    result.append(display_name)
        return result
    except Exception as e:
        self._logger.error(f"Failed to get connections: {e}")
        return []
```

**Best Practice**: Always use consistent connection identifier format across all communication tools. Support multiple parsing formats in `_get_connection_by_display_name()`:
- `device_id: display_name`
- `display_name` only
- `[device_id] display_name` (bracket format)

### 15. Enhanced Result Panel Implementation

**Overview**: `ui/enhanced_result_panel.py` provides comprehensive result visualization with support for multiple result types, data export, and visual rendering.

**Core Classes**:

1. **ResultCategory (Enum)**: Defines result types (BARCODE, QRCODE, MATCH, CALIPER, BLOB, OCR, etc.)

2. **EnhancedResultPanel**: Main panel with tree-based result list, category filtering, search, and data export

3. **ResultDetailWidget**: Displays detailed information for different result types

4. **DataSelectorWidget**: Dynamic data type selector for viewing different data types

5. **ResultVisualizationWidget**: Graphical visualization of detection results with bounding boxes

**Key Features**:
- **Smart Result Classification**: Auto-detects result category from tool name
  - Contains "YOLO" → detection
  - Contains "条码"/"二维码"/"读码" → code
  - Contains "匹配" → match
  - Contains "测量"/"卡尺" → caliper
  - Contains "Blob" → blob
  - Contains "OCR" → ocr

- **Result Deduplication**: New results from same module replace old ones, preventing infinite list growth

- **Performance Optimization**: Limits max results to 500 to prevent memory overflow

- **Data Export**: Supports CSV and JSON formats for result analysis

**Usage Example**:
```python
from ui.enhanced_result_panel import EnhancedResultPanel
from data.result_data import ResultData

# Create panel
result_panel = EnhancedResultPanel()

# Add result
result_data = ResultData(
    tool_name="条码识别_1",
    status=True,
    values={"codes": [{"data": "123456", "type": "CODE128"}]}
)
result_panel.add_result(result_data, category="barcode")
```

**Integration in Main Window**:
```python
from ui.enhanced_result_panel import EnhancedResultPanel

self.result_panel = EnhancedResultPanel()
self.result_panel.result_selected.connect(self._on_result_selected)
self.result_panel.data_connection_requested.connect(self._on_data_connection_requested)
```

### 16. Python Class Constructor Parameter Rules

**Problem**: `TypeError: Class.__init__() got an unexpected keyword argument 'xxx'`

**Root Cause**: Attempting to pass attributes as constructor parameters when they should be set after object creation.

**Wrong Example**:
```python
class DataExtractionRule:
    def __init__(self, rule_type, name, description, enabled=True):
        self.rule_type = rule_type
        self.name = name
        self.description = description
        self.enabled = enabled
        # Other attributes are NOT in __init__ parameters
        self.scale_offset_rule = None
        self.bit_extract_rule = None
        # ...

# WRONG: This will cause TypeError
rule = DataExtractionRule(
    rule_type=ExtractionRuleType.SCALE_OFFSET,
    name="温度传感器",
    scale_offset_rule=ScaleOffsetRule(scale=0.1, offset=-40.0)  # ERROR!
)
```

**Correct Example**:
```python
# CORRECT: Create object first, then set attributes
rule = DataExtractionRule(
    rule_type=ExtractionRuleType.SCALE_OFFSET,
    name="温度传感器",
    description="温度转换规则"
)
rule.scale_offset_rule = ScaleOffsetRule(scale=0.1, offset=-40.0)

# For predefined rules, use a factory function
def _create_predefined_rules():
    rules = {}
    
    temp_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.SCALE_OFFSET,
        name="温度传感器",
        description="将原始值转换为温度值"
    )
    temp_rule.scale_offset_rule = ScaleOffsetRule(scale=0.1, offset=-40.0)
    rules["温度传感器"] = temp_rule
    
    return rules
```

**Key Rules**:
1. **Check `__init__` signature** before passing parameters
2. **Only pass parameters defined in `__init__`**
3. **Set other attributes after object creation**
4. **Use factory functions** for complex object initialization
5. **Use lazy initialization** for module-level predefined objects to avoid import-time errors

**Common Mistake Pattern**:
```python
# Module-level predefined objects - DANGEROUS at import time
PREDEFINED_RULES = {
    "温度传感器": DataExtractionRule(
        rule_type=ExtractionRuleType.SCALE_OFFSET,
        scale_offset_rule=ScaleOffsetRule(...)  # May cause errors
    )
}

# BETTER: Lazy initialization
PREDEFINED_RULES: Dict[str, DataExtractionRule] = {}

def get_predefined_rules():
    global PREDEFINED_RULES
    if not PREDEFINED_RULES:
        PREDEFINED_RULES = _create_predefined_rules()
    return PREDEFINED_RULES.copy()
```

### 17. Hot Reload Performance Optimization

**Problem**: Application startup takes 20+ seconds due to hot reload module mapping initialization.

**Root Cause**: `HotReloadManager._initialize_module_mapping()` traverses entire `sys.path` which includes many system directories.

**Wrong Implementation**:
```python
def _initialize_module_mapping(self):
    """初始化模块路径映射"""
    for path in sys.path:  # ❌ 遍历整个sys.path，包含系统目录
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                # ... 处理文件
```

**Optimized Implementation**:
```python
def _initialize_module_mapping(self):
    """初始化模块路径映射（优化版：只监控指定路径）"""
    # ✅ 只遍历需要监控的路径
    for path in self.paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                # ... 处理项目文件
```

**Performance Improvement**:
- Before: 20+ seconds (scanning entire sys.path)
- After: <1 second (scanning only project directories)

**Key Points**:
1. Only scan directories that need monitoring
2. Avoid scanning system directories in sys.path
3. Use lazy loading for module mapping
4. Consider using file system events instead of full scan

### 18. Missing Method Reference Errors

**Problem**: `AttributeError: 'ClassName' object has no attribute '_method_name'`

**Root Cause**: Method was renamed or removed, but references were not updated.

**Example Error**:
```
[热重载] 回调函数执行失败: 'ToolLibraryWidget' object has no attribute '_setup_category_tree'
```

**Solution**:
```python
# Before (Error)
def refresh(self):
    self._load_tools()
    self._update_tool_list()
    self._setup_category_tree()  # ❌ Method doesn't exist

# After (Fixed)
def refresh(self):
    self._load_tools()
    self._update_tool_list()  # ✅ This method already includes category tree update
```

**Prevention**:
1. Use IDE refactoring tools when renaming methods
2. Search for all references before deleting methods
3. Add unit tests to catch missing method errors
4. Use `hasattr()` check for optional methods:
   ```python
   if hasattr(self, '_setup_category_tree'):
       self._setup_category_tree()
   ```

### 19. Qt Signal Blocking in Initialization

**Problem**: Qt widgets trigger signals during initialization, causing unwanted side effects.

**Example**: Dropdown selection triggers config dialog during widget initialization.

**Solution**:
```python
def _update_display(self):
    """更新显示"""
    # ✅ Block signals during programmatic updates
    self.rule_type_combo.blockSignals(True)
    
    # Update widget state
    self._set_combo_by_rule_type(self._rule.rule_type)
    
    # Restore signals
    self.rule_type_combo.blockSignals(False)
```

**Best Practices**:
1. Always use `blockSignals(True)` before programmatic UI updates
2. Restore signals with `blockSignals(False)` after updates
3. Distinguish between user actions and programmatic updates
4. Consider using `QSignalBlocker` context manager:
   ```python
   from PyQt5.QtCore import QSignalBlocker
   
   with QSignalBlocker(self.combo_box):
       self.combo_box.setCurrentIndex(index)
   ```

### 20. Image Stitching Ghosting/Double Image Bug

**Problem**: Image stitching algorithm produces output with ghosting/double image artifacts

**Symptom**: 
- Output image shows overlapping/duplicate content
- Objects appear semi-transparent with offset
- Visual "ghost" effect where same content appears multiple times

**Example**: 
When stitching images of a box, the output shows the box content overlapped with offset, creating a ghosting effect.

**Root Causes**:
1. **Feature Point Mismatch**: Incorrect matching of feature points between images
2. **Homography Matrix Error**: Wrong transformation matrix calculation
3. **Blending Issue**: Improper alpha blending in overlapping regions
4. **Alignment Error**: Images not properly aligned before blending
5. **Parallax Effect**: Significant depth differences causing misalignment

**Potential Solutions**:

```python
# 1. Improve Feature Detection and Matching
def _detect_and_match_features(self, img1, img2):
    """改进的特征检测和匹配"""
    # Use ORB or SIFT for better feature detection
    orb = cv2.ORB_create(nfeatures=5000)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    
    # Use BFMatcher with Hamming distance for ORB
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    # Sort matches by distance
    matches = sorted(matches, key=lambda x: x.distance)
    
    # Filter good matches (keep top 30%)
    good_matches = matches[:int(len(matches) * 0.3)]
    
    return kp1, kp2, good_matches

# 2. RANSAC for Robust Homography Estimation
def _compute_homography_ransac(self, src_pts, dst_pts):
    """使用RANSAC计算单应性矩阵"""
    H, mask = cv2.findHomography(
        src_pts, dst_pts, 
        cv2.RANSAC, 
        ransacReprojThreshold=5.0
    )
    
    # Check if enough inliers
    inliers = np.sum(mask)
    if inliers < 4:
        raise ValueError(f"Not enough inliers: {inliers}")
    
    return H, mask

# 3. Multi-band Blending for Seamless Result
def _multi_band_blending(self, img1, img2, H):
    """多频段融合减少重影"""
    # Create masks for blending
    mask1 = np.ones_like(img1[:, :, 0], dtype=np.float32)
    mask2 = np.ones_like(img2[:, :, 0], dtype=np.float32)
    
    # Warp images and masks
    h, w = img1.shape[:2]
    result_size = (w * 2, h)
    
    warped_img2 = cv2.warpPerspective(img2, H, result_size)
    warped_mask2 = cv2.warpPerspective(mask2, H, result_size)
    
    # Create weight maps based on distance to edges
    weight1 = cv2.distanceTransform((mask1 > 0).astype(np.uint8), cv2.DIST_L2, 5)
    weight2 = cv2.distanceTransform((warped_mask2 > 0).astype(np.uint8), cv2.DIST_L2, 5)
    
    # Normalize weights
    weight_sum = weight1 + weight2 + 1e-6
    weight1 = weight1 / weight_sum
    weight2 = weight2 / weight_sum
    
    # Blend images
    result = np.zeros_like(warped_img2, dtype=np.float32)
    result[:h, :w] = img1.astype(np.float32) * weight1[:, :, np.newaxis]
    result += warped_img2.astype(np.float32) * weight2[:, :, np.newaxis]
    
    return result.astype(np.uint8)

# 4. Exposure Compensation
def _exposure_compensation(self, images):
    """曝光补偿减少亮度差异"""
    # Calculate average brightness for each image
    avg_brightness = [np.mean(img) for img in images]
    
    # Use first image as reference
    reference_brightness = avg_brightness[0]
    
    # Adjust each image
    compensated = []
    for img, brightness in zip(images, avg_brightness):
        ratio = reference_brightness / (brightness + 1e-6)
        adjusted = np.clip(img.astype(np.float32) * ratio, 0, 255).astype(np.uint8)
        compensated.append(adjusted)
    
    return compensated
```

**Debugging Steps**:
1. **Visualize Feature Matches**: Draw lines between matched features to verify correctness
2. **Check Homography Quality**: Verify inlier ratio (should be >50%)
3. **Inspect Overlapping Region**: Examine the area where images overlap
4. **Test with Different Images**: Try with images that have more/less texture
5. **Check Camera Parameters**: Ensure consistent focal length and exposure

**Prevention**:
1. **Input Image Quality**: Ensure sufficient overlap (30-50%) between images
2. **Scene Requirements**: Avoid scenes with moving objects or significant depth variation
3. **Camera Settings**: Use consistent exposure and white balance
4. **Feature Richness**: Ensure images have enough texture for feature detection
5. **Validation**: Add quality checks before and after stitching

**Testing**:
```python
# Test case for ghosting detection
def test_stitching_ghosting():
    stitcher = ImageStitchingTool()
    
    # Load test images
    img1 = cv2.imread("test_image_1.jpg")
    img2 = cv2.imread("test_image_2.jpg")
    
    # Perform stitching
    result = stitcher.stitch([img1, img2])
    
    # Check for ghosting artifacts
    # Compare overlapping regions
    overlap_region = result[:, img1.shape[1]-50:img1.shape[1]+50]
    variance = np.var(overlap_region)
    
    # High variance in overlap region indicates ghosting
    assert variance < threshold, "Ghosting detected in stitched image"
```

### 21. Image Stitching Input Accumulation Bug

**Problem**: Image stitching tool processes 4 images when only 2 are connected.

**Root Cause**: 
- `set_input()` accumulates images in `_input_data_list` across multiple execution cycles
- Each time upstream tools run, they call `set_input()` and data accumulates
- By the time stitching tool runs, list may have 4+ images from previous cycles

**Solution - Detect New Execution Cycle**:
```python
def set_input(self, input_data, port_name="InputImage"):
    super().set_input(input_data, port_name)
    
    # Initialize list
    if not hasattr(self, "_input_data_list"):
        self._input_data_list = []
        self._last_input_time = 0
    
    # Fix: Detect new execution cycle (>1 second gap)
    import time
    current_time = time.time()
    if (current_time - self._last_input_time) > 1.0:
        # New cycle, clear old data
        if len(self._input_data_list) > 0:
            self._logger.debug(f"New cycle detected, clearing {len(self._input_data_list)} images")
            self._input_data_list.clear()
    self._last_input_time = current_time
    
    # Add new input
    if input_data:
        self._input_data_list.append(input_data)
```

**Lessons**:
1. Don't rely on end-of-method cleanup for data that accumulates during input phase
2. Detect execution cycle boundaries using timestamps
3. Always clear accumulated data when starting a new cycle
4. Log list length to detect accumulation issues early

---

### 22. Image Stitching Algorithm Selection

**Problem**: Custom stitching algorithm produces visible seams, ghosting, or black lines.

**Root Cause**: 
- Custom feature matching and blending algorithms are prone to edge artifacts
- Homography-based stitching can create visible seams even with good feature matching
- Simple alpha blending causes ghosting in overlapping regions

**Solution - Use OpenCV Stitcher as Primary Method**:

```python
# In ImageStitchingTool class, add this method:
def _stitch_with_opencv(self, images: List[ImageData]) -> ImageData:
    """Use OpenCV Stitcher for best quality (no seams, no ghosting)"""
    cv_images = [img.data for img in images]
    stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
    status, stitched = stitcher.stitch(cv_images)
    
    if status == cv2.Stitcher_OK:
        return ImageData(data=stitched)
    else:
        raise Exception(f"OpenCV Stitcher failed with status: {status}")

# In process() method, use strategy pattern:
def process(self, input_data: List[ImageData]) -> ResultData:
    # Strategy 1: Try OpenCV Stitcher first (best quality)
    try:
        stitched_image = self._stitch_with_opencv(input_data)
    except Exception as e:
        # Strategy 2: Fallback to custom algorithm
        stitched_image = self._stitch_with_custom_algorithm(input_data)
```

**Why OpenCV Stitcher is Better**:
- Uses Multi-band Blending (true multi-resolution blending)
- Automatic exposure compensation
- Optimized seam finding
- Handles parallax and exposure differences
- No black lines or visible seams

**Testing Strategy**:
1. Always test with real images, not just synthetic test cases
2. Test both image orderings (A+B and B+A)
3. Check for:
   - Black lines in middle region
   - Ghosting artifacts (duplicated objects)

---

### 23. Image Stitching Process Method Clears Input List

**Problem**: `process()` method immediately clears `_input_data_list`, causing "至少需要两张图像" error even when 2+ images are provided.

**Symptom**:
```
列表状态: 2张, 计数: 2
运行拼接...
至少需要两张图像进行拼接
拼接失败: 至少需要两张图像进行拼接
```

**Root Cause**:
```python
def process(self, input_data: List[ImageData]) -> ResultData:
    result = ResultData()
    # BUG: This line clears the list before processing!
    if hasattr(self, "_input_data_list"):
        self._input_data_list.clear()  # ← Problem here
    result.tool_name = self._name
    
    # ... later code checks len(input_data) which is now 0
    if len(input_data) < 2:
        result.status = False
        result.message = "至少需要两张图像进行拼接"
```

**Solution**: Remove the premature clearing:
```python
def process(self, input_data: List[ImageData]) -> ResultData:
    result = ResultData()
    # REMOVED: Incorrect clearing that caused the bug
    result.tool_name = self._name
    
    # Only clear after successful processing in run() method
```

**Lessons**:
1. Don't clear input data at the start of processing
2. Clear accumulated data only after successful processing or in set_input() when detecting new cycle
3. Keep input data intact until processing is complete

---

### 24. Image Stitching Performance and Ghosting Optimization

**Problem**: Image stitching is slow and produces ghosting artifacts.

**Root Causes**:
1. **Slow Performance**: Using SIFT with too many feature points (5000+)
2. **Ghosting**: Linear weight blending causes semi-transparent overlap
3. **Inaccurate Matching**: Too many low-quality matches included
4. **Improper Preprocessing**: Heavy CLAHE and morphological operations

**Solutions Implemented**:

```python
# 1. Performance Optimization - Use ORB with reduced features
def _create_feature_detector(self):
    performance_mode = self._params.get("performance_mode", "balanced")
    if performance_mode == "fast":
        nfeatures = 800
    elif performance_mode == "balanced":
        nfeatures = 1500
    else:  # quality
        nfeatures = 3000
    
    return cv2.ORB_create(
        nfeatures=nfeatures,
        scaleFactor=1.2,  # Larger = fewer pyramid levels = faster
        nlevels=6,        # Reduced from 8
        fastThreshold=20, # Higher = fewer features = faster
    )

# 2. Ghosting Fix - Steep sigmoid weight transition
def _blend_images(self, img1, img2, mask1, mask2):
    # Use sigmoid for steep transition (not linear)
    ratio = d1 / (d1 + d2 + 1e-6)
    steepness = 10.0
    w1 = 1.0 / (1.0 + np.exp(-steepness * (ratio - 0.5)))
    w2 = 1.0 - w1
    
    # Small kernel to keep edges sharp
    kernel_size = 11  # Reduced from 21
    weight1 = cv2.GaussianBlur(weight1, (kernel_size, kernel_size), 3)

# 3. Better Matching - Use crossCheck and limit matches
def _create_matcher(self):
    # Use BFMatcher with crossCheck=True (one call, bidirectional check)
    return cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def _match_features(self, features1, features2):
    matches = self._matcher.match(desc1, desc2)
    matches = sorted(matches, key=lambda x: x.distance)
    
    # Limit to top 100 matches
    max_matches = 100
    if len(matches) > max_matches:
        matches = matches[:max_matches]

# 4. Fast Preprocessing - Skip heavy operations
def preprocess_image(self, image, fast_mode=True):
    if fast_mode:
        # Fast mode: only Gaussian blur
        return cv2.GaussianBlur(gray, (3, 3), 0.5)
    else:
        # Quality mode: full preprocessing
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        # ... morphological operations
```

**New Parameters Added** (Chinese labels):
```python
"performance_mode": {
    "name": "性能模式",
    "options": ["fast", "balanced", "quality"],
    "option_labels": {
        "fast": "快速模式 (速度优先)",
        "balanced": "平衡模式 (推荐)",
        "quality": "高质量模式 (质量优先)",
    },
},
"fast_mode": {
    "name": "快速预处理",
    "description": "启用快速预处理模式，减少图像预处理时间",
},
```

**Performance Results**:
| Configuration | Time | Speedup |
|--------------|------|---------|
| Before (SIFT) | ~0.5s | 1x |
| After (ORB fast) | ~0.03s | **17x** |
| After (ORB balanced) | ~0.03s | **17x** |
| After (SIFT quality) | ~0.46s | 1.1x |

**Lessons**:
1. ORB is 10-20x faster than SIFT with comparable quality for stitching
2. Use steep weight transitions (sigmoid) instead of linear blending to reduce ghosting
3. Limit feature points and matches for better performance
4. Use crossCheck=True in BFMatcher for better match quality with single call
5. Provide performance modes to let users choose speed/quality tradeoff
   - Exposure discontinuities
   - Geometric misalignment

**File Organization**:
- Keep test outputs in `test_outputs/` folder
- Don't commit test images to repository
- Clean up temporary test files regularly

**Code Maintenance**:
- Don't remove working algorithms until new ones are fully tested
- Keep fallback methods as backup
- Log which algorithm was used (for debugging)
- Document algorithm selection strategy in code comments

---

### 34. Barcode Recognition Result Display Issue

**Problem**: Barcode recognition tool results not displaying or displaying abnormally in result panel.

**Symptom**:
- Barcode recognition tool executes but result panel shows nothing
- Or results displayed incorrectly
- Data selector cannot access barcode data fields

**Root Cause**:
1. Missing `tool_name` and `result_category` settings in ResultData
2. Using `barcodes` field name but result panel expects `codes` field
3. Wrong `result_category` value ("recognition" instead of "barcode")

**Solution**:
```python
# In tools/vision/recognition.py
self._result_data = ResultData()
self._result_data.tool_name = self._name
self._result_data.result_category = "barcode"  # Must match panel expectations

# Use 'codes' field to match result panel
self._result_data.set_value("codes", results)
# Keep 'barcodes' for backward compatibility
self._result_data.set_value("barcodes", results)
```

**Key Points**:
1. Always set `tool_name` and `result_category` when creating ResultData
2. Use field names that match result panel expectations
3. Check `enhanced_result_panel.py` for expected field names and categories

---

### 35. Result Panel Not Synchronized When Deleting Tools

**Problem**: After deleting a tool from algorithm editor, its results remain in result panel.

**Symptom**:
- Delete a tool from algorithm editor
- Result panel still shows the deleted tool's results
- Results accumulate over time

**Root Cause**:
- Adding results uses `tool.name` (instance name like "Barcode_1")
- Removing results uses `tool.tool_name` (type name like "Barcode")
- Name mismatch prevents proper removal

**Solution**:
```python
# In ui/main_window.py remove_tool method
# Use tool.name (instance name) not tool.tool_name (type name)
self.result_dock.remove_result_by_tool_name(tool.name)
```

**Key Points**:
1. Use consistent naming when adding and removing results
2. Instance name (`tool.name`) is preferred to distinguish multiple tools of same type
3. Add comments explaining the naming choice

---

### 36. Missing Result Data in Algorithm Tools

**Problem**: Many algorithm tools lack proper ResultData initialization.

**Symptom**:
- Tools execute but don't show results in result panel
- Data selector shows no available data from these tools
- Inconsistent behavior across different tool types

**Affected Tools**:
- OCR tools (ChineseOCR, EnglishOCR)
- Appearance detection
- Calibration
- Geometric transform
- Image saver

**Root Cause**:
- Tools create `_result_data` but don't set `tool_name` and `result_category`
- Some tools don't create `_result_data` at all
- Result panel cannot categorize and display results properly

**Solution**:
```python
# Standard pattern for all tools
self._result_data = ResultData()
self._result_data.tool_name = self._name
self._result_data.result_category = "appropriate_category"
# Then set tool-specific values
self._result_data.set_value("key", value)
```

**Categories by Tool Type**:
- Barcode: "barcode"
- QR Code: "qrcode"
- OCR: "ocr"
- Detection: "detection"
- Calibration: "calibration"
- Matching: "match"
- Transform: "transform"
- Saver: "saver"

---

### 37. Barcode Result Data Structure Optimization

**Problem**: Barcode results stored as nested list, making it hard to select individual fields.

**Symptom**:
- Data shows as `[{'data': '123', 'type': 'EAN13', ...}]` in selector
- Cannot easily select just the barcode data or type
- Sending data requires complex parsing

**Solution**:
```python
# Split first barcode result into separate fields
if results:
    first_code = results[0]
    self._result_data.set_value("code_data", first_code.get("data", ""))
    self._result_data.set_value("code_type", first_code.get("type", ""))
    rect = first_code.get("rect", {})
    self._result_data.set_value("code_x", rect.get("x", 0))
    self._result_data.set_value("code_y", rect.get("y", 0))
    self._result_data.set_value("code_width", rect.get("width", 0))
    self._result_data.set_value("code_height", rect.get("height", 0))
```

**Benefits**:
1. Users can select specific fields (data, type, position)
2. Easier to send individual values via communication tools
3. Better integration with data extraction rules

---

### 38. Data Selector Field Name Translation

**Problem**: Data selector shows English field names instead of Chinese.

**Symptom**:
- Field names like "code_data", "stitched_width" shown in English
- Users cannot understand what each field represents
- Poor user experience for Chinese users

**Solution**:
```python
# In ui/data_selector.py _translate_field_name method
translations = {
    # Barcode fields
    "code_data": "码值内容",
    "code_type": "码类型",
    "code_x": "码X坐标",
    "code_y": "码Y坐标",
    "code_width": "码宽度",
    "code_height": "码高度",
    # Add translations for all tool-specific fields
}
```

**Key Points**:
1. Maintain translation dictionary for all exposed fields
2. Use descriptive Chinese names
3. Keep English field name in parentheses for reference

---

### 39. Communication Auto-Connect After Solution Load

**Problem**: After saving communication settings and reopening application, all connections need manual reconnection.

**Root Cause**: `ConnectionManager.load_from_solution()` method loads configuration but doesn't trigger auto-connect logic.

**Solution**:
```python
# In ui/communication_config.py

# 1. Add _auto_connect_all() method
def _auto_connect_all(self):
    """Auto-connect all configured connections"""
    for conn_id, connection in self._connections.items():
        auto_connect = connection.config.get("auto_connect", True)
        if auto_connect:
            self._create_and_connect_async(connection)

# 2. Call after loading configuration
def load_from_solution(self, communication_config: List[Dict]):
    # ... load connections ...
    self._auto_connect_all()  # Auto-connect all

# 3. Add UI option for auto-connect
# In ConnectionConfigDialog.setup_ui()
self.auto_connect_check = QCheckBox("程序启动时自动建立连接")
self.auto_connect_check.setChecked(True)

# 4. Save auto_connect setting in config
config["auto_connect"] = self.auto_connect_check.isChecked()
```

---

### 40. ROI Editor Live Preview and Mode Switching

**Problem**: 
1. ROI box only appears after drawing is complete
2. Cannot pan/move image while in ROI drawing mode

**Root Causes**:
1. No live preview during drawing
2. All mouse events used for drawing, no pan mode

**Solution**:
```python
# In ui/roi_selection_dialog.py

# 1. Add mode switching UI
self._btn_draw_mode = QRadioButton("绘制ROI模式")
self._btn_pan_mode = QRadioButton("拖拽移动模式")

# 2. Add mode variables
self._is_draw_mode = True   # True=ROI drawing, False=pan mode
self._offset_x = 0.0        # Image offset for panning
self._offset_y = 0.0

# 3. Add set_draw_mode() method
def set_draw_mode(self, is_draw_mode: bool):
    self._is_draw_mode = is_draw_mode
    if is_draw_mode:
        self.setCursor(Qt.CursorShape.CrossCursor)
    else:
        self.setCursor(Qt.CursorShape.OpenHandCursor)

# 4. Modify mouse events to handle both modes
def mousePressEvent(self, event):
    if not self._is_draw_mode:
        # Pan mode - start panning
        self._is_panning = True
        self._pan_start = event.pos()
        self._pan_offset_start = (self._offset_x, self._offset_y)
        return
    # Drawing mode - draw ROI
    self._is_drawing = True
    ...

# 5. Add live preview method
def _draw_preview_rect(self, painter, offset_x, offset_y):
    """Draw preview rectangle during drawing"""
    # Draw semi-transparent green fill
    # Draw green border
    # Show coordinates and size info

# 6. Fix coordinate calculations with offset
# All x, y calculations must include offset
x = (self.width() - self._image.width() * self._scale) / 2 + self._offset_x
y = (self.height() - self._image.height() * self._scale) / 2 + self._offset_y
```

**Common Mistakes to Avoid**:
1. Don't reset offset when switching modes (user expects to continue from where they left)
2. Use tuples instead of QPointF for offset storage (QPointF may not be imported)
3. Add offset to ALL coordinate calculations (mousePress, mouseMove, mouseRelease, paintEvent)
4. Initialize offset variables in __init__

---

### 41. Documentation Update Checklist

**Required Updates After New Features**:

1. **CHANGELOG.md** (Root directory) - Update changelog with new features/fixes
2. **README.md** - Update project header with latest update date
3. **documentation/INDEX.md** - Add new documentation links if created
4. **AGENTS.md** - Add lessons learned if it's a common pattern

**Key Rules**:
1. **Don't create duplicate documents** - Check if CHANGELOG.md already exists
2. **Update existing documents** - Prefer updating CHANGELOG.md over creating new files
3. **Complete index** - Ensure INDEX.md includes all documentation

**Example Update Pattern**:
```markdown
# In CHANGELOG.md
## [Unreleased] - YYYY-MM-DD

### 🚀 New Features
- Feature description

### 🐛 Bug Fixes
- Fixed issue

### 📝 Documentation
- Updated AGENTS.md
```

**Remember**: 
- Always update CHANGELOG.md when adding new features or fixing bugs!
- Check INDEX.md to ensure all docs are properly linked
- Don't create new files if existing ones can be updated

---

### 42. Image Slice Tool Development Issues

**Problems Encountered**:

1. **Tool Not Registered**: Error "未找到工具: Vision.图像切片" when creating tool
   
   **Root Cause**: New tool module not imported in `tools/vision/__init__.py`
   
   **Solution**: Add import in `tools/vision/__init__.py`:
   ```python
   from .image_slice import ImageSliceTool
   ```

2. **option_labels Parameter Error**: `TypeError: ToolBase.set_param() got an unexpected keyword argument 'option_labels'`
   
   **Root Cause**: Using `option_labels` in `set_param()` call instead of `PARAM_DEFINITIONS`
   
   **Solution**: Define parameters with `option_labels` in `PARAM_DEFINITIONS` dictionary:
   ```python
   PARAM_DEFINITIONS = {
       "切片模式": ToolParameter(
           name="切片模式",
           param_type="enum",
           default="extract",
           options=["extract", "remove"],
           option_labels={  # Only in PARAM_DEFINITIONS!
               "extract": "提取（保留选中区域）",
               "remove": "去除（删除选中区域）",
           },
       ),
   }
   ```

3. **Missing Method Error**: `'ImageSliceTool' object has no attribute 'get_input_data_recursive'`
   
   **Root Cause**: Using wrong method to get upstream data
   
   **Solution**: Use `get_upstream_values()` instead:
   ```python
   upstream_values = self.get_upstream_values()
   ```

4. **Tuple vs Dict Error**: `'tuple' object has no attribute 'get'`
   
   **Root Cause**: GrayMatch returns matches as tuples `[(x, y, score), ...]` not dicts
   
   **Solution**: Handle both tuple and dict formats:
   ```python
   for item in value:
       if isinstance(item, tuple):
           matches.append({
               "x": item[0],
               "y": item[1],
               "score": item[2] if len(item) > 2 else 0,
           })
       elif isinstance(item, dict):
           matches.append(item)
   ```

5. **Property Panel Not Updated After Auto-Increment**:
   
   **Root Cause**: UI doesn't refresh when parameter changes programmatically
   
   **Solution**: Manually call `update_parameter()` after changing parameter:
   ```python
   # In main_window.py after tool.run()
   new_index = tool.get_param("结果索引", 0)
   self.property_dock.update_parameter("结果索引", new_index)
   ```

**Key Points**:
1. Always add new tool imports to `tools/vision/__init__.py`
2. Use `PARAM_DEFINITIONS` for complex parameter definitions (enum with labels)
3. Use correct method names: `get_upstream_values()` not `get_input_data_recursive()`
4. Handle different data formats from different tools (tuple vs dict)
5. Property panel needs manual refresh after programmatic parameter changes

---

### 43. Performance Optimization Integration Issues

**Problems Encountered**:

1. **Import Error After Adding Numba Code**: `unmatched ')' (template_match.py, line 45)`

   **Root Cause**: After adding try/except block for Numba import, accidentally deleted closing parenthesis of the import statement

   **Solution**: Ensure import statements are properly formatted:
   ```python
   # Wrong - missing closing parenthesis
   from utils.image_processing_utils import (
       preprocess_image,
       non_maximum_suppression,
   )
   
   USE_NUMBA = False
   try:
       from core.numba_utils import ssd_match_parallel
   except ImportError:
       pass
   
   # Correct - imports placed AFTER try/except
   from utils.image_processing_utils import (
       preprocess_image,
       non_maximum_suppression,
       draw_matches,
       draw_lines,
   )
   
   USE_NUMBA = False
   try:
       from core.numba_utils import ssd_match_parallel
   except ImportError:
       pass
   ```

2. **Image Color Issue After Optimization**: Saved images appear blue/tinted

   **Root Cause**: Pillow uses RGB format, OpenCV uses BGR format. When saving with Pillow without conversion, colors are swapped (BGR → RGB = blue/tinted)

   **Solution**: Convert BGR to RGB before saving with Pillow:
   ```python
   def save_image_fast(image: np.ndarray, path: str, quality: int = 95) -> bool:
       if PIL_AVAILABLE:
           # Convert BGR to RGB for 3-channel images
           if len(image.shape) == 3 and image.shape[2] == 3:
               image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
           img = PILImage.fromarray(image)
           img.save(path, quality=quality, optimize=True)
           return True
   ```

3. **Integration Best Practices**

   **Key Points**:
   - Always test integration before committing
   - Use graceful fallback when optimization modules unavailable
   - Maintain backward compatibility with existing code
   - Test color channels after image format conversion

4. **Performance Optimization Modules Created**

   **Modules**:
   - `core/parallel_processing.py` - joblib-based parallel processing
   - `core/numba_utils.py` - Numba JIT compilation functions
   - `core/image_utils.py` - Fast image I/O with Pillow-SIMD

   **Integration**:
   - `tools/image_source.py` - Uses `load_image_fast()`
   - `tools/vision/image_saver.py` - Uses `save_image_fast()`
   - `tools/vision/template_match.py` - Uses `ssd_match_parallel()` for SSD mode
