"""
参数序列化器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from enum import Enum
from typing import Dict, Any, Optional

from core.parameter_serializer import (
    ParameterSerializer, Serializable, 
    serialize, deserialize, to_json, from_json
)


# 测试用的枚举
class TestEnum(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"
    VALUE3 = 3


# 测试用的可序列化类
class TestSerializable(Serializable):
    def __init__(self, name: str = "", value: int = 0, nested: Optional['TestSerializable'] = None):
        self.name = name
        self.value = value
        self.nested = nested
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "nested": self.nested.to_dict() if self.nested else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSerializable':
        nested = None
        if data.get("nested"):
            nested = cls.from_dict(data["nested"])
        return cls(
            name=data.get("name", ""),
            value=data.get("value", 0),
            nested=nested
        )
    
    def __eq__(self, other):
        if not isinstance(other, TestSerializable):
            return False
        return (self.name == other.name and 
                self.value == other.value and
                ((self.nested is None and other.nested is None) or
                 (self.nested is not None and other.nested is not None and 
                  self.nested == other.nested)))


class TestParameterSerializer(unittest.TestCase):
    """参数序列化器测试类"""
    
    def test_basic_types(self):
        """测试基本类型序列化"""
        # 整数
        self.assertEqual(ParameterSerializer.serialize(42), 42)
        # 浮点数
        self.assertEqual(ParameterSerializer.serialize(3.14), 3.14)
        # 字符串
        self.assertEqual(ParameterSerializer.serialize("hello"), "hello")
        # 布尔值
        self.assertEqual(ParameterSerializer.serialize(True), True)
        self.assertEqual(ParameterSerializer.serialize(False), False)
        # None
        self.assertIsNone(ParameterSerializer.serialize(None))
    
    def test_container_types(self):
        """测试容器类型序列化"""
        # 列表
        data = [1, 2, 3, "hello", True]
        serialized = ParameterSerializer.serialize(data)
        self.assertEqual(serialized, data)
        
        # 元组（序列化为列表）
        data = (1, 2, 3)
        serialized = ParameterSerializer.serialize(data)
        self.assertEqual(serialized, [1, 2, 3])
        
        # 字典
        data = {"a": 1, "b": "hello", "c": True}
        serialized = ParameterSerializer.serialize(data)
        self.assertEqual(serialized, data)
        
        # 嵌套容器
        data = {"list": [1, 2, 3], "dict": {"a": 1}}
        serialized = ParameterSerializer.serialize(data)
        self.assertEqual(serialized, data)
    
    def test_enum_serialization(self):
        """测试枚举类型序列化"""
        enum_val = TestEnum.VALUE1
        serialized = ParameterSerializer.serialize(enum_val)
        
        # 验证格式
        self.assertEqual(serialized["__type__"], "enum")
        self.assertIn("__class__", serialized)
        self.assertEqual(serialized["value"], "value1")
        
        # 验证反序列化
        deserialized = ParameterSerializer.deserialize(serialized)
        self.assertEqual(deserialized, TestEnum.VALUE1)
    
    def test_serializable_object(self):
        """测试可序列化对象"""
        obj = TestSerializable(name="test", value=42)
        serialized = ParameterSerializer.serialize(obj)
        
        # 验证格式
        self.assertEqual(serialized["__type__"], "object")
        self.assertIn("__class__", serialized)
        self.assertEqual(serialized["data"]["name"], "test")
        self.assertEqual(serialized["data"]["value"], 42)
        
        # 验证反序列化
        deserialized = ParameterSerializer.deserialize(serialized)
        self.assertEqual(deserialized, obj)
    
    def test_nested_serializable(self):
        """测试嵌套可序列化对象"""
        inner = TestSerializable(name="inner", value=10)
        outer = TestSerializable(name="outer", value=20, nested=inner)
        
        serialized = ParameterSerializer.serialize(outer)
        deserialized = ParameterSerializer.deserialize(serialized)
        
        self.assertEqual(deserialized, outer)
        self.assertEqual(deserialized.nested, inner)
    
    def test_mixed_types(self):
        """测试混合类型"""
        data = {
            "enum": TestEnum.VALUE2,
            "object": TestSerializable("test", 42),
            "list": [1, 2, TestEnum.VALUE3],
            "dict": {"nested": TestSerializable("nested", 100)}
        }
        
        serialized = ParameterSerializer.serialize(data)
        deserialized = ParameterSerializer.deserialize(serialized)
        
        self.assertEqual(deserialized["enum"], TestEnum.VALUE2)
        self.assertEqual(deserialized["object"], TestSerializable("test", 42))
        self.assertEqual(deserialized["list"][:2], [1, 2])
        self.assertEqual(deserialized["list"][2], TestEnum.VALUE3)
        self.assertEqual(deserialized["dict"]["nested"], TestSerializable("nested", 100))
    
    def test_json_conversion(self):
        """测试JSON转换"""
        data = {
            "name": "test",
            "enum": TestEnum.VALUE1,
            "object": TestSerializable("obj", 123)
        }
        
        # 转换为JSON
        json_str = to_json(data, indent=2)
        self.assertIsInstance(json_str, str)
        
        # 从JSON还原
        restored = from_json(json_str)
        self.assertEqual(restored["name"], "test")
        self.assertEqual(restored["enum"], TestEnum.VALUE1)
        self.assertEqual(restored["object"], TestSerializable("obj", 123))
    
    def test_validation(self):
        """测试数据验证"""
        # 有效数据
        valid_data = {"a": 1, "b": TestEnum.VALUE1}
        self.assertTrue(ParameterSerializer.validate(valid_data))
        
        # 空数据
        self.assertTrue(ParameterSerializer.validate({}))
        
        # None
        self.assertTrue(ParameterSerializer.validate(None))
    
    def test_numpy_array(self):
        """测试numpy数组序列化（如果可用）"""
        try:
            import numpy as np
            
            arr = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
            serialized = ParameterSerializer.serialize(arr)
            
            # 验证格式
            self.assertEqual(serialized["__type__"], "numpy")
            self.assertEqual(list(serialized["shape"]), [2, 3])
            self.assertEqual(serialized["dtype"], "float32")
            
            # 验证反序列化
            deserialized = ParameterSerializer.deserialize(serialized)
            self.assertTrue(np.array_equal(deserialized, arr))
        except ImportError:
            self.skipTest("numpy not available")
    
    def test_unsupported_type(self):
        """测试不支持的类型"""
        # 定义一个不支持的类型
        class UnsupportedType:
            def __str__(self):
                return "unsupported"
        
        obj = UnsupportedType()
        serialized = ParameterSerializer.serialize(obj)
        
        # 应该返回unsupported标记
        self.assertEqual(serialized["__type__"], "unsupported")
        self.assertEqual(serialized["value"], "unsupported")
    
    def test_recursion_depth(self):
        """测试递归深度限制"""
        # 创建深度嵌套的数据
        data = {}
        current = data
        for i in range(150):  # 超过MAX_RECURSION_DEPTH
            current["nested"] = {"value": i}
            current = current["nested"]
        
        # 应该抛出RecursionError
        with self.assertRaises(RecursionError):
            ParameterSerializer.serialize(data)
    
    def test_custom_type_registration(self):
        """测试自定义类型注册"""
        class CustomType:
            def __init__(self, value: str):
                self.value = value
        
        # 注册自定义类型
        ParameterSerializer.register_type(
            CustomType,
            serializer=lambda x: {"value": x.value},
            deserializer=lambda d: CustomType(d["value"])
        )
        
        obj = CustomType("test_value")
        serialized = ParameterSerializer.serialize(obj)
        
        # 验证格式
        self.assertEqual(serialized["__type__"], "custom")
        self.assertEqual(serialized["data"]["value"], "test_value")
        
        # 验证反序列化
        deserialized = ParameterSerializer.deserialize(serialized)
        self.assertIsInstance(deserialized, CustomType)
        self.assertEqual(deserialized.value, "test_value")


class TestConvenienceFunctions(unittest.TestCase):
    """便捷函数测试"""
    
    def test_serialize_deserialize(self):
        """测试便捷序列化/反序列化函数"""
        data = {"enum": TestEnum.VALUE1, "value": 42}
        
        serialized = serialize(data)
        self.assertIsInstance(serialized, dict)
        
        deserialized = deserialize(serialized)
        self.assertEqual(deserialized["enum"], TestEnum.VALUE1)
        self.assertEqual(deserialized["value"], 42)
    
    def test_to_json_from_json(self):
        """测试便捷JSON转换函数"""
        data = {"name": "test", "enum": TestEnum.VALUE2}
        
        json_str = to_json(data)
        self.assertIsInstance(json_str, str)
        
        restored = from_json(json_str)
        self.assertEqual(restored["name"], "test")
        self.assertEqual(restored["enum"], TestEnum.VALUE2)


if __name__ == "__main__":
    unittest.main()
