# -*- coding: utf-8 -*-
"""
DataMapper tests for data mapping functionality

Author: AI Agent
Date: 2026-02-04
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_mapping import DataMapper, DataMappingRule


def test_data_mapper_creation():
    """测试数据映射器创建"""
    mapper = DataMapper()
    assert mapper is not None


def test_simple_mapping():
    """测试简单字段映射"""
    mapper = DataMapper()
    
    # 添加映射规则：将输入的"result"字段映射到输出的"status"
    mapper.add_rule(DataMappingRule(
        source_field="result",
        target_field="status",
        transform_func=lambda x: "OK" if x else "NG"
    ))
    
    # 测试映射
    input_data = {"result": True, "other": "ignore"}
    output = mapper.map(input_data)
    
    assert output["status"] == "OK"
    assert "other" not in output  # 未映射的字段被忽略


def test_nested_mapping():
    """测试嵌套字段映射"""
    mapper = DataMapper()
    
    # 嵌套字段映射：input.position.x -> output.x
    mapper.add_rule(DataMappingRule(
        source_field="position.x",
        target_field="x",
        transform_func=float
    ))
    
    input_data = {"position": {"x": 100, "y": 200}}
    output = mapper.map(input_data)
    
    assert output["x"] == 100.0


def test_default_value():
    """测试默认值"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="missing_field",
        target_field="output",
        default_value="default"
    ))
    
    input_data = {}
    output = mapper.map(input_data)
    
    assert output["output"] == "default"


def test_multiple_rules():
    """测试多个映射规则"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="a",
        target_field="x"
    ))
    mapper.add_rule(DataMappingRule(
        source_field="b",
        target_field="y"
    ))
    
    input_data = {"a": 1, "b": 2}
    output = mapper.map(input_data)
    
    assert output["x"] == 1
    assert output["y"] == 2


def test_transform_with_numpy():
    """测试使用numpy的转换函数"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="values",
        target_field="sum",
        transform_func=lambda x: float(np.sum(x))
    ))
    
    input_data = {"values": np.array([1, 2, 3, 4, 5])}
    output = mapper.map(input_data)
    
    assert output["sum"] == 15.0


def test_serialization():
    """测试序列化和反序列化"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="input",
        target_field="output",
        default_value="default"
    ))
    
    # 序列化
    json_data = mapper.to_json()
    assert json_data is not None
    assert "rules" in json_data
    
    # 反序列化
    new_mapper = DataMapper.from_json(json_data)
    assert new_mapper is not None
    
    # 测试反序列化后的功能
    input_data = {}
    output = new_mapper.map(input_data)
    assert output["output"] == "default"


def test_remove_rule():
    """测试删除规则"""
    mapper = DataMapper()
    
    rule = DataMappingRule(source_field="a", target_field="x")
    mapper.add_rule(rule)
    
    input_data = {"a": 1}
    output = mapper.map(input_data)
    assert output["x"] == 1
    
    # 删除规则
    mapper.remove_rule(rule)
    output = mapper.map(input_data)
    assert "x" not in output


def test_deep_nested_mapping():
    """测试深层嵌套字段映射"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="a.b.c.d",
        target_field="result"
    ))
    
    input_data = {"a": {"b": {"c": {"d": "deep_value"}}}}
    output = mapper.map(input_data)
    
    assert output["result"] == "deep_value"


def test_identity_mapping():
    """测试恒等映射（无转换函数）"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="value",
        target_field="value"
    ))
    
    input_data = {"value": 42}
    output = mapper.map(input_data)
    
    assert output["value"] == 42


def test_transform_func_exception():
    """测试转换函数异常处理"""
    mapper = DataMapper()
    
    def failing_transform(x):
        raise ValueError("Transform error")
    
    mapper.add_rule(DataMappingRule(
        source_field="input",
        target_field="output",
        transform_func=failing_transform,
        default_value="fallback"
    ))
    
    input_data = {"input": "some_value"}
    output = mapper.map(input_data)
    
    # 转换失败时应使用默认值
    assert output["output"] == "fallback"


def test_invalid_nested_path():
    """测试无效嵌套路径（通过非字典值访问）"""
    mapper = DataMapper()
    
    mapper.add_rule(DataMappingRule(
        source_field="value.nested",
        target_field="output",
        default_value="default"
    ))
    
    # value是字符串而非字典，无法访问nested字段
    input_data = {"value": "not_a_dict"}
    output = mapper.map(input_data)
    
    # 应该返回默认值
    assert output["output"] == "default"
