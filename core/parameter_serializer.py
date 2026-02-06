"""
参数序列化工具类
提供统一的参数序列化和反序列化功能
"""

import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Callable, Union, Tuple
import logging

logger = logging.getLogger(__name__)


class Serializable(ABC):
    """可序列化接口基类"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """将对象序列化为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """从字典反序列化为对象"""
        pass
    
    def get_serializable_fields(self) -> List[str]:
        """获取可序列化字段列表（可选实现）"""
        return []


class ParameterSerializer:
    """参数序列化器
    
    提供统一的参数序列化和反序列化功能，支持：
    - 基本类型（int, float, str, bool, None）
    - 容器类型（list, dict, tuple）
    - 枚举类型（Enum）
    - 可序列化对象（Serializable）
    - 循环引用检测
    """
    
    # 自定义类型注册表
    _type_registry: Dict[str, Tuple[Type, Callable, Callable]] = {}
    
    # 最大递归深度
    MAX_RECURSION_DEPTH = 100
    
    @classmethod
    def serialize(cls, value: Any, _depth: int = 0, _visited: Optional[set] = None) -> Any:
        """将参数值序列化为JSON兼容格式
        
        Args:
            value: 要序列化的值
            _depth: 当前递归深度（内部使用）
            _visited: 已访问对象集合（用于循环引用检测）
            
        Returns:
            JSON兼容的序列化值
            
        Raises:
            RecursionError: 超过最大递归深度
            ValueError: 无法序列化的类型
        """
        if _visited is None:
            _visited = set()
        
        # 检查递归深度
        if _depth > cls.MAX_RECURSION_DEPTH:
            raise RecursionError(f"序列化递归深度超过最大值 {cls.MAX_RECURSION_DEPTH}")
        
        # 处理None
        if value is None:
            return None
        
        # 处理基本类型
        if isinstance(value, (int, float, str, bool)):
            return value
        
        # 处理枚举类型
        if isinstance(value, Enum):
            return {
                "__type__": "enum",
                "__class__": f"{value.__class__.__module__}.{value.__class__.__name__}",
                "value": value.value
            }
        
        # 处理可序列化对象
        if isinstance(value, Serializable):
            obj_id = id(value)
            if obj_id in _visited:
                # 循环引用，返回引用标记
                return {"__type__": "ref", "id": obj_id}
            _visited.add(obj_id)
            
            result = {
                "__type__": "object",
                "__class__": f"{value.__class__.__module__}.{value.__class__.__name__}",
                "data": value.to_dict()
            }
            _visited.remove(obj_id)
            return result
        
        # 处理列表和元组
        if isinstance(value, (list, tuple)):
            return [cls.serialize(item, _depth + 1, _visited) for item in value]
        
        # 处理字典
        if isinstance(value, dict):
            return {
                key: cls.serialize(val, _depth + 1, _visited)
                for key, val in value.items()
            }
        
        # 处理numpy数组（如果可用）
        try:
            import numpy as np
            if isinstance(value, np.ndarray):
                return {
                    "__type__": "numpy",
                    "shape": value.shape,
                    "dtype": str(value.dtype),
                    "data": value.tobytes().hex()
                }
        except ImportError:
            pass
        
        # 处理自定义注册类型
        type_name = f"{value.__class__.__module__}.{value.__class__.__name__}"
        if type_name in cls._type_registry:
            _, serializer, _ = cls._type_registry[type_name]
            return {
                "__type__": "custom",
                "__class__": type_name,
                "data": serializer(value)
            }
        
        # 不支持的类型
        logger.warning(f"不支持的序列化类型: {type(value)}, 将使用str()转换")
        return {"__type__": "unsupported", "value": str(value)}
    
    @classmethod
    def deserialize(cls, value: Any, context: Optional[Dict] = None, 
                    _depth: int = 0) -> Any:
        """从序列化格式还原参数值
        
        Args:
            value: 序列化的值
            context: 上下文信息（用于还原复杂对象）
            _depth: 当前递归深度（内部使用）
            
        Returns:
            还原后的值
            
        Raises:
            RecursionError: 超过最大递归深度
            ValueError: 无法反序列化的类型
        """
        if context is None:
            context = {}
        
        # 检查递归深度
        if _depth > cls.MAX_RECURSION_DEPTH:
            raise RecursionError(f"反序列化递归深度超过最大值 {cls.MAX_RECURSION_DEPTH}")
        
        # 处理None
        if value is None:
            return None
        
        # 处理基本类型
        if isinstance(value, (int, float, str, bool)):
            return value
        
        # 处理列表
        if isinstance(value, list):
            return [cls.deserialize(item, context, _depth + 1) for item in value]
        
        # 处理字典（检查特殊类型标记）
        if isinstance(value, dict):
            type_mark = value.get("__type__")
            
            if type_mark == "enum":
                # 还原枚举
                return cls._restore_enum(value)
            
            elif type_mark == "object":
                # 还原可序列化对象
                return cls._restore_object(value, context)
            
            elif type_mark == "ref":
                # 循环引用，返回None（需要后续处理）
                logger.warning("检测到循环引用，可能丢失数据")
                return None
            
            elif type_mark == "numpy":
                # 还原numpy数组
                return cls._restore_numpy(value)
            
            elif type_mark == "custom":
                # 还原自定义类型
                return cls._restore_custom(value)
            
            elif type_mark == "unsupported":
                # 不支持的类型，返回字符串值
                return value.get("value", "")
            
            else:
                # 普通字典
                return {
                    key: cls.deserialize(val, context, _depth + 1)
                    for key, val in value.items()
                }
        
        # 未知类型
        logger.warning(f"未知的反序列化类型: {type(value)}")
        return value
    
    @classmethod
    def _restore_enum(cls, data: Dict) -> Any:
        """还原枚举类型"""
        try:
            class_path = data["__class__"]
            value = data["value"]
            
            # 动态导入枚举类
            module_name, class_name = class_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            enum_class = getattr(module, class_name)
            
            # 创建枚举实例
            return enum_class(value)
        except Exception as e:
            logger.error(f"还原枚举失败: {e}")
            return value
    
    @classmethod
    def _restore_object(cls, data: Dict, context: Dict) -> Any:
        """还原可序列化对象"""
        try:
            class_path = data["__class__"]
            obj_data = data["data"]
            
            # 动态导入类
            module_name, class_name = class_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            obj_class = getattr(module, class_name)
            
            # 检查是否有from_dict方法
            if hasattr(obj_class, 'from_dict'):
                return obj_class.from_dict(obj_data)
            else:
                # 尝试直接实例化
                return obj_class(**obj_data)
        except Exception as e:
            logger.error(f"还原对象失败: {e}")
            return data
    
    @classmethod
    def _restore_numpy(cls, data: Dict) -> Any:
        """还原numpy数组"""
        try:
            import numpy as np
            shape = tuple(data["shape"])
            dtype = data["dtype"]
            hex_data = data["data"]
            
            # 从hex字符串还原字节
            bytes_data = bytes.fromhex(hex_data)
            
            # 创建数组
            return np.frombuffer(bytes_data, dtype=dtype).reshape(shape)
        except Exception as e:
            logger.error(f"还原numpy数组失败: {e}")
            return None
    
    @classmethod
    def _restore_custom(cls, data: Dict) -> Any:
        """还原自定义类型"""
        try:
            class_path = data["__class__"]
            custom_data = data["data"]
            
            if class_path in cls._type_registry:
                _, _, deserializer = cls._type_registry[class_path]
                return deserializer(custom_data)
            else:
                logger.warning(f"未注册的自定义类型: {class_path}")
                return custom_data
        except Exception as e:
            logger.error(f"还原自定义类型失败: {e}")
            return data
    
    @classmethod
    def register_type(cls, type_class: Type, 
                      serializer: Callable[[Any], Any],
                      deserializer: Callable[[Any], Any]):
        """注册自定义类型序列化器
        
        Args:
            type_class: 要注册的类型
            serializer: 序列化函数
            deserializer: 反序列化函数
        """
        type_name = f"{type_class.__module__}.{type_class.__name__}"
        cls._type_registry[type_name] = (type_class, serializer, deserializer)
        logger.info(f"注册自定义类型: {type_name}")
    
    @classmethod
    def validate(cls, data: Dict) -> bool:
        """验证序列化数据完整性
        
        Args:
            data: 序列化数据
            
        Returns:
            数据是否有效
        """
        try:
            # 尝试序列化后再反序列化
            serialized = cls.serialize(data)
            json_str = json.dumps(serialized)
            restored = json.loads(json_str)
            cls.deserialize(restored)
            return True
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    @classmethod
    def to_json(cls, value: Any, indent: Optional[int] = None) -> str:
        """将值转换为JSON字符串
        
        Args:
            value: 要转换的值
            indent: 缩进空格数（None表示压缩）
            
        Returns:
            JSON字符串
        """
        serialized = cls.serialize(value)
        return json.dumps(serialized, ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> Any:
        """从JSON字符串还原值
        
        Args:
            json_str: JSON字符串
            
        Returns:
            还原后的值
        """
        data = json.loads(json_str)
        return cls.deserialize(data)


# 便捷函数
def serialize(value: Any) -> Any:
    """序列化值"""
    return ParameterSerializer.serialize(value)


def deserialize(value: Any, context: Optional[Dict] = None) -> Any:
    """反序列化值"""
    return ParameterSerializer.deserialize(value, context)


def to_json(value: Any, indent: Optional[int] = None) -> str:
    """转换为JSON字符串"""
    return ParameterSerializer.to_json(value, indent)


def from_json(json_str: str) -> Any:
    """从JSON字符串还原"""
    return ParameterSerializer.from_json(json_str)
