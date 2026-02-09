#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的通讯工具模块

提供完整的数据发送和接收功能，支持多种通讯协议：
- SendDataTool: 发送数据到外部设备
- ReceiveDataTool: 接收外部设备数据

功能特性:
- 多种协议支持：TCP客户端/服务端、串口、WebSocket、Modbus TCP
- 多种数据格式：JSON、ASCII、HEX、二进制
- 动态IO类型：支持Int/Float/String/Point/Circle/Rect/Posture等
- 连接管理：持久化连接、连接复用、设备ID管理

Author: Vision System Team
Date: 2026-02-03
"""

import json
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.communication import ConnectionState, ProtocolManager, ProtocolType
from core.communication.dynamic_io import (
    IoType, IoDataFactory, DynamicOutputParser,
    PointF, Circle, RectBox, Posture, Fixture
)
from core.tool_base import ToolBase, ToolParameter, ToolRegistry
from core.parameter_serializer import ParameterSerializer


def _get_comm_manager():
    """获取通讯管理器（从UI模块获取单例）"""
    try:
        from ui.communication_config import get_connection_manager
        return get_connection_manager()
    except ImportError:
        # 如果UI模块不可用，使用tools中的管理器
        from tools.communication.communication import get_communication_manager
        return get_communication_manager()


@ToolRegistry.register
class SendDataTool(ToolBase):
    """发送数据工具（重构版）

    将数据发送到外部设备。通过连接ID使用已有的通讯连接，
    专注于数据处理和路由，不负责连接管理。

    功能特性:
    - 使用已有连接：通过连接ID引用ConnectionManager中的连接
    - 数据映射：支持将上游工具输出映射为发送格式
    - 发送条件控制：总是/成功时/失败时
    - 仅发送变化的数据：避免重复发送相同数据
    - 多种数据格式：JSON、ASCII、HEX、二进制

    端口:
    - 输入端口: InputTrigger (触发信号，可选)
    """

    tool_name = "发送数据"
    tool_category = "Communication"
    tool_description = "发送数据到外部设备，通过连接ID使用已有连接"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._data_mapper = None  # 数据映射器实例
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0
        self._last_sent_data = None  # 上次发送的数据，用于变化检测

    # 参数定义 - 用于属性面板识别参数类型
    PARAM_DEFINITIONS = [
        {
            "name": "目标连接",
            "param_type": "enum",
            "default": "",
            "description": "选择要发送数据的通讯连接"
        },
        {
            "name": "发送格式",
            "param_type": "enum",
            "default": "JSON",
            "options": ["JSON", "ASCII", "HEX", "二进制"],
            "description": "发送数据格式"
        },
        {
            "name": "数据内容",
            "param_type": "data_content",  # 特殊类型：数据内容选择器
            "default": "",
            "description": "点击选择要发送的数据（格式：模块名称.结果字段）"
        },
        {
            "name": "发送条件",
            "param_type": "enum",
            "default": "总是",
            "options": ["总是", "成功时", "失败时"],
            "description": "发送触发条件"
        },
        {
            "name": "仅发送变化的数据",
            "param_type": "bool",
            "default": False,
            "description": "是否只发送变化的数据"
        }
    ]

    def _init_params(self):
        """初始化参数（优化版）
        
        优化内容：
        1. 目标连接改为下拉框选择
        2. 数据内容支持"模块名称.结果字段"格式选择
        3. 不默认保存"all"
        4. 只在参数不存在时才设置默认值，避免覆盖用户设置
        5. 延迟加载连接列表，避免初始化时卡顿
        """
        self._logger.info(f"【_init_params】开始初始化参数，当前参数: {dict(self._params)}")
        
        # 只在参数不存在或为空时设置默认值
        current_connection = self._params.get("目标连接", "")
        self._logger.info(f"【_init_params】当前目标连接值: '{current_connection}'")
        
        # 延迟加载：只在需要时获取连接列表
        # 初始化时设置空列表或默认值，避免卡顿
        if not current_connection:
            self._logger.info(f"【_init_params】目标连接为空，设置默认值（延迟加载连接列表）")
            self.set_param("目标连接", "",
                          param_type="enum",
                          options=["点击刷新获取连接列表"],
                          description="选择要发送数据的通讯连接（点击下拉框刷新）")
        else:
            # 只更新选项列表，不覆盖值（延迟加载）
            self._logger.info(f"【_init_params】目标连接不为空，延迟加载选项列表")
            self._params[f"__options_目标连接"] = ["点击刷新获取连接列表"]
        
        self._logger.info(f"【_init_params】初始化完成，目标连接值: '{self._params.get('目标连接', '')}'")

        # 数据配置 - 只在不存在时设置默认值
        if "发送格式" not in self._params:
            self.set_param("发送格式", "JSON",
                          param_type="enum",
                          options=["JSON", "ASCII", "HEX", "二进制"],
                          description="发送数据格式")
        
        # 数据内容 - 只在不存在时设置默认值
        if "数据内容" not in self._params:
            self.set_param("数据内容", "",
                          param_type="data_content",
                          description="点击选择要发送的数据（格式：模块名称.结果字段）")

        # 发送控制 - 只在不存在时设置默认值
        if "发送条件" not in self._params:
            self.set_param("发送条件", "总是",
                          param_type="enum",
                          options=["总是", "成功时", "失败时"],
                          description="发送触发条件")
        if "仅发送变化的数据" not in self._params:
            self.set_param("仅发送变化的数据", False, description="是否只发送变化的数据")
    
    def _on_param_changed(self, key: str, old_value: Any, new_value: Any):
        """参数变更回调
        
        当目标连接参数被点击时，刷新连接列表
        """
        super()._on_param_changed(key, old_value, new_value)
        
        if key == "目标连接":
            # 检查是否需要刷新连接列表
            # 当选择"点击刷新获取连接列表"或"暂无可用连接"时，刷新列表
            if new_value in ["点击刷新获取连接列表", "暂无可用连接"] or old_value == "点击刷新获取连接列表":
                self._logger.info(f"【_on_param_changed】刷新连接列表，新值: '{new_value}', 旧值: '{old_value}'")
                self._refresh_connection_options()
    
    def _refresh_connection_options(self):
        """刷新连接列表选项"""
        try:
            self._logger.info("【_refresh_connection_options】开始刷新连接列表...")
            
            # 清除缓存，强制获取最新连接
            if hasattr(self, '_connections_cache'):
                delattr(self, '_connections_cache')
                self._logger.debug("【_refresh_connection_options】已清除连接缓存")
            
            available_connections = self._get_available_connections()
            self._logger.info(f"【_refresh_connection_options】获取到 {len(available_connections)} 个连接")
            
            if available_connections:
                self._params["__options_目标连接"] = available_connections
                # 自动选择第一个可用连接
                first_connection = available_connections[0]
                self.set_param("目标连接", first_connection)
                self._logger.info(f"【_refresh_connection_options】自动选择第一个连接: {first_connection}")
            else:
                self._params["__options_目标连接"] = ["暂无可用连接"]
                # 清空当前选择
                self.set_param("目标连接", "")
                self._logger.warning("【_refresh_connection_options】没有可用的连接")
        except Exception as e:
            self._logger.error(f"【_refresh_connection_options】刷新连接列表失败: {e}", exc_info=True)
            self._params["__options_目标连接"] = ["刷新失败，请重试"]
    
    def _update_data_content_options(self):
        """根据上游数据更新数据内容选项"""
        upstream_values = self.get_upstream_values()
        
        if upstream_values:
            # 有上游数据，生成字段选择列表
            field_options = []
            for key in upstream_values.keys():
                # 将字段名转换为中文显示
                display_name = self._translate_field_name(key)
                field_options.append(f"{display_name} ({key})")
            
            # 添加特殊选项
            field_options.insert(0, "全部数据 (all)")
            field_options.append("自定义输入")
            
            self.set_param("数据内容", "",
                          param_type="enum",
                          options=field_options,
                          description="选择要发送的数据字段")
        else:
            # 没有上游数据，使用文本输入
            self.set_param("数据内容", "",
                          param_type="text",
                          description="输入要发送的数据内容（无上游数据可用）")
    
    def _translate_field_name(self, field_name: str) -> str:
        """将字段名翻译为中文"""
        translations = {
            # 通用字段
            "status": "状态",
            "result": "结果",
            "message": "消息",
            "error": "错误",
            "confidence": "置信度",
            "score": "分数",
            "value": "数值",
            "count": "数量",
            "index": "索引",
            "id": "编号",
            "name": "名称",
            "type": "类型",
            "category": "类别",
            "label": "标签",
            "timestamp": "时间戳",
            
            # 图像相关
            "width": "width",
            "height": "height",
            "channels": "通道数",
            "format": "格式",
            "size": "大小",
            "resolution": "分辨率",
            
            # 位置相关
            "x": "X坐标",
            "y": "Y坐标",
            "z": "Z坐标",
            "position": "位置",
            "center": "中心点",
            "top": "顶部",
            "bottom": "底部",
            "left": "左侧",
            "right": "右侧",
            
            # 尺寸相关
            "radius": "半径",
            "diameter": "直径",
            "area": "面积",
            "perimeter": "周长",
            "length": "长度",
            "distance": "距离",
            "angle": "角度",
            "rotation": "旋转角度",
            "scale": "缩放比例",
            
            # 检测相关
            "detected": "检测结果",
            "found": "发现目标",
            "matched": "匹配结果",
            "recognized": "识别结果",
            "verified": "验证结果",
            "passed": "通过状态",
            "failed": "失败状态",
            
            # 码识别相关
            "code": "码值",
            "barcode": "条形码",
            "qrcode": "二维码",
            "content": "内容",
            "data": "数据",
            "text": "文本",
            
            # 匹配相关
            "template": "模板",
            "similarity": "相似度",
            "correlation": "相关性",
            "offset": "偏移量",
            "shift": "位移",
            
            # 测量相关
            "measurement": "测量值",
            "dimension": "尺寸",
            "thickness": "厚度",
            "width_mm": "宽度(mm)",
            "height_mm": "高度(mm)",
            "depth": "深度",
            "volume": "体积",
            
            # 颜色相关
            "color": "颜色",
            "gray": "灰度",
            "brightness": "亮度",
            "contrast": "对比度",
            "saturation": "饱和度",
            "hue": "色调",
            
            # 通信相关
            "device_id": "设备ID",
            "connection": "连接",
            "sent": "已发送",
            "received": "已接收",
            "send_count": "发送次数",
            "receive_count": "接收次数",
        }
        
        return translations.get(field_name, field_name)

    def _get_available_connections(self) -> List[str]:
        """获取可用的连接列表（带缓存机制，避免卡顿）
        
        修复：
        1. 添加缓存避免重复查询
        2. 使用非阻塞方式获取连接
        3. 异常时返回缓存数据或空列表
        """
        import time
        
        # 检查缓存（缩短缓存时间以获取最新连接）
        cache_attr = '_connections_cache'
        cache_timeout = 1.0  # 1秒缓存，确保能获取最新连接状态
        
        if hasattr(self, cache_attr):
            cache_time, cache_data = getattr(self, cache_attr)
            if time.time() - cache_time < cache_timeout:
                self._logger.debug(f"使用缓存的连接列表，缓存时间: {time.time() - cache_time:.2f}秒")
                return cache_data
        
        try:
            conn_manager = _get_comm_manager()
            result = []
            
            # 快速检查连接管理器是否可用（非阻塞）
            if conn_manager is None:
                self._logger.warning("【_get_available_connections】连接管理器为None")
                return []
            
            self._logger.debug(f"【_get_available_connections】连接管理器类型: {type(conn_manager)}")
            
            # 方法1：使用get_available_connections（推荐）
            if hasattr(conn_manager, 'get_available_connections'):
                connections = conn_manager.get_available_connections()
                self._logger.info(f"【_get_available_connections】从连接管理器获取到 {len(connections)} 个可用连接")
                
                if not connections:
                    # 如果没有可用连接，尝试获取所有连接（包括未连接的）用于调试
                    if hasattr(conn_manager, 'get_all_connections'):
                        all_connections = conn_manager.get_all_connections()
                        self._logger.debug(f"【_get_available_connections】所有连接数量: {len(all_connections)}")
                        for conn in all_connections:
                            conn_id = getattr(conn, 'id', 'unknown')
                            is_connected = getattr(conn, 'is_connected', False)
                            self._logger.debug(f"  连接 {conn_id}: is_connected={is_connected}")
                
                for conn in connections:
                    display_name = conn.get("display_name", "")
                    device_id = conn.get("device_id", "")
                    name = conn.get("name", "")
                    protocol = conn.get("protocol_type", "Unknown")
                    
                    self._logger.debug(f"连接信息: device_id={device_id}, name={name}, display_name={display_name}")
                    
                    # 确保 display_name 不为空
                    if not display_name:
                        display_name = f"[{protocol}] {name}"
                    
                    # 确保 device_id 不为空
                    if not device_id:
                        device_id = name
                    
                    result.append(f"{device_id}: {display_name}")
            
            # 方法2：使用get_all_connections（备选）
            elif hasattr(conn_manager, 'get_all_connections'):
                connections = conn_manager.get_all_connections()
                for conn in connections:
                    conn_id = getattr(conn, 'id', '')
                    name = getattr(conn, 'name', '')
                    protocol = getattr(conn, 'protocol_type', 'TCP')
                    is_connected = getattr(conn, 'is_connected', False)
                    status = "已连接" if is_connected else "未连接"
                    result.append(f"{conn_id}: [{protocol}] {name} ({status})")
            
            # 更新缓存
            setattr(self, cache_attr, (time.time(), result))
            return result
            
        except Exception as e:
            # 出错时返回缓存数据（如果可用）
            if hasattr(self, cache_attr):
                return getattr(self, cache_attr)[1]
            return []

    def _get_connection_by_display_name(self, display_name: str) -> Optional[Any]:
        """根据显示名称获取连接
        
        支持两种格式：
        1. 完整的显示格式：device_id: display_name
        2. 只有display_name
        """
        try:
            conn_manager = _get_comm_manager()
            connections = conn_manager.get_available_connections()
            
            self._logger.debug(f"尝试根据显示名称查找连接: {display_name}")
            self._logger.debug(f"可用连接数: {len(connections)}")
            
            # 尝试直接匹配 display_name
            for conn in connections:
                conn_display_name = conn.get("display_name", "")
                self._logger.debug(f"检查连接: display_name={conn_display_name}")
                if conn_display_name == display_name:
                    device_id = conn.get("device_id", conn.get("name", ""))
                    self._logger.debug(f"找到匹配，使用 device_id: {device_id}")
                    return conn_manager.get_connection(device_id)
            
            # 尝试解析 device_id: display_name 格式
            if ": " in display_name:
                parts = display_name.split(": ", 1)
                if len(parts) == 2:
                    device_id = parts[0]
                    self._logger.debug(f"尝试使用解析的 device_id 查找: {device_id}")
                    # 使用device_id查找
                    for conn in connections:
                        if conn.get("device_id") == device_id:
                            self._logger.debug(f"找到匹配的 device_id: {device_id}")
                            return conn_manager.get_connection(device_id)
            
            self._logger.warning(f"未找到匹配的连接: {display_name}")
            return None
        except Exception as e:
            self._logger.error(f"根据显示名称获取连接失败: {e}")
            import traceback
            self._logger.error(traceback.format_exc())
            return None

    def _run_impl(self):
        """执行发送逻辑（重构版）"""
        try:
            self._logger.info(f"[{self.name}] 开始执行发送数据...")
            
            # 调试：查看所有参数及其值
            all_params = self.get_all_params()
            self._logger.debug(f"工具所有参数键: {list(all_params.keys())}")
            self._logger.info(f"【调试】所有参数及其值:")
            for key, value in all_params.items():
                if not key.startswith('__'):
                    self._logger.info(f"  {key}: '{value}' (类型: {type(value).__name__})")
            
            # 特别查看目标连接参数
            target_conn_value = all_params.get("目标连接", "")
            self._logger.info(f"【调试】目标连接原始值: '{target_conn_value}'")
            self._logger.info(f"【调试】目标连接类型: {type(target_conn_value)}")
            self._logger.info(f"【调试】目标连接是否为空: {not target_conn_value}")
            if target_conn_value:
                self._logger.info(f"【调试】目标连接长度: {len(str(target_conn_value))}")
                self._logger.info(f"【调试】目标连接repr: {repr(target_conn_value)}")
            
            # 1. 检查目标连接 - 尝试多个可能的参数名
            connection_id = ""
            
            # 尝试不同的参数名（处理可能的参数名不一致问题）
            possible_names = ["目标连接", "连接ID", "connection_id", "target_connection"]
            for name in possible_names:
                value = all_params.get(name, "")
                self._logger.info(f"【调试】尝试参数名 '{name}': '{value}'")
                if value:
                    connection_id = value
                    self._logger.info(f"【调试】使用参数名 '{name}' 获取连接: '{connection_id}'")
                    break
            
            # 如果没有找到，使用默认的 get_param
            if not connection_id:
                connection_id = self.get_param("目标连接", "")
                self._logger.info(f"【调试】使用get_param获取: '{connection_id}'")
            
            # 检查是否是提示文本，如果是则自动刷新
            if connection_id in ["点击刷新获取连接列表", "暂无可用连接", "刷新失败，请重试"]:
                self._logger.info(f"【调试】当前选择的是提示文本 '{connection_id}'，自动刷新连接列表")
                self._refresh_connection_options()
                # 重新获取连接ID
                connection_id = self.get_param("目标连接", "")
                self._logger.info(f"【调试】刷新后获取的连接ID: '{connection_id}'")
            
            self._logger.info(f"【调试】最终目标连接: '{connection_id}'")
            self._logger.info(f"【调试】最终目标连接类型: {type(connection_id)}")
            self._logger.info(f"【调试】最终目标连接长度: {len(str(connection_id)) if connection_id else 0}")
            
            if not connection_id or connection_id in ["点击刷新获取连接列表", "暂无可用连接", "刷新失败，请重试"]:
                self._logger.error("未选择有效的连接")
                self._logger.error(f"可用参数: {list(all_params.keys())}")
                return {
                    "status": False,
                    "message": "未选择有效的通讯连接，请在属性面板中选择",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 2. 获取连接
            conn_manager = _get_comm_manager()
            
            # 首先尝试直接使用connection_id查找
            connection = conn_manager.get_connection(connection_id)
            self._logger.debug(f"直接查找连接结果: {connection is not None}")
            
            # 如果找不到，尝试解析 device_id: display_name 格式，提取device_id
            if not connection and ": " in connection_id:
                parts = connection_id.split(": ", 1)
                if len(parts) == 2:
                    device_id = parts[0]
                    self._logger.debug(f"尝试使用device_id查找: {device_id}")
                    connection = conn_manager.get_connection(device_id)
                    self._logger.debug(f"使用device_id查找结果: {connection is not None}")

            # 如果还找不到，尝试使用display_name查找
            if not connection:
                connection = self._get_connection_by_display_name(connection_id)
                self._logger.debug(f"通过display_name查找连接结果: {connection is not None}")

            if not connection:
                self._logger.error(f"未找到连接: {connection_id}")
                return {
                    "status": False,
                    "message": f"未找到连接: {connection_id}",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }
            
            # 3. 检查连接状态
            self._logger.debug(f"连接状态检查 - is_connected: {connection.is_connected}")
            if not connection.is_connected:
                self._logger.error(f"连接 {connection.name} 未建立")
                return {
                    "status": False,
                    "message": f"连接 {connection.name} 未建立",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }
            
            # 4. 获取协议实例
            protocol_instance = connection.protocol_instance
            self._logger.debug(f"协议实例: {protocol_instance is not None}")
            if not protocol_instance:
                self._logger.error("协议实例不存在")
                return {
                    "status": False,
                    "message": "协议实例不存在",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }
            
            # 5. 检查协议实例连接状态
            if hasattr(protocol_instance, 'is_connected') and not protocol_instance.is_connected():
                self._logger.error("协议实例未连接")
                return {
                    "status": False,
                    "message": "协议实例未连接",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 4. 收集上游输入数据
            input_data = self._collect_input_data()
            if not input_data:
                input_data = {}

            # 6. 检查发送条件
            send_condition = self.get_param("发送条件", "总是")
            self._logger.debug(f"发送条件: {send_condition}")
            if not self._should_send(send_condition, input_data):
                self._logger.info("不满足发送条件，跳过发送")
                return {
                    "status": True,
                    "message": "不满足发送条件",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 7. 直接使用收集的数据
            data_to_send = input_data
            self._logger.debug(f"准备发送的数据: {data_to_send}")

            # 8. 检查数据变化
            only_on_change = self.get_param("仅发送变化的数据", False)
            if only_on_change and self._is_data_unchanged(data_to_send):
                self._logger.info("数据未变化，跳过发送")
                return {
                    "status": True,
                    "message": "数据未变化，跳过发送",
                    "发送成功次数": self._send_count,
                    "发送失败次数": self._fail_count
                }

            # 9. 格式化数据
            format_type = self.get_param("发送格式", "JSON")
            self._logger.debug(f"格式化数据，格式: {format_type}, 数据: {data_to_send}")
            formatted_data = self._format_data(data_to_send, format_type)
            self._logger.debug(f"格式化后的数据: {formatted_data}")

            # 10. 发送数据
            self._logger.info(f"正在发送数据到 {connection_id}...")
            success = protocol_instance.send(formatted_data)
            self._logger.info(f"发送结果: {success}")

            if success:
                self._send_count += 1
                self._last_sent_data = data_to_send.copy() if isinstance(data_to_send, dict) else data_to_send
                message = "发送成功"
            else:
                self._fail_count += 1
                message = "发送失败"

            return {
                "status": success,
                "message": message,
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count,
                "连接ID": connection_id,
                "OutputData": data_to_send
            }

        except Exception as e:
            self._fail_count += 1
            self._logger.error(f"发送异常: {e}", exc_info=True)
            return {
                "status": False,
                "message": f"发送异常: {str(e)}",
                "发送成功次数": self._send_count,
                "发送失败次数": self._fail_count
            }

    def _collect_input_data(self) -> Dict[str, Any]:
        """收集上游工具的输入数据（重构版）
        
        使用新的上游结果数据传递机制：
        - 从ToolBase.get_upstream_values()获取上游数据
        - 支持{all}、{field_name}、模块名称.结果字段等格式
        """
        input_data = {}
        
        try:
            # 获取数据内容配置
            data_content = self.get_param("数据内容", "")
            self._logger.debug(f"数据内容参数: {data_content}")
            
            # 使用新的上游数据获取机制
            upstream_values = self.get_upstream_values()
            self._logger.debug(f"上游数据: {upstream_values}")
            
            if data_content:
                # 处理 "模块名称.结果字段" 格式（用户从选择器选择的格式）
                if "." in data_content and not data_content.startswith("{"):
                    parts = data_content.split(".", 1)
                    if len(parts) == 2:
                        module_name, field_name = parts
                        self._logger.debug(f"解析模块名称: {module_name}, 字段: {field_name}")
                        
                        # 从上游数据中查找对应模块的数据
                        if upstream_values:
                            # 提取特定字段的值
                            if field_name in upstream_values:
                                field_value = upstream_values[field_name]
                                input_data = {field_name: field_value}
                                self._logger.info(f"提取字段 '{field_name}' 的值: {field_value}")
                            else:
                                # 字段不存在，发送所有数据并提示
                                self._logger.warning(f"字段 '{field_name}' 不在上游数据中，发送所有数据")
                                input_data = {"data": upstream_values}
                        else:
                            # 没有上游数据，使用字段名作为key
                            input_data = {field_name: data_content}
                # 如果数据内容为{all}，发送所有上游数据
                elif data_content.strip() == "{all}":
                    if upstream_values:
                        input_data = upstream_values
                    else:
                        input_data = {"data": "all"}
                # 如果包含变量引用 {field_name}
                elif "{" in data_content and "}" in data_content:
                    if upstream_values:
                        input_data = self._parse_data_content_with_variables(data_content, upstream_values)
                    else:
                        input_data = {"data": data_content}
                else:
                    # 固定内容，作为data字段发送
                    input_data = {"data": data_content}
                
                self._logger.debug(f"收集到输入数据: {input_data}")
            elif upstream_values:
                # 没有配置数据内容，但有上游数据，发送所有上游数据
                input_data = upstream_values
                self._logger.debug(f"使用默认上游数据: {list(upstream_values.keys())}")
            else:
                self._logger.warning("没有上游数据，且数据内容未配置")
                    
        except Exception as e:
            self._logger.error(f"收集输入数据失败: {e}", exc_info=True)
            
        return input_data
    
    def _parse_data_content_with_variables(self, content: str, all_values: Dict[str, Any]) -> Dict[str, Any]:
        """解析包含变量的数据内容
        
        支持格式：
        - {all} - 发送所有上游数据
        - {field_name} - 引用上游数据的字段
        - 普通文本 - 直接包含在结果中
        
        示例：
        - "{all}" - 返回所有上游数据
        - "{status}" - 返回 {"data": "value of status"}
        - "result: {status}, value: {data}" - 返回 {"status": "...", "data": "..."}
        """
        import re
        
        # 处理空内容
        if not content or not content.strip():
            return {"data": ""}
        
        content_stripped = content.strip()
        
        # 处理 {all} - 返回所有上游数据
        if content_stripped == "{all}":
            return all_values.copy()
        
        # 简单模式：如果内容是单个变量（非{all}），直接返回该字段值
        if content_stripped.startswith("{") and content_stripped.endswith("}"):
            var_name = content_stripped[1:-1].strip()
            if var_name in all_values:
                # 如果是单个字段，直接返回该字段的值
                value = all_values[var_name]
                if isinstance(value, dict):
                    return value
                else:
                    return {"data": value}
        
        # 复杂模式：解析多个变量
        result = {}
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, content)
        
        if matches:
            # 提取所有引用的字段
            for var_name in matches:
                var_name = var_name.strip()
                if var_name in all_values:
                    result[var_name] = all_values[var_name]
            
            # 如果没有匹配到任何变量，将整个内容作为data字段
            if not result:
                result = {"data": content}
        else:
            # 没有变量，作为固定内容
            result = {"data": content}
            
        return result

    def _apply_data_template(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """应用数据模板"""
        if not template or template == "*":
            # 发送所有数据
            return data

        if template.startswith("{") and template.endswith("}"):
            # JSON格式的字段映射
            try:
                import json
                mapping = json.loads(template)
                if isinstance(mapping, dict):
                    result = {}
                    for target_field, source_field in mapping.items():
                        if source_field in data:
                            result[target_field] = data[source_field]
                    return result
            except json.JSONDecodeError:
                pass

        # 逗号分隔的字段列表
        fields = [f.strip() for f in template.split(",")]
        result = {}
        for field in fields:
            if field and field in data:
                result[field] = data[field]
        return result

    def _should_send(self, condition: str, input_data: Dict[str, Any]) -> bool:
        """检查是否应该发送数据"""
        if condition == "总是":
            return True
        elif condition == "成功时":
            # 检查是否有result字段且为True
            result = input_data.get("result", input_data.get("status", False))
            return bool(result)
        elif condition == "失败时":
            # 检查是否有result字段且为False
            result = input_data.get("result", input_data.get("status", True))
            return not bool(result)
        return True

    def _apply_data_mapping(self, input_data: Dict[str, Any]) -> Any:
        """应用数据映射"""
        mapping_json = self.get_param("数据映射", "")
        
        if not mapping_json:
            # 没有映射规则，直接返回原始数据
            return input_data
        
        try:
            # 解析映射规则
            mapping_rules = json.loads(mapping_json)
            
            # 如果有映射规则，应用映射
            if isinstance(mapping_rules, dict):
                from core.data_mapping import DataMapper, DataMappingRule
                
                mapper = DataMapper()
                for source_field, target_field in mapping_rules.items():
                    rule = DataMappingRule(
                        source_field=source_field,
                        target_field=target_field
                    )
                    mapper.add_rule(rule)
                
                return mapper.map(input_data)
            
            return input_data
        except (json.JSONDecodeError, Exception):
            # 解析失败，返回原始数据
            return input_data

    def _is_data_unchanged(self, data: Any) -> bool:
        """检查数据是否未变化"""
        if self._last_sent_data is None:
            return False
        
        # 简单比较，对于字典使用字符串化比较
        if isinstance(data, dict) and isinstance(self._last_sent_data, dict):
            return json.dumps(data, sort_keys=True) == json.dumps(self._last_sent_data, sort_keys=True)
        
        return data == self._last_sent_data

    def _format_data(self, data: Any, format_type: str) -> Any:
        """格式化数据"""
        # 支持中英文格式名称
        format_lower = format_type.lower()
        
        if format_lower == "json":
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)
            return json.dumps({"data": data}, ensure_ascii=False)
        elif format_lower == "ascii" or format_lower == "字符串":
            # 使用UTF-8编码以支持中文字符
            if isinstance(data, str):
                return data.encode("utf-8")
            return str(data).encode("utf-8")
        elif format_lower == "hex":
            if isinstance(data, str):
                return data.encode("utf-8").hex().upper()
            elif isinstance(data, bytes):
                return data.hex().upper()
            return str(data).encode("utf-8").hex().upper()
        elif format_lower == "binary" or format_lower == "二进制":
            if isinstance(data, str):
                return data.encode("utf-8")
            elif isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False).encode("utf-8")
            return str(data).encode("utf-8")
        else:
            return str(data)

    def reset(self):
        """重置"""
        self._send_count = 0
        self._fail_count = 0
        self._last_send_time = 0.0
        self._last_sent_data = None
        self._data_mapper = None
        super().reset()


@ToolRegistry.register
class ReceiveDataTool(ToolBase):
    """接收数据工具（重构版）

    从外部设备接收数据。通过连接ID使用已有的通讯连接，
    专注于数据接收和解析，不负责连接管理。

    功能特性:
    - 使用已有连接：通过连接ID引用ConnectionManager中的连接
    - 多种数据格式解析：JSON、String、Int、Float、Hex、Bytes
    - 数据提取规则：支持从复杂数据中提取特定字段
    - 超时控制：可配置的接收超时时间

    端口:
    - 输出端口: OutputData (接收的数据)
    """

    tool_name = "接收数据"
    tool_category = "Communication"
    tool_description = "从外部设备接收数据，通过连接ID使用已有连接"

    def __init__(self, name: str = None):
        super().__init__(name)
        self._receive_count = 0
        self._fail_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0

    def _init_params(self):
        """初始化参数
        
        只在参数不存在时才设置默认值，避免覆盖用户设置
        优化：延迟加载连接列表，避免初始化时卡顿
        """
        # 只在参数不存在或为空时设置默认值
        current_connection = self._params.get("连接ID", "")
        # 延迟加载：初始化时设置提示选项
        if not current_connection:
            self.set_param("连接ID", "",
                          param_type="enum",
                          options=["点击刷新获取连接列表"],
                          description="选择已有的通讯连接ID（点击下拉框刷新）")
        else:
            # 只更新选项列表，不覆盖值（延迟加载）
            self._params[f"__options_连接ID"] = ["点击刷新获取连接列表"]

        # 接收配置 - 只在不存在时设置默认值
        if "输出格式" not in self._params:
            self.set_param("输出格式", "JSON",
                          param_type="enum",
                          options=["JSON", "字符串", "整数", "浮点数", "HEX", "字节"],
                          description="接收数据的解析格式")
        if "超时时间" not in self._params:
            self.set_param("超时时间", 5.0,
                          description="接收超时时间（秒）")
        if "缓冲区大小" not in self._params:
            self.set_param("缓冲区大小", 4096,
                          description="接收缓冲区大小（字节）")

        # 数据提取规则 - 只在不存在时设置默认值
        if "数据提取规则" not in self._params:
            self.set_param("数据提取规则", None,
                          param_type="extraction_rule",
                          description='配置Modbus TCP数据提取规则')

    def _on_param_changed(self, key: str, old_value: Any, new_value: Any):
        """参数变更回调
        
        当连接ID参数被点击时，刷新连接列表
        """
        super()._on_param_changed(key, old_value, new_value)
        
        if key == "连接ID":
            # 检查是否需要刷新连接列表
            if new_value == "点击刷新获取连接列表" or old_value == "点击刷新获取连接列表":
                self._logger.info("【_on_param_changed】刷新连接列表")
                self._refresh_connection_options()
    
    def _refresh_connection_options(self):
        """刷新连接列表选项"""
        try:
            available_connections = self._get_available_connections()
            self._logger.info(f"【_refresh_connection_options】获取到 {len(available_connections)} 个连接")
            
            if available_connections:
                self._params["__options_连接ID"] = available_connections
            else:
                self._params["__options_连接ID"] = ["暂无可用连接"]
        except Exception as e:
            self._logger.error(f"【_refresh_connection_options】刷新连接列表失败: {e}")
            self._params["__options_连接ID"] = ["刷新失败，请重试"]

    def set_param(self, key: str, value: Any, **kwargs):
        """设置参数，特殊处理数据提取规则"""
        # 特殊处理数据提取规则参数
        if key == "数据提取规则":
            if value is not None and not isinstance(value, (dict, type(None))):
                # 如果是DataExtractionRule对象，转换为字典
                try:
                    from tools.communication.data_extraction_rules import DataExtractionRule
                    if isinstance(value, DataExtractionRule):
                        value = value.to_dict()
                except ImportError:
                    pass
        
        super().set_param(key, value, **kwargs)
    
    def get_param(self, key: str, default=None):
        """获取参数，特殊处理数据提取规则"""
        value = super().get_param(key, default)
        
        if key == "数据提取规则" and value is not None:
            if isinstance(value, dict):
                # 从字典还原为DataExtractionRule对象
                try:
                    from tools.communication.data_extraction_rules import DataExtractionRule
                    return DataExtractionRule.from_dict(value)
                except Exception as e:
                    self._logger.warning(f"还原数据提取规则失败: {e}")
                    return default
        
        return value
    
    def _check_input(self) -> bool:
        """检查输入数据有效性
        
        接收数据工具不需要输入图像数据，
        它从外部连接接收数据，所以总是返回True
        """
        return True

    def _get_available_connections(self) -> List[str]:
        """获取可用的连接列表（统一格式：device_id: display_name）"""
        try:
            conn_manager = _get_comm_manager()
            connections = conn_manager.get_available_connections()
            result = []
            for conn in connections:
                if conn.get("connected"):
                    device_id = conn.get("device_id", conn.get("name", ""))
                    display_name = conn.get("display_name", "")
                    if device_id and display_name:
                        result.append(f"{device_id}: {display_name}")
                    elif display_name:
                        result.append(display_name)
            self._logger.debug(f"接收数据工具获取到 {len(result)} 个可用连接")
            return result
        except Exception as e:
            self._logger.error(f"获取可用连接列表失败: {e}")
            return []

    def _get_connection_by_display_name(self, display_name: str) -> Optional[Any]:
        """根据显示名称获取连接
        
        支持多种格式：
        1. 完整的显示格式：device_id: display_name
        2. 只有display_name
        3. 方括号格式：[device_id] display_name
        """
        try:
            conn_manager = _get_comm_manager()
            connections = conn_manager.get_available_connections()
            
            self._logger.debug(f"尝试根据显示名称查找连接: {display_name}")
            
            # 尝试直接匹配 display_name
            for conn in connections:
                conn_display_name = conn.get("display_name", "")
                if conn_display_name == display_name:
                    device_id = conn.get("device_id", conn.get("name", ""))
                    self._logger.debug(f"找到匹配，使用 device_id: {device_id}")
                    return conn_manager.get_connection(device_id)
            
            # 尝试解析 device_id: display_name 格式
            if ": " in display_name:
                parts = display_name.split(": ", 1)
                if len(parts) == 2:
                    device_id = parts[0]
                    self._logger.debug(f"尝试使用解析的 device_id 查找: {device_id}")
                    for conn in connections:
                        if conn.get("device_id") == device_id:
                            self._logger.debug(f"找到匹配的 device_id: {device_id}")
                            return conn_manager.get_connection(device_id)
            
            # 尝试解析 [device_id] display_name 格式
            if display_name.startswith("[") and "]" in display_name:
                parts = display_name.split("]", 1)
                if len(parts) == 2:
                    device_id = parts[0][1:]  # 去掉开头的 [
                    self._logger.debug(f"尝试使用方括号格式的 device_id 查找: {device_id}")
                    for conn in connections:
                        if conn.get("device_id") == device_id:
                            self._logger.debug(f"找到匹配的 device_id: {device_id}")
                            return conn_manager.get_connection(device_id)
            
            self._logger.warning(f"未找到匹配的连接: {display_name}")
            return None
        except Exception as e:
            self._logger.error(f"根据显示名称获取连接失败: {e}")
            import traceback
            self._logger.error(traceback.format_exc())
            return None

    def _run_impl(self):
        """执行接收逻辑（重构版）"""
        try:
            self._logger.info(f"[{self.name}] 开始执行接收数据...")
            
            # 调试：查看所有参数
            all_params = self.get_all_params()
            self._logger.debug(f"工具所有参数: {list(all_params.keys())}")
            
            # 1. 检查连接ID - 尝试多个可能的参数名
            connection_id = ""
            
            # 尝试不同的参数名（处理可能的参数名不一致问题）
            possible_names = ["连接ID", "目标连接", "connection_id", "target_connection"]
            for name in possible_names:
                value = all_params.get(name, "")
                if value:
                    connection_id = value
                    self._logger.debug(f"使用参数名 '{name}' 获取连接: {connection_id}")
                    break
            
            # 如果没有找到，使用默认的 get_param
            if not connection_id:
                connection_id = self.get_param("连接ID", "")
            
            self._logger.debug(f"最终连接ID: '{connection_id}'")
            self._logger.debug(f"连接ID类型: {type(connection_id)}")
            self._logger.debug(f"连接ID长度: {len(connection_id) if connection_id else 0}")
            
            if not connection_id:
                self._logger.error("未选择通讯连接")
                self._logger.error(f"可用参数: {list(all_params.keys())}")
                return {
                    "status": False,
                    "message": "未选择通讯连接，请在属性面板中选择已建立的连接",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 2. 获取已有连接
            conn_manager = _get_comm_manager()
            
            # 首先尝试直接使用connection_id查找
            connection = conn_manager.get_connection(connection_id)
            self._logger.debug(f"直接查找连接结果: {connection is not None}")
            
            # 如果找不到，尝试解析 device_id: display_name 格式，提取device_id
            if not connection and ": " in connection_id:
                parts = connection_id.split(": ", 1)
                if len(parts) == 2:
                    device_id = parts[0]
                    self._logger.debug(f"尝试使用device_id查找: {device_id}")
                    connection = conn_manager.get_connection(device_id)
                    self._logger.debug(f"使用device_id查找结果: {connection is not None}")

            # 如果还找不到，尝试使用display_name查找
            if not connection:
                connection = self._get_connection_by_display_name(connection_id)
                self._logger.debug(f"通过display_name查找连接结果: {connection is not None}")

            if not connection:
                self._logger.error(f"未找到连接: {connection_id}")
                return {
                    "status": False,
                    "message": f"未找到连接 {connection_id}，请先在通讯配置中建立连接",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 3. 检查连接状态
            self._logger.debug(f"连接状态检查 - is_connected: {connection.is_connected}")
            if not connection.is_connected:
                self._logger.error(f"连接 {connection.name} 未建立")
                return {
                    "status": False,
                    "message": f"连接 {connection.name} 未建立，请先连接",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }
            
            # 4. 获取协议实例
            protocol_instance = connection.protocol_instance
            self._logger.debug(f"协议实例: {protocol_instance is not None}")
            if not protocol_instance:
                self._logger.error("协议实例不存在")
                return {
                    "status": False,
                    "message": "协议实例不存在",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }
            
            # 5. 检查协议实例连接状态
            if hasattr(protocol_instance, 'is_connected') and not protocol_instance.is_connected():
                self._logger.error("协议实例未连接")
                return {
                    "status": False,
                    "message": "协议实例未连接",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 6. 检查接收接口
            if not hasattr(protocol_instance, 'receive'):
                self._logger.error(f"连接 {connection.name} 无接收接口")
                return {
                    "status": False,
                    "message": f"连接 {connection.name} 无接收接口",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 7. 从已有连接接收数据
            self._logger.info(f"正在从 {connection.name} 接收数据...")
            timeout = self.get_param("超时时间", 5.0)
            self._logger.debug(f"接收超时: {timeout}秒")
            raw_data = protocol_instance.receive(timeout)
            self._logger.debug(f"接收到的原始数据: {raw_data}")

            if raw_data is None:
                self._fail_count += 1
                self._logger.warning("接收超时，未收到数据")
                return {
                    "status": False,
                    "message": "接收超时，未收到数据",
                    "接收成功次数": self._receive_count,
                    "接收失败次数": self._fail_count
                }

            # 8. 解析数据
            format_type = self.get_param("输出格式", "JSON")
            self._logger.debug(f"解析数据，格式: {format_type}")
            parsed_data = self._parse_data(raw_data, format_type)
            self._logger.debug(f"解析后的数据: {parsed_data}")

            # 9. 应用数据提取规则
            extracted_data = self._extract_data(parsed_data)
            self._logger.debug(f"提取后的数据: {extracted_data}")

            # 10. 更新统计
            self._receive_count += 1
            self._last_received_data = extracted_data
            self._last_receive_time = time.time()

            # 11. 构建输出
            result = {
                "status": True,
                "message": f"从 {connection.name} 接收到数据",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count,
                "接收数据": extracted_data,
                "OutputStatus": True,
                "OutputData": extracted_data
            }

            self._logger.info(f"接收数据成功: {extracted_data}")
            return result

        except Exception as e:
            self._fail_count += 1
            self._logger.error(f"接收异常: {e}", exc_info=True)
            return {
                "status": False,
                "message": f"接收异常：{str(e)}",
                "接收成功次数": self._receive_count,
                "接收失败次数": self._fail_count
            }

    def _parse_data(self, raw_data: Any, format_type: str) -> Any:
        """解析接收到的数据"""
        try:
            # 支持中英文格式名称
            format_lower = format_type.lower()
            
            if format_lower == "json":
                if isinstance(raw_data, bytes):
                    return json.loads(raw_data.decode('utf-8'))
                elif isinstance(raw_data, str):
                    return json.loads(raw_data)
                return raw_data

            elif format_lower == "string" or format_lower == "字符串":
                if isinstance(raw_data, bytes):
                    return raw_data.decode('utf-8', errors='replace')
                return str(raw_data)

            elif format_lower == "int" or format_lower == "整数":
                if isinstance(raw_data, bytes):
                    return int(raw_data.decode('utf-8').strip())
                return int(str(raw_data).strip())

            elif format_lower == "float" or format_lower == "浮点数":
                if isinstance(raw_data, bytes):
                    return float(raw_data.decode('utf-8').strip())
                return float(str(raw_data).strip())

            elif format_lower == "hex":
                if isinstance(raw_data, bytes):
                    return raw_data.hex().upper()
                return str(raw_data).encode('utf-8').hex().upper()

            elif format_lower == "bytes" or format_lower == "字节":
                if isinstance(raw_data, str):
                    return raw_data.encode('utf-8')
                return raw_data

            else:
                return raw_data

        except Exception as e:
            return raw_data

    def _extract_data(self, data: Any) -> Any:
        """根据规则提取数据"""
        extract_rules = self.get_param("数据提取规则", None)

        if not extract_rules:
            return data

        try:
            # 检查是否是新的 DataExtractionRule 格式
            if isinstance(extract_rules, dict) and "rule_type" in extract_rules:
                from tools.communication.data_extraction_rules import DataExtractionRule
                rule = DataExtractionRule.from_dict(extract_rules)
                return rule.extract(data)
            
            # 兼容旧格式（JSON字符串）
            if isinstance(extract_rules, str):
                import json
                rules = json.loads(extract_rules)

                if not isinstance(data, dict):
                    return data

                result = {}
                for target_field, source_path in rules.items():
                    value = self._get_nested_value(data, source_path)
                    if value is not None:
                        result[target_field] = value

                return result if result else data

            return data

        except Exception as e:
            self._logger.warning(f"数据提取失败: {e}")
            return data

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """获取嵌套字段值"""
        if not isinstance(data, dict):
            return None

        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def reset(self):
        """重置"""
        self._receive_count = 0
        self._fail_count = 0
        self._last_received_data = None
        self._last_receive_time = 0.0
        self._received_data = None
        super().reset()


# 兼容性别名
EnhancedSendData = SendDataTool
EnhancedReceiveData = ReceiveDataTool


# 导出
__all__ = [
    'SendDataTool',
    'ReceiveDataTool',
    'EnhancedSendData',
    'EnhancedReceiveData'
]
