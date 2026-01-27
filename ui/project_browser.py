#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目浏览器UI模块

实现VisionMaster风格的项目浏览器，包括：
- 方案、流程、工具的层次结构显示
- 项目结构管理
- 双击编辑功能
- 右键菜单支持
- 拖拽操作支持
- 实时项目结构更新

Author: Vision System Team
Date: 2026-01-05
"""

import sys
import os
import logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

PYQT_VERSION = 5

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
        QTreeWidgetItem, QMenu, QAction, QLineEdit, QSplitter, QDockWidget, 
        QFrame, QDialog, QFormLayout, QDialogButtonBox, QInputDialog
    )
    from PyQt6.QtGui import QFont, QColor, QIcon
    from PyQt6.QtCore import Qt, pyqtSignal, QObject
    PYQT_VERSION = 6
except Exception:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
        QTreeWidgetItem, QMenu, QAction, QLineEdit, QSplitter, QDockWidget, 
        QFrame, QDialog, QFormLayout, QDialogButtonBox, QInputDialog
    )
    from PyQt5.QtGui import QFont, QColor, QIcon
    from PyQt5.QtCore import Qt, pyqtSignal, QObject

from core.solution import Solution
from core.procedure import Procedure
from core.tool_base import ToolBase


class ItemType(Enum):
    """项目树节点类型"""
    SOLUTION = "solution"    # 方案
    PROCEDURE = "procedure"  # 流程
    TOOL = "tool"           # 工具
    FOLDER = "folder"       # 文件夹


class ProjectTreeItem(QTreeWidgetItem):
    """项目树节点"""
    
    def __init__(self, item_type: ItemType, name: str, item_obj: Any = None, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("ProjectTreeItem")
        self._type = item_type
        self._object = item_obj
        self._name = name
        
        # 设置节点显示
        self._update_display()
    
    @property
    def type(self) -> ItemType:
        """获取节点类型"""
        return self._type
    
    @property
    def object(self) -> Any:
        """获取节点对应的对象"""
        return self._object
    
    @property
    def name(self) -> str:
        """获取节点名称"""
        return self._name
    
    def set_name(self, name: str):
        """设置节点名称"""
        self._name = name
        self._update_display()
        
        # 更新对应的对象名称
        if self._object:
            if hasattr(self._object, 'name'):
                self._object.name = name
    
    def _update_display(self):
        """更新节点显示"""
        # 设置节点文本
        self.setText(0, self._name)
        
        # 设置节点图标和颜色
        if self._type == ItemType.SOLUTION:
            self.setIcon(0, QIcon.fromTheme("document"))
            self.setForeground(0, QColor(0, 0, 128))
        elif self._type == ItemType.PROCEDURE:
            self.setIcon(0, QIcon.fromTheme("folder"))
            self.setForeground(0, QColor(0, 128, 0))
        elif self._type == ItemType.TOOL:
            self.setIcon(0, QIcon.fromTheme("application-x-executable"))
            self.setForeground(0, QColor(128, 0, 128))
        elif self._type == ItemType.FOLDER:
            self.setIcon(0, QIcon.fromTheme("folder"))
            self.setForeground(0, QColor(128, 128, 0))
    
    def update_from_object(self):
        """从对象更新节点显示"""
        if self._object:
            if hasattr(self._object, 'name'):
                self._name = self._object.name
            self._update_display()


class ProjectBrowserWidget(QWidget):
    """项目浏览器"""
    
    # 信号
    item_double_clicked = pyqtSignal(str, object)  # item_type, item_object
    item_selected = pyqtSignal(str, object)        # item_type, item_object
    item_deleted = pyqtSignal(str, object)         # item_type, item_object
    item_renamed = pyqtSignal(str, object, str)    # item_type, item_object, new_name
    procedure_created = pyqtSignal(object)         # 新建的流程对象
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger("ProjectBrowserWidget")
        self._solution: Optional[Solution] = None
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("项目浏览器")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # 控制栏
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 5)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._on_refresh)
        control_layout.addWidget(refresh_btn)
        
        # 新建流程按钮
        new_proc_btn = QPushButton("新建流程")
        new_proc_btn.clicked.connect(self._on_new_procedure)
        control_layout.addWidget(new_proc_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._on_delete)
        control_layout.addWidget(delete_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # 项目树
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels(["名称", "类型"])
        self.project_tree.setColumnWidth(0, 180)
        self.project_tree.setColumnWidth(1, 80)
        
        # 连接信号
        self.project_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.project_tree.itemSelectionChanged.connect(self._on_item_selected)
        self.project_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_tree.customContextMenuRequested.connect(self._on_context_menu)
        
        main_layout.addWidget(self.project_tree)
    
    def set_solution(self, solution: Solution):
        """设置当前方案
        
        Args:
            solution: 方案对象
        """
        self._solution = solution
        self._refresh_tree()
    
    def get_solution(self) -> Optional[Solution]:
        """获取当前方案"""
        return self._solution
    
    def _refresh_tree(self):
        """刷新项目树"""
        self._logger.info(f"刷新项目树 - 流程数量: {len(self._solution.procedures) if self._solution else 0}")
        self.project_tree.clear()
        
        if self._solution is None:
            return
        
        # 创建方案根节点
        solution_item = ProjectTreeItem(ItemType.SOLUTION, self._solution.name, self._solution)
        solution_item.setText(1, "方案")
        self.project_tree.addTopLevelItem(solution_item)
        
        # 创建流程节点
        procedures_item = ProjectTreeItem(ItemType.FOLDER, "流程", None, solution_item)
        procedures_item.setText(1, "文件夹")
        
        # 添加流程
        for i, procedure in enumerate(self._solution.procedures):
            self._logger.info(f"  流程[{i}]: {procedure.name}, 工具数量: {procedure.tool_count}")
            proc_item = ProjectTreeItem(ItemType.PROCEDURE, procedure.name, procedure, procedures_item)
            proc_item.setText(1, "流程")
            
            # 添加工具
            for j, tool in enumerate(procedure.tools):
                self._logger.info(f"    工具[{j}]: {tool.name} ({tool.tool_name})")
                tool_item = ProjectTreeItem(ItemType.TOOL, tool.name, tool, proc_item)
                tool_item.setText(1, tool.tool_name)
        
        # 展开所有节点
        self.project_tree.expandAll()
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """节点双击事件"""
        if isinstance(item, ProjectTreeItem):
            self._logger.info(f"双击节点: {item.name} ({item.type.value})")
            self.item_double_clicked.emit(item.type.value, item.object)
    
    def _on_item_selected(self):
        """节点选择变化事件"""
        selected_items = self.project_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if isinstance(item, ProjectTreeItem):
                self._logger.info(f"选择节点: {item.name} ({item.type.value})")
                self.item_selected.emit(item.type.value, item.object)
    
    def _on_context_menu(self, position):
        """上下文菜单事件"""
        item = self.project_tree.itemAt(position)
        if not item or not isinstance(item, ProjectTreeItem):
            return
        
        # 创建上下文菜单
        menu = QMenu(self)
        
        # 添加重命名菜单项
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self._on_rename(item))
        menu.addAction(rename_action)
        
        # 添加删除菜单项
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._on_delete_item(item))
        menu.addAction(delete_action)
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加展开/折叠菜单项
        expand_action = QAction("展开", self)
        expand_action.triggered.connect(lambda: item.setExpanded(True))
        menu.addAction(expand_action)
        
        collapse_action = QAction("折叠", self)
        collapse_action.triggered.connect(lambda: item.setExpanded(False))
        menu.addAction(collapse_action)
        
        # 显示菜单
        menu.exec(self.project_tree.viewport().mapToGlobal(position))
    
    def _on_rename(self, item: ProjectTreeItem):
        """重命名节点"""
        # 使用QInputDialog获取新名称
        new_name, ok = QInputDialog.getText(self, "重命名", f"输入{item.type.value}的新名称:", text=item.name)
        if ok and new_name:
            old_name = item.name
            item.set_name(new_name)
            self._logger.info(f"重命名{item.type.value}: {old_name} -> {new_name}")
            self.item_renamed.emit(item.type.value, item.object, new_name)
    
    def _on_delete_item(self, item: ProjectTreeItem):
        """删除节点"""
        self._logger.info(f"删除节点: {item.name} ({item.type.value})")
        
        # 检查item是否仍然有效（在主窗口处理后可能已被删除）
        if not item or not item.isSelected():
            self._logger.debug(f"节点已在前置处理中被删除: {item.name if item else 'unknown'}")
            return
        
        # 保存父节点引用
        try:
            parent = item.parent()
        except (RuntimeError, Exception):
            self._logger.debug(f"节点已被删除，无法获取父节点: {item.name}")
            return
        
        # 发送删除信号（主窗口处理时可能会调用refresh，所以先保存必要信息）
        self.item_deleted.emit(item.type.value, item.object)
        
        # 再次检查item是否仍然有效
        try:
            if item.parent() is None and parent is not None:
                self._logger.debug(f"节点已在前置处理中被删除: {item.name}")
                return
        except (RuntimeError, Exception):
            self._logger.debug(f"节点已被删除: {item.name}")
            return
        
        # 从树中移除
        if parent:
            parent.removeChild(item)
        else:
            self.project_tree.takeTopLevelItem(self.project_tree.indexOfTopLevelItem(item))
        
        # 从对应的对象中移除
        if item.type == ItemType.PROCEDURE and self._solution:
            self._solution.remove_procedure(item.name)
        elif item.type == ItemType.TOOL:
            parent_item = item.parent()
            if parent_item and hasattr(parent_item, 'object'):
                parent_obj = parent_item.object
                if parent_obj and hasattr(parent_obj, 'remove_tool'):
                    parent_obj.remove_tool(item.name)
    
    def _on_refresh(self):
        """刷新按钮点击事件"""
        self._refresh_tree()
    
    def _on_new_procedure(self):
        """新建流程按钮点击事件"""
        if self._solution is None:
            self._logger.error("没有当前方案，无法新建流程")
            return
        
        # 使用QInputDialog获取流程名称
        proc_name, ok = QInputDialog.getText(self, "新建流程", "输入流程名称:", text=f"流程{len(self._solution.procedures) + 1}")
        if ok and proc_name:
            from core.procedure import Procedure
            new_proc = Procedure(proc_name)
            self._solution.add_procedure(new_proc)
            self._refresh_tree()
            self._logger.info(f"新建流程: {proc_name}")
            # 发送新建流程信号，通知主窗口
            self.procedure_created.emit(new_proc)
    
    def _on_delete(self):
        """删除按钮点击事件"""
        selected_items = self.project_tree.selectedItems()
        if selected_items:
            self._on_delete_item(selected_items[0])
    
    def update_item(self, item_type: str, item_object: Any):
        """更新指定类型的指定对象的节点显示
        
        Args:
            item_type: 节点类型
            item_object: 对象实例
        """
        self._logger.info(f"更新节点: {item_type}")
        
        # 遍历树，找到对应的节点并更新
        def _update_recursive(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if isinstance(child, ProjectTreeItem):
                    if child.object is item_object:
                        child.update_from_object()
                        return True
                    if _update_recursive(child):
                        return True
            return False
        
        for i in range(self.project_tree.topLevelItemCount()):
            top_item = self.project_tree.topLevelItem(i)
            if _update_recursive(top_item):
                break


class ProjectBrowserDockWidget(QDockWidget):
    """项目浏览器停靠窗口"""
    
    # 信号
    item_double_clicked = pyqtSignal(str, Any)  # item_type, item_object
    item_selected = pyqtSignal(str, Any)        # item_type, item_object
    item_deleted = pyqtSignal(str, Any)         # item_type, item_object
    item_renamed = pyqtSignal(str, Any, str)    # item_type, item_object, new_name
    procedure_created = pyqtSignal(Any)         # 新建的流程对象
    
    def __init__(self, parent=None):
        super().__init__("项目浏览器", parent)
        self._logger = logging.getLogger("ProjectBrowserDockWidget")
        
        # 创建项目浏览器面板
        self.project_browser = ProjectBrowserWidget()
        self.setWidget(self.project_browser)
        
        # 设置停靠位置
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # 设置样式
        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #d0d0d0;
            }
            QDockWidget::title {
                background-color: #f5f5f5;
                padding: 5px;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        
        # 连接信号
        self.project_browser.item_double_clicked.connect(self.item_double_clicked)
        self.project_browser.item_selected.connect(self.item_selected)
        self.project_browser.item_deleted.connect(self.item_deleted)
        self.project_browser.item_renamed.connect(self.item_renamed)
        self.project_browser.procedure_created.connect(self.procedure_created)
    
    def set_solution(self, solution: Solution):
        """设置当前方案
        
        Args:
            solution: 方案对象
        """
        self.project_browser.set_solution(solution)
    
    def get_solution(self) -> Optional[Solution]:
        """获取当前方案"""
        return self.project_browser.get_solution()
    
    def refresh(self):
        """刷新项目树"""
        self.project_browser._refresh_tree()
    
    def update_item(self, item_type: str, item_object: Any):
        """更新指定类型的指定对象的节点显示
        
        Args:
            item_type: 节点类型
            item_object: 对象实例
        """
        self.project_browser.update_item(item_type, item_object)
    
    def get_project_browser(self) -> ProjectBrowserWidget:
        """获取项目浏览器实例"""
        return self.project_browser
