#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SendDataTool重构后的功能

Author: AI Agent
Date: 2026-02-04
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.communication.enhanced_communication import SendDataTool


def test_send_data_tool_creation():
    """测试发送数据工具创建"""
    tool = SendDataTool("test_send")
    assert tool is not None
    assert tool.tool_name == "发送数据"


def test_send_data_requires_connection():
    """测试发送数据需要选择连接"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "")  # 空连接ID
    
    result = tool._run_impl()
    
    assert result["status"] == False
    assert "未选择连接" in result["message"]


def test_send_data_with_mock_connection():
    """测试使用模拟连接发送数据"""
    tool = SendDataTool("test_send")
    
    # 设置参数
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "json")
    tool.set_param("数据映射", '{"result": "status"}')
    
    # 模拟输入数据
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"result": True}
    
    # 模拟连接
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        mock_conn.send.assert_called_once()


def test_send_data_connection_not_found():
    """测试连接不存在时的处理"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "non_existent_conn")
    
    # 模拟连接管理器返回None
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = None
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "未找到连接" in result["message"]


def test_send_data_connection_not_connected():
    """测试连接未连接时的处理"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    
    # 模拟连接未连接
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = False
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "连接未建立" in result["message"]


def test_send_data_with_send_condition():
    """测试发送条件控制"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("发送条件", "成功时")  # 仅在成功时发送
    tool.set_param("数据格式", "json")
    
    # 模拟输入数据（成功状态）
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"result": True}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        # 成功时应该发送
        result = tool._run_impl()
        assert result["status"] == True
        mock_conn.send.assert_called_once()


def test_send_data_only_on_change():
    """测试仅发送变化的数据"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("仅发送变化的数据", True)
    tool.set_param("数据格式", "json")
    
    # 第一次发送
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"value": 100}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result1 = tool._run_impl()
        assert result1["status"] == True
        assert result1["message"] == "发送成功"
        
        # 相同数据再次发送
        result2 = tool._run_impl()
        assert result2["status"] == True
        assert "数据未变化" in result2["message"]
        mock_conn.send.assert_called_once()  # 只调用了一次


def test_send_data_format_json():
    """测试JSON格式数据发送"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "json")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"status": "ok", "value": 42}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        # 验证发送的是JSON字符串
        call_args = mock_conn.send.call_args[0][0]
        assert isinstance(call_args, str)
        import json
        parsed = json.loads(call_args)
        assert parsed["status"] == "ok"


def test_send_data_format_ascii():
    """测试ASCII格式数据发送"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "ascii")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"message": "Hello"}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        call_args = mock_conn.send.call_args[0][0]
        assert isinstance(call_args, bytes)


def test_send_data_format_hex():
    """测试HEX格式数据发送"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "hex")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"data": "AB"}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        call_args = mock_conn.send.call_args[0][0]
        assert isinstance(call_args, str)
        # 应该是十六进制字符串
        assert all(c in "0123456789ABCDEF" for c in call_args)


def test_send_data_format_binary():
    """测试二进制格式数据发送"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "binary")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"data": "test"}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = True
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        call_args = mock_conn.send.call_args[0][0]
        assert isinstance(call_args, bytes)


def test_send_data_send_failure():
    """测试发送失败时的处理"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "json")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"result": True}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.return_value = False  # 发送失败
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "发送失败" in result["message"]
        assert result["发送失败次数"] == 1


def test_send_data_exception_handling():
    """测试异常处理"""
    tool = SendDataTool("test_send")
    tool.set_param("连接ID", "test_conn_123")
    tool.set_param("数据格式", "json")
    
    tool._result_data = Mock()
    tool._result_data.get_all_values.return_value = {"result": True}
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.send.side_effect = Exception("Connection error")
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(protocol_instance=mock_conn)
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert result["发送失败次数"] == 1


def test_send_data_reset():
    """测试重置功能"""
    tool = SendDataTool("test_send")
    tool._send_count = 10
    tool._fail_count = 5
    tool._last_sent_data = {"test": "data"}
    
    tool.reset()
    
    assert tool._send_count == 0
    assert tool._fail_count == 0
    assert tool._last_sent_data is None
