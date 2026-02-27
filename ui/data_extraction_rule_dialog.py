#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据提取规则配置对话框

提供友好的界面用于配置Modbus TCP数据提取规则：
- 规则类型选择
- 参数配置
- 实时预览
- 预定义模板
- 帮助说明

Author: Vision System Team
Date: 2026-02-05
"""

import json
import sys
import os
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit, QPushButton,
    QGroupBox, QFormLayout, QMessageBox, QTabWidget, QWidget,
    QCheckBox, QRadioButton, QButtonGroup, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QScrollArea, QDialogButtonBox
)

from tools.communication.data_extraction_rules import (
    DataExtractionRule, ExtractionRuleType, DataType, ByteOrder,
    BitExtractRule, RegisterCombineRule, TypeConvertRule,
    ScaleOffsetRule, ConditionalRule,
    get_predefined_rules, create_default_rule
)


class DataExtractionRuleDialog(QDialog):
    """数据提取规则配置对话框"""
    
    rule_configured = pyqtSignal(dict)  # 规则配置完成信号
    
    def __init__(self, parent=None, current_rule: Optional[DataExtractionRule] = None):
        super().__init__(parent)
        self.setWindowTitle("数据提取规则配置")
        self.setMinimumSize(700, 600)
        
        self.current_rule = current_rule or create_default_rule()
        self._init_ui()
        self._load_current_rule()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === 顶部：规则类型选择 ===
        type_group = QGroupBox("规则类型")
        type_layout = QVBoxLayout(type_group)
        
        self.rule_type_combo = QComboBox()
        self.rule_type_combo.setMinimumHeight(30)
        self._populate_rule_types()
        self.rule_type_combo.currentIndexChanged.connect(self._on_rule_type_changed)
        type_layout.addWidget(self.rule_type_combo)
        
        # 规则描述标签
        self.rule_desc_label = QLabel("请选择数据提取规则类型")
        self.rule_desc_label.setWordWrap(True)
        self.rule_desc_label.setStyleSheet("color: gray; padding: 5px;")
        type_layout.addWidget(self.rule_desc_label)
        
        layout.addWidget(type_group)
        
        # === 中部：参数配置区域（使用TabWidget）===
        self.params_tabs = QTabWidget()
        self.params_tabs.setVisible(False)  # 默认隐藏，选择规则类型后显示
        
        # 创建各个规则类型的配置页面
        self._create_none_page()
        self._create_bit_extract_page()
        self._create_register_combine_page()
        self._create_type_convert_page()
        self._create_scale_offset_page()
        self._create_conditional_page()
        
        layout.addWidget(self.params_tabs)
        
        # === 预定义模板 ===
        template_group = QGroupBox("预定义模板")
        template_layout = QHBoxLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("选择模板...", None)
        self._populate_templates()
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_combo)
        
        self.apply_template_btn = QPushButton("应用模板")
        self.apply_template_btn.clicked.connect(self._apply_template)
        template_layout.addWidget(self.apply_template_btn)
        
        layout.addWidget(template_group)
        
        # === 预览区域 ===
        preview_group = QGroupBox("规则预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        # 测试输入
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("测试输入:"))
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("输入测试值（如：250 或 [100, 200]）")
        test_layout.addWidget(self.test_input)
        
        self.test_btn = QPushButton("测试规则")
        self.test_btn.clicked.connect(self._test_rule)
        test_layout.addWidget(self.test_btn)
        
        preview_layout.addLayout(test_layout)
        
        # 测试结果
        self.test_result_label = QLabel("测试结果将显示在这里")
        self.test_result_label.setStyleSheet("color: blue; padding: 5px;")
        preview_layout.addWidget(self.test_result_label)
        
        layout.addWidget(preview_group)
        
        # === 底部按钮 ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Help
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        button_box.helpRequested.connect(self._show_help)
        
        # 添加重置按钮
        self.reset_btn = QPushButton("重置为默认")
        self.reset_btn.clicked.connect(self._reset_to_default)
        button_box.addButton(self.reset_btn, QDialogButtonBox.ResetRole)
        
        layout.addWidget(button_box)
    
    def _populate_rule_types(self):
        """填充规则类型下拉框"""
        rule_types = [
            (ExtractionRuleType.NONE, "无提取规则"),
            (ExtractionRuleType.BIT_EXTRACT, "位提取"),
            (ExtractionRuleType.REGISTER_COMBINE, "多寄存器组合"),
            (ExtractionRuleType.TYPE_CONVERT, "数据类型转换"),
            (ExtractionRuleType.SCALE_OFFSET, "缩放和偏移"),
            (ExtractionRuleType.CONDITIONAL, "条件提取"),
        ]
        
        for rule_type, display_name in rule_types:
            self.rule_type_combo.addItem(display_name, rule_type)
    
    def _populate_templates(self):
        """填充预定义模板"""
        templates = get_predefined_rules()
        for name, rule in templates.items():
            self.template_combo.addItem(name, rule)
    
    def _create_none_page(self):
        """创建"无提取规则"页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        info_label = QLabel("此选项不使用任何数据提取规则，直接使用原始数据。\n\n"
                           "适用于：\n"
                           "• 数据已经是以正确格式接收\n"
                           "• 不需要任何转换或处理\n"
                           "• 原始值就是需要的值")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; padding: 20px;")
        layout.addWidget(info_label)
        layout.addStretch()
        
        self.params_tabs.addTab(page, "无规则")
    
    def _create_bit_extract_page(self):
        """创建"位提取"配置页面"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        # 寄存器索引
        self.bit_reg_index = QSpinBox()
        self.bit_reg_index.setRange(0, 255)
        self.bit_reg_index.setValue(0)
        self.bit_reg_index.setToolTip("要提取的寄存器索引（从0开始）")
        layout.addRow("寄存器索引:", self.bit_reg_index)
        
        # 起始位
        self.bit_start = QSpinBox()
        self.bit_start.setRange(0, 15)
        self.bit_start.setValue(0)
        self.bit_start.setToolTip("起始位位置（0-15）")
        layout.addRow("起始位:", self.bit_start)
        
        # 位数
        self.bit_count = QSpinBox()
        self.bit_count.setRange(1, 16)
        self.bit_count.setValue(1)
        self.bit_count.setToolTip("要提取的位数（1-16）")
        layout.addRow("位数:", self.bit_count)
        
        # 示例说明
        example_label = QLabel("示例：从寄存器值 0xABCD (二进制: 1010101111001101) 中\n"
                              "提取位 4-7 (起始位=4, 位数=4)，结果为 0xC (12)")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 10px;")
        layout.addRow(example_label)
        
        self.params_tabs.addTab(page, "位提取")
    
    def _create_register_combine_page(self):
        """创建"多寄存器组合"配置页面"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        # 寄存器索引列表
        self.combine_reg_indices = QLineEdit()
        self.combine_reg_indices.setText("0,1")
        self.combine_reg_indices.setToolTip("要组合的寄存器索引，用逗号分隔（如：0,1）")
        layout.addRow("寄存器索引:", self.combine_reg_indices)
        
        # 字节序
        self.combine_byte_order = QComboBox()
        self.combine_byte_order.addItem("大端序（Motorola）", ByteOrder.BIG_ENDIAN)
        self.combine_byte_order.addItem("小端序（Intel）", ByteOrder.LITTLE_ENDIAN)
        self.combine_byte_order.setToolTip("选择字节序格式")
        layout.addRow("字节序:", self.combine_byte_order)
        
        # 示例说明
        example_label = QLabel("示例：将两个16位寄存器 [0x1234, 0x5678] 组合成32位整数\n"
                              "大端序结果: 0x12345678\n"
                              "小端序结果: 0x56781234")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 10px;")
        layout.addRow(example_label)
        
        self.params_tabs.addTab(page, "寄存器组合")
    
    def _create_type_convert_page(self):
        """创建"数据类型转换"配置页面"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        # 源数据类型
        self.convert_source_type = QComboBox()
        self._populate_data_types(self.convert_source_type)
        self.convert_source_type.setCurrentIndex(1)  # UINT16
        layout.addRow("源数据类型:", self.convert_source_type)
        
        # 目标数据类型
        self.convert_target_type = QComboBox()
        self._populate_data_types(self.convert_target_type)
        self.convert_target_type.setCurrentIndex(3)  # INT32
        layout.addRow("目标数据类型:", self.convert_target_type)
        
        # 字节序
        self.convert_byte_order = QComboBox()
        self.convert_byte_order.addItem("大端序（Motorola）", ByteOrder.BIG_ENDIAN)
        self.convert_byte_order.addItem("小端序（Intel）", ByteOrder.LITTLE_ENDIAN)
        layout.addRow("字节序:", self.convert_byte_order)
        
        # 示例说明
        example_label = QLabel("示例：将 UINT16 值 0x1234 转换为 INT32\n"
                              "结果: 4660")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 10px;")
        layout.addRow(example_label)
        
        self.params_tabs.addTab(page, "类型转换")
    
    def _create_scale_offset_page(self):
        """创建"缩放和偏移"配置页面"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        # 缩放系数
        self.scale_value = QDoubleSpinBox()
        self.scale_value.setRange(-999999.0, 999999.0)
        self.scale_value.setDecimals(6)
        self.scale_value.setValue(1.0)
        self.scale_value.setToolTip("缩放系数（公式: value = raw * scale + offset）")
        layout.addRow("缩放系数:", self.scale_value)
        
        # 偏移量
        self.offset_value = QDoubleSpinBox()
        self.offset_value.setRange(-999999.0, 999999.0)
        self.offset_value.setDecimals(6)
        self.offset_value.setValue(0.0)
        self.offset_value.setToolTip("偏移量（公式: value = raw * scale + offset）")
        layout.addRow("偏移量:", self.offset_value)
        
        # 小数位数
        self.decimal_places = QSpinBox()
        self.decimal_places.setRange(0, 10)
        self.decimal_places.setValue(2)
        self.decimal_places.setToolTip("结果保留的小数位数")
        layout.addRow("小数位数:", self.decimal_places)
        
        # 公式显示
        self.formula_label = QLabel("公式: value = raw × 1.000000 + 0.000000")
        self.formula_label.setStyleSheet("color: blue; font-weight: bold; padding: 10px; background: #f0f0f0; border-radius: 4px;")
        layout.addRow("转换公式:", self.formula_label)
        
        # 更新公式显示
        self.scale_value.valueChanged.connect(self._update_formula)
        self.offset_value.valueChanged.connect(self._update_formula)
        
        # 示例说明
        example_label = QLabel("示例：温度传感器转换\n"
                              "原始值: 250, 缩放: 0.1, 偏移: -40\n"
                              "结果: 250 × 0.1 - 40 = -15.0°C")
        example_label.setWordWrap(True)
        example_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 10px;")
        layout.addRow(example_label)
        
        self.params_tabs.addTab(page, "缩放偏移")
    
    def _create_conditional_page(self):
        """创建"条件提取"配置页面"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setSpacing(10)
        
        info_label = QLabel("条件提取允许根据数据值选择不同的提取规则。\n"
                           "此功能需要高级配置，建议使用其他规则类型。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: orange; padding: 10px;")
        layout.addRow(info_label)
        
        # 条件字段
        self.cond_field = QLineEdit()
        self.cond_field.setPlaceholderText("输入条件字段名")
        layout.addRow("条件字段:", self.cond_field)
        
        # 条件值
        self.cond_value = QLineEdit()
        self.cond_value.setPlaceholderText("输入条件值")
        layout.addRow("条件值:", self.cond_value)
        
        self.params_tabs.addTab(page, "条件提取")
    
    def _populate_data_types(self, combo: QComboBox):
        """填充数据类型下拉框"""
        data_types = [
            (DataType.INT16, "INT16 - 有符号16位整数"),
            (DataType.UINT16, "UINT16 - 无符号16位整数"),
            (DataType.INT32, "INT32 - 有符号32位整数"),
            (DataType.UINT32, "UINT32 - 无符号32位整数"),
            (DataType.FLOAT32, "FLOAT32 - 32位浮点数"),
            (DataType.FLOAT64, "FLOAT64 - 64位浮点数"),
            (DataType.BOOL, "BOOL - 布尔值"),
            (DataType.STRING, "STRING - 字符串"),
        ]
        
        for data_type, display_name in data_types:
            combo.addItem(display_name, data_type)
    
    def _on_rule_type_changed(self, index: int):
        """规则类型改变时"""
        rule_type = self.rule_type_combo.currentData()
        
        # 更新描述
        if rule_type:
            description = DataExtractionRule.get_rule_type_description(rule_type)
            self.rule_desc_label.setText(description)
        
        # 显示对应的参数页面
        if rule_type == ExtractionRuleType.NONE:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(0)
        elif rule_type == ExtractionRuleType.BIT_EXTRACT:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(1)
        elif rule_type == ExtractionRuleType.REGISTER_COMBINE:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(2)
        elif rule_type == ExtractionRuleType.TYPE_CONVERT:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(3)
        elif rule_type == ExtractionRuleType.SCALE_OFFSET:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(4)
        elif rule_type == ExtractionRuleType.CONDITIONAL:
            self.params_tabs.setVisible(True)
            self.params_tabs.setCurrentIndex(5)
        else:
            self.params_tabs.setVisible(False)
        
        # 更新预览
        self._update_preview()
    
    def _update_formula(self):
        """更新公式显示"""
        scale = self.scale_value.value()
        offset = self.offset_value.value()
        self.formula_label.setText(f"公式: value = raw × {scale:.6f} + {offset:.6f}")
    
    def _update_preview(self):
        """更新规则预览"""
        try:
            rule = self._create_rule_from_ui()
            preview_text = f"规则类型: {rule.rule_type.value}\n"
            preview_text += f"规则名称: {rule.name}\n"
            preview_text += f"配置详情: {json.dumps(rule.to_dict(), indent=2, ensure_ascii=False)}"
            self.preview_text.setText(preview_text)
        except Exception as e:
            self.preview_text.setText(f"预览生成失败: {e}")
    
    def _create_rule_from_ui(self) -> DataExtractionRule:
        """从UI创建规则对象"""
        rule_type = self.rule_type_combo.currentData()
        
        rule = DataExtractionRule(
            rule_type=rule_type,
            name=f"自定义{self.rule_type_combo.currentText()}规则",
            description=f"通过对话框配置的{self.rule_type_combo.currentText()}规则",
            enabled=True
        )
        
        if rule_type == ExtractionRuleType.BIT_EXTRACT:
            rule.bit_extract_rule = BitExtractRule(
                start_bit=self.bit_start.value(),
                bit_count=self.bit_count.value(),
                register_index=self.bit_reg_index.value()
            )
        
        elif rule_type == ExtractionRuleType.REGISTER_COMBINE:
            indices_str = self.combine_reg_indices.text()
            indices = [int(x.strip()) for x in indices_str.split(",") if x.strip()]
            rule.register_combine_rule = RegisterCombineRule(
                register_indices=indices,
                byte_order=self.combine_byte_order.currentData()
            )
        
        elif rule_type == ExtractionRuleType.TYPE_CONVERT:
            rule.type_convert_rule = TypeConvertRule(
                source_type=self.convert_source_type.currentData(),
                target_type=self.convert_target_type.currentData(),
                byte_order=self.convert_byte_order.currentData()
            )
        
        elif rule_type == ExtractionRuleType.SCALE_OFFSET:
            rule.scale_offset_rule = ScaleOffsetRule(
                scale=self.scale_value.value(),
                offset=self.offset_value.value(),
                decimal_places=self.decimal_places.value()
            )
        
        return rule
    
    def _on_template_selected(self, index: int):
        """模板选择改变时"""
        # 不自动应用，等待用户点击应用按钮
        pass
    
    def _apply_template(self):
        """应用选中的模板"""
        rule = self.template_combo.currentData()
        if rule:
            self.current_rule = rule
            self._load_current_rule()
            QMessageBox.information(self, "成功", f"已应用模板: {self.template_combo.currentText()}")
        else:
            QMessageBox.warning(self, "提示", "请先选择一个模板")
    
    def _test_rule(self):
        """测试规则"""
        try:
            rule = self._create_rule_from_ui()
            input_text = self.test_input.text().strip()
            
            if not input_text:
                self.test_result_label.setText("请输入测试值")
                self.test_result_label.setStyleSheet("color: orange;")
                return
            
            # 解析输入
            try:
                if input_text.startswith("["):
                    # 列表格式 [1, 2, 3]
                    test_data = eval(input_text)
                elif "," in input_text:
                    # 逗号分隔 1, 2, 3
                    test_data = [int(x.strip()) for x in input_text.split(",")]
                else:
                    # 单个值
                    test_data = int(input_text)
            except Exception:
                test_data = input_text
            
            # 应用规则
            result = rule.extract(test_data)
            
            self.test_result_label.setText(f"✓ 测试结果: {result}")
            self.test_result_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            self.test_result_label.setText(f"✗ 测试失败: {e}")
            self.test_result_label.setStyleSheet("color: red;")
    
    def _load_current_rule(self):
        """加载当前规则到UI"""
        if not self.current_rule:
            return
        
        # 设置规则类型
        index = self.rule_type_combo.findData(self.current_rule.rule_type)
        if index >= 0:
            self.rule_type_combo.setCurrentIndex(index)
        
        # 加载具体规则参数
        if self.current_rule.bit_extract_rule:
            self.bit_start.setValue(self.current_rule.bit_extract_rule.start_bit)
            self.bit_count.setValue(self.current_rule.bit_extract_rule.bit_count)
            self.bit_reg_index.setValue(self.current_rule.bit_extract_rule.register_index)
        
        if self.current_rule.register_combine_rule:
            indices_str = ",".join(map(str, self.current_rule.register_combine_rule.register_indices))
            self.combine_reg_indices.setText(indices_str)
            
            byte_order_index = self.combine_byte_order.findData(
                self.current_rule.register_combine_rule.byte_order
            )
            if byte_order_index >= 0:
                self.combine_byte_order.setCurrentIndex(byte_order_index)
        
        if self.current_rule.type_convert_rule:
            source_index = self.convert_source_type.findData(
                self.current_rule.type_convert_rule.source_type
            )
            if source_index >= 0:
                self.convert_source_type.setCurrentIndex(source_index)
            
            target_index = self.convert_target_type.findData(
                self.current_rule.type_convert_rule.target_type
            )
            if target_index >= 0:
                self.convert_target_type.setCurrentIndex(target_index)
            
            byte_order_index = self.convert_byte_order.findData(
                self.current_rule.type_convert_rule.byte_order
            )
            if byte_order_index >= 0:
                self.convert_byte_order.setCurrentIndex(byte_order_index)
        
        if self.current_rule.scale_offset_rule:
            self.scale_value.setValue(self.current_rule.scale_offset_rule.scale)
            self.offset_value.setValue(self.current_rule.scale_offset_rule.offset)
            self.decimal_places.setValue(self.current_rule.scale_offset_rule.decimal_places)
            self._update_formula()
        
        # 更新预览
        self._update_preview()
    
    def _on_ok(self):
        """确定按钮"""
        try:
            rule = self._create_rule_from_ui()
            self.rule_configured.emit(rule.to_dict())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"配置规则失败: {e}")
    
    def _reset_to_default(self):
        """重置为默认规则"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置为默认规则吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_rule = create_default_rule()
            self._load_current_rule()
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
<h2>数据提取规则配置帮助</h2>

<h3>规则类型说明</h3>

<p><b>1. 无提取规则（默认）</b></p>
<ul>
<li>直接使用原始数据，不进行任何转换</li>
<li>适用于数据已经是正确格式的情况</li>
</ul>

<p><b>2. 位提取</b></p>
<ul>
<li>从寄存器值中提取特定的位</li>
<li>参数：寄存器索引、起始位（0-15）、位数（1-16）</li>
<li>示例：从 0xABCD 中提取位 4-7，结果为 0xC</li>
</ul>

<p><b>3. 多寄存器组合</b></p>
<ul>
<li>将多个16位寄存器组合成一个32位值</li>
<li>参数：寄存器索引列表、字节序</li>
<li>示例：[0x1234, 0x5678] → 0x12345678（大端序）</li>
</ul>

<p><b>4. 数据类型转换</b></p>
<ul>
<li>转换数据类型（INT16/INT32/FLOAT等）</li>
<li>参数：源类型、目标类型、字节序</li>
<li>示例：将 UINT16 转换为 FLOAT32</li>
</ul>

<p><b>5. 缩放和偏移</b></p>
<ul>
<li>线性变换：value = raw × scale + offset</li>
<li>参数：缩放系数、偏移量、小数位数</li>
<li>示例：温度传感器 250 × 0.1 - 40 = -15.0°C</li>
</ul>

<p><b>6. 条件提取</b></p>
<ul>
<li>根据条件选择不同的提取规则</li>
<li>适用于复杂的数据处理场景</li>
</ul>

<h3>使用建议</h3>
<ul>
<li>不确定时选择"无提取规则"</li>
<li>常用场景可使用"预定义模板"</li>
<li>配置后使用"测试"功能验证</li>
<li>注意字节序的选择（PLC通常使用大端序）</li>
</ul>
        """
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("数据提取规则配置帮助")
        help_dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(help_dialog)
        
        text_edit = QTextEdit()
        text_edit.setHtml(help_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        btn = QPushButton("关闭")
        btn.clicked.connect(help_dialog.accept)
        layout.addWidget(btn)
        
        help_dialog.exec_()
    
    def get_configured_rule(self) -> Optional[DataExtractionRule]:
        """获取配置好的规则"""
        if self.result() == QDialog.Accepted:
            return self._create_rule_from_ui()
        return None


# 便捷函数
def configure_extraction_rule(parent=None, current_rule: Optional[DataExtractionRule] = None) -> Optional[DataExtractionRule]:
    """
    打开数据提取规则配置对话框
    
    Args:
        parent: 父窗口
        current_rule: 当前规则（用于编辑）
        
    Returns:
        配置好的规则，如果取消则返回None
    """
    dialog = DataExtractionRuleDialog(parent, current_rule)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_configured_rule()
    return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 测试对话框
    dialog = DataExtractionRuleDialog()
    if dialog.exec_() == QDialog.Accepted:
        rule = dialog.get_configured_rule()
        if rule:
            print("配置的规则:")
            print(json.dumps(rule.to_dict(), indent=2, ensure_ascii=False))
    
    sys.exit(app.exec_())
