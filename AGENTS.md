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
