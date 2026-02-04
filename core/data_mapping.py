# -*- coding: utf-8 -*-
"""
DataMapper module for converting upstream tool output data into sendable format.

This module provides data mapping functionality to decouple communication management
from data sending/receiving tools.

Author: AI Agent
Date: 2026-02-04
"""

import json
import sys
import os
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_management import log_error


@dataclass
class DataMappingRule:
    """数据映射规则
    
    定义从源字段到目标字段的映射关系，支持转换函数和默认值。
    
    Attributes:
        source_field: 源数据字段名，支持嵌套路径（如"position.x"）
        target_field: 目标数据字段名
        transform_func: 可选的转换函数，用于转换字段值
        default_value: 当源字段不存在时的默认值
    """
    source_field: str
    target_field: str
    transform_func: Optional[Callable[[Any], Any]] = None
    default_value: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典（用于序列化）"""
        return {
            "source_field": self.source_field,
            "target_field": self.target_field,
            "default_value": self.default_value,
            # transform_func 不能被序列化，所以不包含在字典中
            "has_transform": self.transform_func is not None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataMappingRule":
        """从字典创建规则（用于反序列化）"""
        return cls(
            source_field=data["source_field"],
            target_field=data["target_field"],
            default_value=data.get("default_value"),
            transform_func=None  # 转换函数需要在反序列化后手动设置
        )


class DataMapper:
    """数据映射器
    
    管理多个数据映射规则，将上游工具的输出数据转换为发送所需的格式。
    
    Example:
        >>> mapper = DataMapper()
        >>> mapper.add_rule(DataMappingRule(
        ...     source_field="result",
        ...     target_field="status",
        ...     transform_func=lambda x: "OK" if x else "NG"
        ... ))
        >>> output = mapper.map({"result": True})
        >>> print(output)  # {"status": "OK"}
    """
    
    def __init__(self):
        """初始化数据映射器"""
        self._rules: List[DataMappingRule] = []
    
    def add_rule(self, rule: DataMappingRule) -> None:
        """添加映射规则
        
        Args:
            rule: 要添加的数据映射规则
        """
        self._rules.append(rule)
    
    def remove_rule(self, rule: DataMappingRule) -> None:
        """删除映射规则
        
        Args:
            rule: 要删除的数据映射规则
        """
        if rule in self._rules:
            self._rules.remove(rule)
    
    def clear_rules(self) -> None:
        """清除所有映射规则"""
        self._rules.clear()
    
    def get_rules(self) -> List[DataMappingRule]:
        """获取所有映射规则
        
        Returns:
            当前所有映射规则的列表
        """
        return self._rules.copy()
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字段值
        
        支持点号分隔的路径，如"position.x"会从{"position": {"x": 100}}中获取100
        
        Args:
            data: 输入数据字典
            path: 字段路径，支持点号分隔的嵌套路径
            
        Returns:
            字段值，如果路径不存在则返回None
        """
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def map(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据映射
        
        根据配置的规则将输入数据转换为输出数据。
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            映射后的输出数据字典
        """
        output_data: Dict[str, Any] = {}
        
        for rule in self._rules:
            # 获取源字段值（支持嵌套路径）
            value = self._get_nested_value(input_data, rule.source_field)
            
            # 如果字段不存在，使用默认值
            if value is None:
                value = rule.default_value
            
            # 应用转换函数
            if rule.transform_func is not None and value is not None:
                try:
                    value = rule.transform_func(value)
                except Exception as e:
                    # 转换失败时记录错误并使用默认值
                    log_error(
                        1001,
                        f"Transform failed for field '{rule.source_field}': {str(e)}"
                    )
                    value = rule.default_value
            
            # 设置目标字段
            if value is not None:
                output_data[rule.target_field] = value
        
        return output_data
    
    def to_json(self) -> Dict[str, Any]:
        """将映射器配置序列化为JSON字典
        
        Returns:
            包含所有规则的字典，可用于JSON序列化
        """
        return {
            "rules": [rule.to_dict() for rule in self._rules]
        }
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "DataMapper":
        """从JSON字典反序列化映射器配置
        
        Args:
            data: 包含规则配置的JSON字典
            
        Returns:
            配置好的DataMapper实例
        """
        mapper = cls()
        
        for rule_dict in data.get("rules", []):
            rule = DataMappingRule.from_dict(rule_dict)
            mapper.add_rule(rule)
        
        return mapper
    
    def __repr__(self) -> str:
        """返回映射器的字符串表示"""
        return f"DataMapper(rules={len(self._rules)})"
