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
