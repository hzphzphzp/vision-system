#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据提取规则模块

为Modbus TCP协议提供灵活的数据提取规则配置，支持多种数据提取方式：
- 无提取规则（默认）
- 寄存器位提取（从寄存器值中提取特定位）
- 多寄存器组合（将多个寄存器组合成一个值）
- 数据类型转换（INT16/INT32/UINT16/UINT32/FLOAT等）
- 字节序转换（大端序/小端序）
- 缩放和偏移（线性变换：value = raw * scale + offset）
- 条件提取（根据条件选择不同提取方式）

Author: Vision System Team
Date: 2026-02-05
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
import struct


class ExtractionRuleType(Enum):
    """数据提取规则类型"""
    
    NONE = "none"                           # 无提取规则（默认）
    BIT_EXTRACT = "bit_extract"             # 位提取
    REGISTER_COMBINE = "register_combine"   # 多寄存器组合
    TYPE_CONVERT = "type_convert"           # 数据类型转换
    BYTE_ORDER = "byte_order"               # 字节序转换
    SCALE_OFFSET = "scale_offset"           # 缩放和偏移
    CONDITIONAL = "conditional"             # 条件提取


class DataType(Enum):
    """数据类型"""
    
    INT16 = "int16"         # 有符号16位整数
    UINT16 = "uint16"       # 无符号16位整数
    INT32 = "int32"         # 有符号32位整数
    UINT32 = "uint32"       # 无符号32位整数
    FLOAT32 = "float32"     # 32位浮点数
    FLOAT64 = "float64"     # 64位浮点数
    BOOL = "bool"           # 布尔值
    STRING = "string"       # 字符串


class ByteOrder(Enum):
    """字节序"""
    
    BIG_ENDIAN = "big"      # 大端序（Motorola格式）
    LITTLE_ENDIAN = "little" # 小端序（Intel格式）


class BitExtractRule:
    """位提取规则"""
    
    def __init__(self, 
                 start_bit: int = 0,
                 bit_count: int = 1,
                 register_index: int = 0):
        """
        初始化位提取规则
        
        Args:
            start_bit: 起始位（0-15）
            bit_count: 提取的位数（1-16）
            register_index: 寄存器索引（从0开始）
        """
        self.start_bit = max(0, min(15, start_bit))
        self.bit_count = max(1, min(16, bit_count))
        self.register_index = register_index
    
    def extract(self, registers: List[int]) -> int:
        """
        从寄存器值中提取位
        
        Args:
            registers: 寄存器值列表
            
        Returns:
            提取的位值
        """
        if not registers or self.register_index >= len(registers):
            return 0
        
        value = registers[self.register_index]
        # 创建掩码并提取位
        mask = ((1 << self.bit_count) - 1) << self.start_bit
        return (value & mask) >> self.start_bit
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_bit": self.start_bit,
            "bit_count": self.bit_count,
            "register_index": self.register_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BitExtractRule':
        """从字典创建"""
        return cls(
            start_bit=data.get("start_bit", 0),
            bit_count=data.get("bit_count", 1),
            register_index=data.get("register_index", 0)
        )


class RegisterCombineRule:
    """多寄存器组合规则"""
    
    def __init__(self,
                 register_indices: List[int] = None,
                 byte_order: ByteOrder = ByteOrder.BIG_ENDIAN):
        """
        初始化寄存器组合规则
        
        Args:
            register_indices: 要组合的寄存器索引列表
            byte_order: 字节序
        """
        self.register_indices = register_indices or [0, 1]
        self.byte_order = byte_order
    
    def combine(self, registers: List[int]) -> int:
        """
        组合多个寄存器值
        
        Args:
            registers: 寄存器值列表
            
        Returns:
            组合后的32位整数值
        """
        if len(self.register_indices) < 2:
            return registers[0] if registers else 0
        
        # 获取寄存器值
        values = []
        for idx in self.register_indices:
            if idx < len(registers):
                values.append(registers[idx])
            else:
                values.append(0)
        
        # 组合值
        if self.byte_order == ByteOrder.BIG_ENDIAN:
            # 高位在前
            result = (values[0] << 16) | values[1]
        else:
            # 低位在前
            result = (values[1] << 16) | values[0]
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "register_indices": self.register_indices,
            "byte_order": self.byte_order.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegisterCombineRule':
        """从字典创建"""
        return cls(
            register_indices=data.get("register_indices", [0, 1]),
            byte_order=ByteOrder(data.get("byte_order", "big"))
        )


class TypeConvertRule:
    """数据类型转换规则"""
    
    def __init__(self,
                 source_type: DataType = DataType.UINT16,
                 target_type: DataType = DataType.INT32,
                 byte_order: ByteOrder = ByteOrder.BIG_ENDIAN):
        """
        初始化类型转换规则
        
        Args:
            source_type: 源数据类型
            target_type: 目标数据类型
            byte_order: 字节序
        """
        self.source_type = source_type
        self.target_type = target_type
        self.byte_order = byte_order
    
    def convert(self, value: Union[int, float, bytes]) -> Union[int, float, bool, str]:
        """
        转换数据类型
        
        Args:
            value: 原始值
            
        Returns:
            转换后的值
        """
        try:
            # 首先将值转换为字节
            if isinstance(value, int):
                if self.source_type in [DataType.INT16, DataType.UINT16]:
                    byte_data = struct.pack('>H', value & 0xFFFF)
                elif self.source_type in [DataType.INT32, DataType.UINT32]:
                    byte_data = struct.pack('>I', value & 0xFFFFFFFF)
                elif self.source_type == DataType.FLOAT32:
                    byte_data = struct.pack('>f', float(value))
                else:
                    byte_data = struct.pack('>d', float(value))
            elif isinstance(value, float):
                byte_data = struct.pack('>f', value)
            elif isinstance(value, bytes):
                byte_data = value
            else:
                byte_data = str(value).encode('utf-8')
            
            # 根据目标类型解析字节
            if self.target_type == DataType.INT16:
                fmt = '>h' if self.byte_order == ByteOrder.BIG_ENDIAN else '<h'
                return struct.unpack(fmt, byte_data[:2])[0]
            elif self.target_type == DataType.UINT16:
                fmt = '>H' if self.byte_order == ByteOrder.BIG_ENDIAN else '<H'
                return struct.unpack(fmt, byte_data[:2])[0]
            elif self.target_type == DataType.INT32:
                fmt = '>i' if self.byte_order == ByteOrder.BIG_ENDIAN else '<i'
                return struct.unpack(fmt, byte_data[:4])[0]
            elif self.target_type == DataType.UINT32:
                fmt = '>I' if self.byte_order == ByteOrder.BIG_ENDIAN else '<I'
                return struct.unpack(fmt, byte_data[:4])[0]
            elif self.target_type == DataType.FLOAT32:
                fmt = '>f' if self.byte_order == ByteOrder.BIG_ENDIAN else '<f'
                return struct.unpack(fmt, byte_data[:4])[0]
            elif self.target_type == DataType.FLOAT64:
                fmt = '>d' if self.byte_order == ByteOrder.BIG_ENDIAN else '<d'
                return struct.unpack(fmt, byte_data[:8])[0]
            elif self.target_type == DataType.BOOL:
                return bool(value)
            elif self.target_type == DataType.STRING:
                return byte_data.decode('utf-8', errors='ignore').strip('\x00')
            
            return value
        except Exception as e:
            print(f"[TypeConvertRule] 转换失败: {e}")
            return value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source_type": self.source_type.value,
            "target_type": self.target_type.value,
            "byte_order": self.byte_order.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypeConvertRule':
        """从字典创建"""
        return cls(
            source_type=DataType(data.get("source_type", "uint16")),
            target_type=DataType(data.get("target_type", "int32")),
            byte_order=ByteOrder(data.get("byte_order", "big"))
        )


class ScaleOffsetRule:
    """缩放和偏移规则"""
    
    def __init__(self,
                 scale: float = 1.0,
                 offset: float = 0.0,
                 decimal_places: int = 2):
        """
        初始化缩放偏移规则
        
        Args:
            scale: 缩放系数
            offset: 偏移量
            decimal_places: 小数位数
        """
        self.scale = scale
        self.offset = offset
        self.decimal_places = decimal_places
    
    def apply(self, value: Union[int, float]) -> float:
        """
        应用缩放和偏移
        
        Args:
            value: 原始值
            
        Returns:
            变换后的值
        """
        result = float(value) * self.scale + self.offset
        return round(result, self.decimal_places)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scale": self.scale,
            "offset": self.offset,
            "decimal_places": self.decimal_places
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScaleOffsetRule':
        """从字典创建"""
        return cls(
            scale=data.get("scale", 1.0),
            offset=data.get("offset", 0.0),
            decimal_places=data.get("decimal_places", 2)
        )


class ConditionalRule:
    """条件提取规则"""
    
    def __init__(self,
                 condition_field: str = "",
                 condition_value: Any = None,
                 true_rule: 'DataExtractionRule' = None,
                 false_rule: 'DataExtractionRule' = None):
        """
        初始化条件规则
        
        Args:
            condition_field: 条件字段名
            condition_value: 条件值
            true_rule: 条件为真时应用的规则
            false_rule: 条件为假时应用的规则
        """
        self.condition_field = condition_field
        self.condition_value = condition_value
        self.true_rule = true_rule
        self.false_rule = false_rule
    
    def apply(self, data: Dict[str, Any]) -> Any:
        """
        应用条件规则
        
        Args:
            data: 输入数据
            
        Returns:
            提取结果
        """
        condition_met = data.get(self.condition_field) == self.condition_value
        
        if condition_met and self.true_rule:
            return self.true_rule.extract(data)
        elif not condition_met and self.false_rule:
            return self.false_rule.extract(data)
        else:
            return data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "condition_field": self.condition_field,
            "condition_value": self.condition_value,
            "true_rule": self.true_rule.to_dict() if self.true_rule else None,
            "false_rule": self.false_rule.to_dict() if self.false_rule else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConditionalRule':
        """从字典创建"""
        true_rule_data = data.get("true_rule")
        false_rule_data = data.get("false_rule")
        
        return cls(
            condition_field=data.get("condition_field", ""),
            condition_value=data.get("condition_value"),
            true_rule=DataExtractionRule.from_dict(true_rule_data) if true_rule_data else None,
            false_rule=DataExtractionRule.from_dict(false_rule_data) if false_rule_data else None
        )


class DataExtractionRule:
    """数据提取规则主类"""
    
    def __init__(self,
                 rule_type: ExtractionRuleType = ExtractionRuleType.NONE,
                 name: str = "",
                 description: str = "",
                 enabled: bool = True):
        """
        初始化数据提取规则
        
        Args:
            rule_type: 规则类型
            name: 规则名称
            description: 规则描述
            enabled: 是否启用
        """
        self.rule_type = rule_type
        self.name = name
        self.description = description
        self.enabled = enabled
        
        # 具体规则配置
        self.bit_extract_rule: Optional[BitExtractRule] = None
        self.register_combine_rule: Optional[RegisterCombineRule] = None
        self.type_convert_rule: Optional[TypeConvertRule] = None
        self.scale_offset_rule: Optional[ScaleOffsetRule] = None
        self.conditional_rule: Optional[ConditionalRule] = None
    
    def extract(self, data: Union[Dict[str, Any], List[int], int]) -> Any:
        """
        应用提取规则
        
        Args:
            data: 输入数据（字典、寄存器列表或单个值）
            
        Returns:
            提取后的数据
        """
        if not self.enabled or self.rule_type == ExtractionRuleType.NONE:
            return data
        
        try:
            if self.rule_type == ExtractionRuleType.BIT_EXTRACT and self.bit_extract_rule:
                if isinstance(data, list):
                    return self.bit_extract_rule.extract(data)
                elif isinstance(data, dict) and "registers" in data:
                    return self.bit_extract_rule.extract(data["registers"])
            
            elif self.rule_type == ExtractionRuleType.REGISTER_COMBINE and self.register_combine_rule:
                if isinstance(data, list):
                    return self.register_combine_rule.combine(data)
                elif isinstance(data, dict) and "registers" in data:
                    return self.register_combine_rule.combine(data["registers"])
            
            elif self.rule_type == ExtractionRuleType.TYPE_CONVERT and self.type_convert_rule:
                return self.type_convert_rule.convert(data)
            
            elif self.rule_type == ExtractionRuleType.SCALE_OFFSET and self.scale_offset_rule:
                return self.scale_offset_rule.apply(data)
            
            elif self.rule_type == ExtractionRuleType.CONDITIONAL and self.conditional_rule:
                return self.conditional_rule.apply(data)
            
            return data
            
        except Exception as e:
            print(f"[DataExtractionRule] 提取失败: {e}")
            return data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled
        }
        
        if self.bit_extract_rule:
            result["bit_extract_rule"] = self.bit_extract_rule.to_dict()
        if self.register_combine_rule:
            result["register_combine_rule"] = self.register_combine_rule.to_dict()
        if self.type_convert_rule:
            result["type_convert_rule"] = self.type_convert_rule.to_dict()
        if self.scale_offset_rule:
            result["scale_offset_rule"] = self.scale_offset_rule.to_dict()
        if self.conditional_rule:
            result["conditional_rule"] = self.conditional_rule.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataExtractionRule':
        """从字典创建"""
        rule = cls(
            rule_type=ExtractionRuleType(data.get("rule_type", "none")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            enabled=data.get("enabled", True)
        )
        
        if "bit_extract_rule" in data:
            rule.bit_extract_rule = BitExtractRule.from_dict(data["bit_extract_rule"])
        if "register_combine_rule" in data:
            rule.register_combine_rule = RegisterCombineRule.from_dict(data["register_combine_rule"])
        if "type_convert_rule" in data:
            rule.type_convert_rule = TypeConvertRule.from_dict(data["type_convert_rule"])
        if "scale_offset_rule" in data:
            rule.scale_offset_rule = ScaleOffsetRule.from_dict(data["scale_offset_rule"])
        if "conditional_rule" in data:
            rule.conditional_rule = ConditionalRule.from_dict(data["conditional_rule"])
        
        return rule
    
    @staticmethod
    def get_rule_type_description(rule_type: ExtractionRuleType) -> str:
        """获取规则类型描述"""
        descriptions = {
            ExtractionRuleType.NONE: "无提取规则 - 直接使用原始数据",
            ExtractionRuleType.BIT_EXTRACT: "位提取 - 从寄存器值中提取特定位",
            ExtractionRuleType.REGISTER_COMBINE: "多寄存器组合 - 将多个寄存器组合成一个值",
            ExtractionRuleType.TYPE_CONVERT: "数据类型转换 - 转换数据类型（INT16/INT32/FLOAT等）",
            ExtractionRuleType.BYTE_ORDER: "字节序转换 - 转换大端序/小端序",
            ExtractionRuleType.SCALE_OFFSET: "缩放和偏移 - 线性变换：value = raw * scale + offset",
            ExtractionRuleType.CONDITIONAL: "条件提取 - 根据条件选择不同提取方式"
        }
        return descriptions.get(rule_type, "未知规则类型")
    
    @staticmethod
    def get_data_type_description(data_type: DataType) -> str:
        """获取数据类型描述"""
        descriptions = {
            DataType.INT16: "有符号16位整数 (-32768 ~ 32767)",
            DataType.UINT16: "无符号16位整数 (0 ~ 65535)",
            DataType.INT32: "有符号32位整数 (-2147483648 ~ 2147483647)",
            DataType.UINT32: "无符号32位整数 (0 ~ 4294967295)",
            DataType.FLOAT32: "32位浮点数（单精度）",
            DataType.FLOAT64: "64位浮点数（双精度）",
            DataType.BOOL: "布尔值（真/假）",
            DataType.STRING: "字符串"
        }
        return descriptions.get(data_type, "未知数据类型")


# 预定义常用规则模板
def _create_predefined_rules() -> Dict[str, DataExtractionRule]:
    """创建预定义规则模板"""
    rules = {}
    
    # 温度传感器
    temp_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.SCALE_OFFSET,
        name="温度传感器",
        description="将原始值转换为温度值（摄氏度）"
    )
    temp_rule.scale_offset_rule = ScaleOffsetRule(scale=0.1, offset=-40.0, decimal_places=1)
    rules["温度传感器"] = temp_rule
    
    # 压力传感器
    pressure_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.SCALE_OFFSET,
        name="压力传感器",
        description="将原始值转换为压力值（MPa）"
    )
    pressure_rule.scale_offset_rule = ScaleOffsetRule(scale=0.001, offset=0.0, decimal_places=3)
    rules["压力传感器"] = pressure_rule
    
    # 32位整数组合
    combine_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.REGISTER_COMBINE,
        name="32位整数组合",
        description="将两个16位寄存器组合成32位整数"
    )
    combine_rule.register_combine_rule = RegisterCombineRule(
        register_indices=[0, 1],
        byte_order=ByteOrder.BIG_ENDIAN
    )
    rules["32位整数组合"] = combine_rule
    
    # 浮点数转换
    float_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.TYPE_CONVERT,
        name="浮点数转换",
        description="将寄存器值转换为32位浮点数"
    )
    float_rule.type_convert_rule = TypeConvertRule(
        source_type=DataType.UINT32,
        target_type=DataType.FLOAT32,
        byte_order=ByteOrder.BIG_ENDIAN
    )
    rules["浮点数转换"] = float_rule
    
    # 状态位提取
    bit_rule = DataExtractionRule(
        rule_type=ExtractionRuleType.BIT_EXTRACT,
        name="状态位提取",
        description="提取寄存器的第0位作为状态标志"
    )
    bit_rule.bit_extract_rule = BitExtractRule(start_bit=0, bit_count=1, register_index=0)
    rules["状态位提取"] = bit_rule
    
    return rules


# 预定义规则模板（延迟初始化）
PREDEFINED_RULES: Dict[str, DataExtractionRule] = {}


def get_predefined_rules() -> Dict[str, DataExtractionRule]:
    """获取预定义规则模板"""
    global PREDEFINED_RULES
    if not PREDEFINED_RULES:
        PREDEFINED_RULES = _create_predefined_rules()
    return PREDEFINED_RULES.copy()


def create_default_rule() -> DataExtractionRule:
    """创建默认规则（无提取规则）"""
    return DataExtractionRule(
        rule_type=ExtractionRuleType.NONE,
        name="默认规则",
        description="不使用数据提取规则，直接使用原始数据",
        enabled=True
    )


if __name__ == "__main__":
    # 测试代码
    print("数据提取规则模块测试")
    print("=" * 50)
    
    # 测试位提取
    print("\n1. 位提取测试")
    bit_rule = BitExtractRule(start_bit=4, bit_count=4)
    registers = [0xABCD]  # 二进制: 1010 1011 1100 1101
    result = bit_rule.extract(registers)
    print(f"  寄存器值: 0x{registers[0]:04X} ({bin(registers[0])})")
    print(f"  提取位 4-7: 0x{result:X} ({bin(result)})")
    
    # 测试寄存器组合
    print("\n2. 寄存器组合测试")
    combine_rule = RegisterCombineRule(register_indices=[0, 1], byte_order=ByteOrder.BIG_ENDIAN)
    registers = [0x1234, 0x5678]
    result = combine_rule.combine(registers)
    print(f"  寄存器值: [0x{registers[0]:04X}, 0x{registers[1]:04X}]")
    print(f"  组合结果: 0x{result:08X} ({result})")
    
    # 测试缩放偏移
    print("\n3. 缩放偏移测试")
    scale_rule = ScaleOffsetRule(scale=0.1, offset=-40.0, decimal_places=1)
    raw_value = 250
    result = scale_rule.apply(raw_value)
    print(f"  原始值: {raw_value}")
    print(f"  转换结果: {result}°C (公式: {raw_value} * 0.1 - 40.0)")
    
    # 测试完整规则
    print("\n4. 完整规则测试")
    rule = DataExtractionRule(
        rule_type=ExtractionRuleType.SCALE_OFFSET,
        name="温度转换",
        description="温度传感器数据转换"
    )
    rule.scale_offset_rule = ScaleOffsetRule(scale=0.1, offset=-40.0)
    result = rule.extract(300)
    print(f"  规则: {rule.name}")
    print(f"  输入: 300")
    print(f"  输出: {result}°C")
    
    print("\n" + "=" * 50)
    print("测试完成")
