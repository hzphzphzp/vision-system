#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据提取规则自定义控件

用于属性面板的自定义控件，提供：
- 规则配置按钮
- 当前规则显示
- 快速清除功能

Author: Vision System Team
Date: 2026-02-05
"""

import json
import sys
import os
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QToolButton, QMenu, QAction,
    QComboBox
)

from tools.communication.data_extraction_rules import (
    DataExtractionRule, ExtractionRuleType, create_default_rule
)
from ui.data_extraction_rule_dialog import DataExtractionRuleDialog


class ExtractionRuleWidget(QWidget):
    """
    数据提取规则配置控件
    
    用于属性面板，提供规则配置入口和当前规则状态显示
    """
    
    rule_changed = pyqtSignal(dict)  # 规则改变信号
    
    def __init__(self, parent=None, rule_data: Optional[Dict] = None):
        super().__init__(parent)
        
        self._rule: Optional[DataExtractionRule] = None
        if rule_data:
            try:
                self._rule = DataExtractionRule.from_dict(rule_data)
            except:
                self._rule = create_default_rule()
        else:
            self._rule = create_default_rule()
        
        self._init_ui()
        self._update_display()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 规则类型下拉框（主要选择方式）
        self.rule_type_combo = QComboBox()
        self.rule_type_combo.setMinimumWidth(150)
        self.rule_type_combo.setToolTip("选择数据提取规则类型")
        self.rule_type_combo.setEditable(False)  # 禁止手动输入
        self._populate_rule_types()
        self.rule_type_combo.currentIndexChanged.connect(self._on_rule_type_selected)
        layout.addWidget(self.rule_type_combo, stretch=2)
        
        # 配置按钮（用于详细配置）
        self.config_btn = QPushButton("⚙️")
        self.config_btn.setToolTip("详细配置")
        self.config_btn.setMaximumWidth(40)
        self.config_btn.clicked.connect(self._on_config_clicked)
        layout.addWidget(self.config_btn)
        
        # 清除按钮
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setToolTip("清除规则")
        self.clear_btn.setMaximumWidth(40)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_btn)
    
    def _populate_rule_types(self):
        """填充规则类型下拉框"""
        from tools.communication.data_extraction_rules import get_predefined_rules, ExtractionRuleType
        
        self.rule_type_combo.clear()
        
        # 添加预定义规则模板
        templates = get_predefined_rules()
        for name, rule in templates.items():
            self.rule_type_combo.addItem(name, rule)
        
        self.rule_type_combo.insertSeparator(self.rule_type_combo.count())
        
        # 添加基本规则类型
        basic_rules = [
            ("无提取规则", ExtractionRuleType.NONE),
            ("位提取", ExtractionRuleType.BIT_EXTRACT),
            ("多寄存器组合", ExtractionRuleType.REGISTER_COMBINE),
            ("数据类型转换", ExtractionRuleType.TYPE_CONVERT),
            ("缩放和偏移", ExtractionRuleType.SCALE_OFFSET),
            ("条件提取", ExtractionRuleType.CONDITIONAL),
        ]
        
        for name, rule_type in basic_rules:
            # 创建一个简单的规则对象
            rule = DataExtractionRule(rule_type=rule_type, name=name)
            self.rule_type_combo.addItem(f"📋 {name}", rule)
    
    def _on_rule_type_selected(self, index: int):
        """规则类型选择改变"""
        if index < 0:
            return
        
        rule = self.rule_type_combo.currentData()
        if rule and isinstance(rule, DataExtractionRule):
            # 如果是预定义模板，直接应用
            # 如果是基本类型，打开配置对话框进行详细配置
            if rule.name in ["温度传感器", "压力传感器", "32位整数组合", "浮点数转换", "状态位提取"]:
                # 预定义模板，直接应用
                self._apply_rule(rule)
            else:
                # 基本类型，打开配置对话框
                self._on_config_clicked()
    
    def _update_display(self):
        """更新显示"""
        # 临时断开信号，避免触发配置对话框
        self.rule_type_combo.blockSignals(True)
        
        if not self._rule:
            # 设置为"无提取规则"
            self._set_combo_by_rule_type(ExtractionRuleType.NONE)
            self.rule_type_combo.blockSignals(False)
            return
        
        # 根据规则类型设置下拉框
        self._set_combo_by_rule_type(self._rule.rule_type, self._rule.name)
        
        # 恢复信号
        self.rule_type_combo.blockSignals(False)
    
    def _set_combo_by_rule_type(self, rule_type: ExtractionRuleType, rule_name: str = ""):
        """根据规则类型设置下拉框选中项（注意：调用前需要手动blockSignals）"""
        # 查找匹配的项
        for i in range(self.rule_type_combo.count()):
            rule = self.rule_type_combo.itemData(i)
            if rule and isinstance(rule, DataExtractionRule):
                # 预定义模板匹配名称
                if rule.name == rule_name and rule_name in ["温度传感器", "压力传感器", "32位整数组合", "浮点数转换", "状态位提取"]:
                    self.rule_type_combo.setCurrentIndex(i)
                    return
                # 基本类型匹配类型
                elif rule.rule_type == rule_type and rule_name not in ["温度传感器", "压力传感器", "32位整数组合", "浮点数转换", "状态位提取"]:
                    self.rule_type_combo.setCurrentIndex(i)
                    return
        
        # 如果没有找到匹配的，设置为"无提取规则"
        for i in range(self.rule_type_combo.count()):
            rule = self.rule_type_combo.itemData(i)
            if rule and isinstance(rule, DataExtractionRule) and rule.rule_type == ExtractionRuleType.NONE:
                self.rule_type_combo.setCurrentIndex(i)
                break
    
    def _get_rule_summary(self) -> str:
        """获取规则摘要"""
        if not self._rule:
            return "无规则"
        
        type_names = {
            ExtractionRuleType.NONE: "无规则",
            ExtractionRuleType.BIT_EXTRACT: "位提取",
            ExtractionRuleType.REGISTER_COMBINE: "寄存器组合",
            ExtractionRuleType.TYPE_CONVERT: "类型转换",
            ExtractionRuleType.BYTE_ORDER: "字节序转换",
            ExtractionRuleType.SCALE_OFFSET: "缩放偏移",
            ExtractionRuleType.CONDITIONAL: "条件提取"
        }
        
        type_name = type_names.get(self._rule.rule_type, "未知")
        
        # 添加具体参数
        details = []
        
        if self._rule.bit_extract_rule:
            details.append(f"位{self._rule.bit_extract_rule.start_bit}-{self._rule.bit_extract_rule.start_bit + self._rule.bit_extract_rule.bit_count - 1}")
        
        if self._rule.register_combine_rule:
            indices = self._rule.register_combine_rule.register_indices
            details.append(f"寄存器{','.join(map(str, indices))}")
        
        if self._rule.type_convert_rule:
            src = self._rule.type_convert_rule.source_type.value
            dst = self._rule.type_convert_rule.target_type.value
            details.append(f"{src}→{dst}")
        
        if self._rule.scale_offset_rule:
            scale = self._rule.scale_offset_rule.scale
            offset = self._rule.scale_offset_rule.offset
            if scale != 1.0 or offset != 0.0:
                details.append(f"×{scale}+{offset}")
        
        if details:
            return f"{type_name} ({', '.join(details)})"
        return type_name
    
    def _on_config_clicked(self):
        """配置按钮点击"""
        dialog = DataExtractionRuleDialog(self, self._rule)
        if dialog.exec_() == DataExtractionRuleDialog.Accepted:
            new_rule = dialog.get_configured_rule()
            if new_rule:
                self._apply_rule(new_rule)
    
    def _on_clear_clicked(self):
        """清除按钮点击"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除数据提取规则吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._apply_rule(create_default_rule())
    
    def _apply_rule(self, rule: DataExtractionRule):
        """应用规则"""
        self._rule = rule
        self._update_display()
        self.rule_changed.emit(rule.to_dict())
    
    def get_rule(self) -> Optional[DataExtractionRule]:
        """获取当前规则"""
        return self._rule
    
    def get_rule_dict(self) -> Dict[str, Any]:
        """获取规则字典"""
        if self._rule:
            return self._rule.to_dict()
        return create_default_rule().to_dict()
    
    def set_rule(self, rule_data: Optional[Dict]):
        """设置规则"""
        # 临时断开信号，避免触发不必要的更新
        self.rule_type_combo.blockSignals(True)
        
        if rule_data:
            try:
                self._rule = DataExtractionRule.from_dict(rule_data)
            except Exception as e:
                print(f"[ExtractionRuleWidget] 加载规则失败: {e}")
                self._rule = create_default_rule()
        else:
            self._rule = create_default_rule()
        
        self._update_display()
        
        # 恢复信号
        self.rule_type_combo.blockSignals(False)


# 用于属性面板的控件创建函数
def create_extraction_rule_widget(parent=None, value=None, **kwargs) -> ExtractionRuleWidget:
    """
    创建数据提取规则控件（供属性面板使用）
    
    Args:
        parent: 父控件
        value: 初始值（规则字典）
        **kwargs: 其他参数
        
    Returns:
        ExtractionRuleWidget 实例
    """
    widget = ExtractionRuleWidget(parent, value)
    return widget


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试控件
    widget = ExtractionRuleWidget()
    widget.setWindowTitle("数据提取规则控件测试")
    widget.resize(500, 50)
    widget.show()
    
    # 连接信号测试
    widget.rule_changed.connect(lambda d: print(f"规则改变: {d}"))
    
    sys.exit(app.exec_())
