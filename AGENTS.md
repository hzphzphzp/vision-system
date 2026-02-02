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
