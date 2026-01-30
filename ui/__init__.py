#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision System UI模块

提供主界面和所有可停靠窗口组件。

Author: Vision System Team
Date: 2025-01-04
"""

from ui.communication_dialog import (
    CommunicationConfigDialog,
    CommunicationMonitorWidget,
)
from ui.enhanced_result_dock import EnhancedResultDockWidget
from ui.enhanced_result_panel import (
    DataSelectorWidget,
    DataType,
    EnhancedResultPanel,
    ResultCategory,
    ResultDetailWidget,
    ResultPanelDockWidget,
)
from ui.main_window import MainWindow
from ui.project_browser import ProjectBrowserDockWidget
from ui.property_panel import PropertyDockWidget
from ui.result_panel import ResultDockWidget, ResultPanelWidget, ResultType
from ui.theme import VISION_MASTER_STYLE, apply_theme, get_style
from ui.tool_library import ToolLibraryDockWidget

__all__ = [
    "MainWindow",
    "ToolLibraryDockWidget",
    "PropertyDockWidget",
    "ResultDockWidget",
    "ResultType",
    "ResultPanelWidget",
    "ProjectBrowserDockWidget",
    "CommunicationConfigDialog",
    "CommunicationMonitorWidget",
    "EnhancedResultPanel",
    "ResultPanelDockWidget",
    "ResultDetailWidget",
    "DataSelectorWidget",
    "ResultCategory",
    "DataType",
    "EnhancedResultDockWidget",
    "get_style",
    "apply_theme",
    "VISION_MASTER_STYLE",
]
