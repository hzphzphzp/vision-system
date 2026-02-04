#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据映射可视化编辑器

提供可视化界面配置数据映射规则，用于SendDataTool的数据转换。

功能特性:
- 可视化字段映射配置
- 添加/删除映射规则
- 导入/导出映射配置
- 支持嵌套字段映射

Author: Vision System Team
Date: 2026-02-04
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class DataMappingEditor(QDialog):
    """数据映射规则编辑器对话框"""

    def __init__(self, parent=None, current_mapping: str = ""):
        super().__init__(parent)
        self.setWindowTitle("数据映射配置")
        self.resize(700, 500)
        self.setMinimumSize(600, 400)

        self._mapping = {}
        self._load_mapping(current_mapping)

        self.setup_ui()
        self.load_mapping()

    def _load_mapping(self, mapping_str: str):
        """加载映射配置"""
        if mapping_str:
            try:
                if isinstance(mapping_str, str):
                    self._mapping = json.loads(mapping_str)
                elif isinstance(mapping_str, dict):
                    self._mapping = mapping_str
            except (json.JSONDecodeError, TypeError) as e:
                print(f"加载映射配置失败: {e}")
                self._mapping = {}

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 说明标签
        info_label = QLabel("配置上游字段到发送字段的映射规则，支持嵌套字段（如 position.x）")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)

        # 映射表格
        table_group = QGroupBox("映射规则")
        table_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["上游字段", "发送字段", "转换函数", "操作"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 80)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 按钮区域
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("添加映射")
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_mapping_row)
        btn_layout.addWidget(add_btn)

        import_btn = QPushButton("导入...")
        import_btn.setMinimumWidth(80)
        import_btn.clicked.connect(self.import_mapping)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("导出...")
        export_btn.setMinimumWidth(80)
        export_btn.clicked.connect(self.export_mapping)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 预览区域
        preview_group = QGroupBox("JSON预览")
        preview_layout = QVBoxLayout()

        self.preview_edit = QLineEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("配置的映射规则将显示为JSON格式...")
        preview_layout.addWidget(self.preview_edit)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # 确定/取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        ok_btn = button_box.button(QDialogButtonBox.Ok)
        ok_btn.setText("确定")
        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("取消")

        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_mapping(self):
        """加载现有映射到表格"""
        self.table.setRowCount(0)

        for source, target in self._mapping.items():
            # 只处理字符串类型的target（简单映射），跳过包含转换函数的复杂映射
            if isinstance(target, str):
                self.add_mapping_row(source, target)
            elif isinstance(target, dict) and "target" in target:
                # 处理包含转换函数的映射
                self.add_mapping_row(
                    source,
                    target.get("target", ""),
                    target.get("transform", "")
                )

        self.update_preview()

    def add_mapping_row(self, source: str = "", target: str = "", transform: str = ""):
        """添加映射行"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 上游字段输入
        source_edit = QLineEdit(source)
        source_edit.setPlaceholderText("例如: result.position.x")
        source_edit.textChanged.connect(self.update_preview)
        self.table.setCellWidget(row, 0, source_edit)

        # 发送字段输入
        target_edit = QLineEdit(target)
        target_edit.setPlaceholderText("例如: x_coord")
        target_edit.textChanged.connect(self.update_preview)
        self.table.setCellWidget(row, 1, target_edit)

        # 转换函数选择
        transform_combo = QComboBox()
        transform_combo.addItems(["无", "to_int", "to_float", "to_string", "bool_to_okng"])
        transform_combo.setCurrentText(transform if transform else "无")
        transform_combo.currentTextChanged.connect(self.update_preview)
        self.table.setCellWidget(row, 2, transform_combo)

        # 删除按钮
        del_btn = QPushButton("删除")
        del_btn.setMinimumWidth(60)
        del_btn.clicked.connect(lambda: self.delete_row(row))
        self.table.setCellWidget(row, 3, del_btn)

    def delete_row(self, row: int):
        """删除行"""
        self.table.removeRow(row)
        self.update_preview()

    def update_preview(self):
        """更新预览"""
        mapping = self.get_mapping()
        try:
            json_str = json.dumps(mapping, ensure_ascii=False, indent=2)
            self.preview_edit.setText(json_str)
        except Exception:
            self.preview_edit.setText("")

    def get_mapping(self) -> dict:
        """获取当前映射配置"""
        mapping = {}

        for row in range(self.table.rowCount()):
            source_widget = self.table.cellWidget(row, 0)
            target_widget = self.table.cellWidget(row, 1)
            transform_widget = self.table.cellWidget(row, 2)

            if source_widget and target_widget:
                source = source_widget.text().strip()
                target = target_widget.text().strip()

                if source and target:
                    # 构建映射规则
                    if transform_widget and transform_widget.currentText() != "无":
                        mapping[source] = {
                            "target": target,
                            "transform": transform_widget.currentText()
                        }
                    else:
                        mapping[source] = target

        return mapping

    def get_mapping_json(self) -> str:
        """获取映射JSON字符串"""
        mapping = self.get_mapping()
        return json.dumps(mapping, ensure_ascii=False, indent=2)

    def import_mapping(self):
        """导入映射配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入映射配置",
            "",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)

                if isinstance(mapping, dict):
                    self._mapping = mapping
                    self.load_mapping()
                    QMessageBox.information(self, "成功", "映射配置导入成功")
                else:
                    QMessageBox.warning(self, "警告", "无效的映射配置格式")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def export_mapping(self):
        """导出映射配置"""
        mapping = self.get_mapping()

        if not mapping:
            QMessageBox.warning(self, "警告", "没有可导出的映射配置")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出映射配置",
            "data_mapping.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "映射配置导出成功")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def accept(self):
        """确认对话框"""
        mapping = self.get_mapping()

        if not mapping:
            reply = QMessageBox.question(
                self,
                "确认",
                "未配置任何映射规则，是否确定？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        super().accept()


class DataMappingSimpleEditor(QDialog):
    """简化版数据映射编辑器 - 用于SendDataTool参数配置"""

    def __init__(self, parent=None, current_mapping: str = ""):
        super().__init__(parent)
        self.setWindowTitle("数据映射")
        self.resize(500, 300)
        self.setMinimumSize(450, 250)

        self._mapping = {}
        self._load_mapping(current_mapping)

        self.setup_ui()
        self.load_mapping()

    def _load_mapping(self, mapping_str: str):
        """加载映射配置"""
        if mapping_str:
            try:
                if isinstance(mapping_str, str):
                    self._mapping = json.loads(mapping_str)
                elif isinstance(mapping_str, dict):
                    self._mapping = mapping_str
            except (json.JSONDecodeError, TypeError):
                self._mapping = {}

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel("配置字段映射（上游字段 → 发送字段）："))

        # 映射表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["上游字段", "发送字段", ""])
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 60)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        layout.addWidget(self.table)

        # 添加按钮
        add_btn = QPushButton("添加映射")
        add_btn.clicked.connect(self.add_mapping_row)
        layout.addWidget(add_btn)

        layout.addStretch()

        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_mapping(self):
        """加载现有映射"""
        self.table.setRowCount(0)

        for source, target in self._mapping.items():
            if isinstance(target, str):
                self.add_mapping_row(source, target)

    def add_mapping_row(self, source: str = "", target: str = ""):
        """添加映射行"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        source_edit = QLineEdit(source)
        source_edit.setPlaceholderText("上游字段")
        self.table.setCellWidget(row, 0, source_edit)

        target_edit = QLineEdit(target)
        target_edit.setPlaceholderText("发送字段")
        self.table.setCellWidget(row, 1, target_edit)

        del_btn = QPushButton("X")
        del_btn.setMaximumWidth(40)
        del_btn.clicked.connect(lambda: self.delete_row(row))
        self.table.setCellWidget(row, 2, del_btn)

    def delete_row(self, row: int):
        """删除行"""
        self.table.removeRow(row)

    def get_mapping_json(self) -> str:
        """获取映射JSON字符串"""
        mapping = {}

        for row in range(self.table.rowCount()):
            source_widget = self.table.cellWidget(row, 0)
            target_widget = self.table.cellWidget(row, 1)

            if source_widget and target_widget:
                source = source_widget.text().strip()
                target = target_widget.text().strip()

                if source and target:
                    mapping[source] = target

        return json.dumps(mapping, ensure_ascii=False, indent=2)

    def accept(self):
        """确认"""
        super().accept()


def edit_mapping(parent=None, current_mapping: str = "") -> str:
    """编辑数据映射的便捷函数

    Args:
        parent: 父窗口
        current_mapping: 当前映射配置（JSON字符串）

    Returns:
        新的映射配置JSON字符串，如果取消返回空字符串
    """
    dialog = DataMappingSimpleEditor(parent, current_mapping)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_mapping_json()
    return ""


# 测试代码
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # 测试完整版编辑器
    dialog = DataMappingEditor()
    result = dialog.exec_()

    if result == QDialog.Accepted:
        mapping_json = dialog.get_mapping_json()
        print("映射配置:")
        print(mapping_json)

    sys.exit(0)
