#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据映射编辑器

Author: AI Agent
Date: 2026-02-04
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.data_mapping_editor import DataMappingEditor, DataMappingSimpleEditor, edit_mapping


def test_data_mapping_editor_creation():
    """测试编辑器创建"""
    editor = DataMappingEditor()
    assert editor is not None
    assert editor.windowTitle() == "数据映射配置"


def test_simple_editor_creation():
    """测试简化版编辑器创建"""
    editor = DataMappingSimpleEditor()
    assert editor is not None
    assert editor.windowTitle() == "数据映射"


def test_add_mapping_row():
    """测试添加映射行"""
    editor = DataMappingSimpleEditor()

    # 添加一行
    editor.add_mapping_row("source_field", "target_field")

    assert editor.table.rowCount() == 1


def test_delete_mapping_row():
    """测试删除映射行"""
    editor = DataMappingSimpleEditor()

    # 添加两行
    editor.add_mapping_row("source1", "target1")
    editor.add_mapping_row("source2", "target2")

    assert editor.table.rowCount() == 2

    # 删除第一行
    editor.delete_row(0)

    assert editor.table.rowCount() == 1


def test_get_mapping_json_empty():
    """测试获取空映射"""
    editor = DataMappingSimpleEditor()
    mapping_json = editor.get_mapping_json()

    assert mapping_json == "{}"


def test_get_mapping_json_with_data():
    """测试获取有数据的映射"""
    editor = DataMappingSimpleEditor()

    editor.add_mapping_row("result.status", "status")
    editor.add_mapping_row("position.x", "x_coord")
    editor.add_mapping_row("position.y", "y_coord")

    mapping_json = editor.get_mapping_json()
    assert "result.status" in mapping_json
    assert "position.x" in mapping_json


def test_load_mapping():
    """测试加载映射配置"""
    existing_mapping = '{"result": "status", "value": "data_value"}'

    editor = DataMappingSimpleEditor(current_mapping=existing_mapping)

    assert editor.table.rowCount() == 2


def test_import_mapping():
    """测试导入映射功能"""
    editor = DataMappingSimpleEditor()

    # 由于无法实际打开文件对话框，这个测试只验证函数存在
    assert hasattr(editor, 'import_mapping')
    assert callable(editor.import_mapping)


def test_export_mapping():
    """测试导出映射功能"""
    editor = DataMappingSimpleEditor()

    # 添加一些数据
    editor.add_mapping_row("test", "value")

    # 由于无法实际保存文件，这个测试只验证函数存在
    assert hasattr(editor, 'export_mapping')
    assert callable(editor.export_mapping)


def test_edit_mapping_function():
    """测试便捷编辑函数"""
    # 测试edit_mapping函数存在且可调用
    assert callable(edit_mapping)


def test_complex_editor_creation():
    """测试完整版编辑器创建"""
    editor = DataMappingEditor()
    assert editor is not None

    # 验证表格有正确的列数
    assert editor.table.columnCount() == 4

    # 验证有预览编辑框
    assert hasattr(editor, 'preview_edit')


def test_complex_editor_with_mapping():
    """测试完整版编辑器加载映射"""
    mapping = '{"result.status": "status", "position.x": "x"}'

    editor = DataMappingEditor(current_mapping=mapping)

    # 应该有两行
    assert editor.table.rowCount() == 2


def test_full_editor_get_mapping():
    """测试完整版编辑器获取映射"""
    editor = DataMappingEditor()

    editor.add_mapping_row("field1", "field2", "to_int")

    mapping_json = editor.get_mapping_json()
    assert "field1" in mapping_json
    assert "field2" in mapping_json


def test_full_editor_transform():
    """测试完整版编辑器转换函数"""
    editor = DataMappingEditor()

    # 添加带有转换函数的行
    editor.add_mapping_row("count", "value", "to_int")

    # 验证转换函数被设置
    transform_widget = editor.table.cellWidget(0, 2)
    assert transform_widget.currentText() == "to_int"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
