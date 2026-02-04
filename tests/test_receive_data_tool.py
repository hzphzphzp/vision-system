#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ReceiveDataTool重构后的功能

Author: AI Agent
Date: 2026-02-04
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.communication.enhanced_communication import ReceiveDataTool


def test_receive_data_tool_creation():
    """测试接收数据工具创建"""
    tool = ReceiveDataTool("test_recv")
    assert tool is not None
    assert tool.tool_name == "接收数据"


def test_receive_data_requires_connection():
    """测试接收数据需要选择连接"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "")
    
    result = tool._run_impl()
    
    assert result["status"] == False
    assert "未选择" in result["message"] and "连接" in result["message"]


def test_receive_data_with_mock():
    """测试使用模拟连接接收数据"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    
    # 模拟连接
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b'{"status": "ok"}'
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert "接收数据" in result


def test_receive_data_connection_not_found():
    """测试连接不存在时的处理"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "non_existent_conn")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = None
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "未找到连接" in result["message"]


def test_receive_data_connection_not_connected():
    """测试连接未连接时的处理"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = False
        mock_conn.name = "test_connection"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=False,
            protocol_instance=mock_conn,
            name="test_connection"
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "未建立" in result.get("message", "") or "未连接" in result.get("message", "")


def test_receive_data_format_json():
    """测试JSON格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "json")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b'{"status": "ok", "value": 42}'
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"]["status"] == "ok"
        assert result["接收数据"]["value"] == 42


def test_receive_data_format_string():
    """测试字符串格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"Hello World"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"] == "Hello World"


def test_receive_data_format_int():
    """测试整型格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "int")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"123"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"] == 123


def test_receive_data_format_float():
    """测试浮点型格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "float")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"3.14"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"] == 3.14


def test_receive_data_format_hex():
    """测试HEX格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "hex")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"AB"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"] == "4142"


def test_receive_data_format_bytes():
    """测试字节格式数据接收"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "bytes")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"\x00\x01\x02\x03"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"] == b"\x00\x01\x02\x03"


def test_receive_data_timeout():
    """测试接收超时"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    tool.set_param("超时时间", 1.0)
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = None  # 模拟超时
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert "接收超时" in result["message"]


def test_receive_data_with_extraction_rule():
    """测试数据提取规则"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "json")
    tool.set_param("数据提取规则", '{"value": "data.value"}')
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b'{"data": {"value": 999}}'
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert result["接收数据"]["value"] == 999


def test_receive_data_exception_handling():
    """测试异常处理"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.side_effect = Exception("Connection error")
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == False
        assert result["接收失败次数"] == 1


def test_receive_data_reset():
    """测试重置功能"""
    tool = ReceiveDataTool("test_recv")
    tool._receive_count = 10
    tool._fail_count = 5
    tool._received_data = {"test": "data"}
    
    tool.reset()
    
    assert tool._receive_count == 0
    assert tool._fail_count == 0
    assert tool._received_data is None


def test_receive_data_outputs_to_downstream():
    """测试输出数据到下游端口"""
    tool = ReceiveDataTool("test_recv")
    tool.set_param("连接ID", "test_conn")
    tool.set_param("输出格式", "string")
    
    with patch("tools.communication.enhanced_communication._get_comm_manager") as mock_get_mgr:
        mock_conn = Mock()
        mock_conn.is_connected.return_value = True
        mock_conn.receive.return_value = b"test value"
        
        mock_mgr = Mock()
        mock_mgr.get_connection.return_value = Mock(
            is_connected=True,
            protocol_instance=mock_conn
        )
        mock_get_mgr.return_value = mock_mgr
        
        result = tool._run_impl()
        
        assert result["status"] == True
        assert "OutputData" in result
        assert result["OutputData"] == "test value"
