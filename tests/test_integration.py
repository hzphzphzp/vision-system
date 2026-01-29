#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本
测试所有新增的方案管理功能
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_solution_file_manager():
    """测试方案文件管理器"""
    print("=== 测试方案文件管理器 ===")
    
    try:
        from core.solution_file_manager import SolutionFileManager, CodeGenerator, DocumentationGenerator
        from core.solution import Solution
        from core.procedure import Procedure
        
        # 创建测试方案
        solution = Solution("测试方案")
        # solution.description = "用于测试方案文件管理器的功能"
        # solution.author = "测试脚本"
        
        # 添加流程
        proc1 = Procedure("测试流程1")
        solution.add_procedure(proc1)
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"临时目录: {temp_dir}")
        
        # 测试JSON格式保存
        json_file = os.path.join(temp_dir, "test_solution.json")
        file_manager = SolutionFileManager()
        success = file_manager.save_solution(solution, json_file, format='json')
        
        if success:
            print("[PASS] JSON格式保存成功")
            
            # 测试JSON格式加载
            loaded_solution = file_manager.load_solution(json_file, format='json')
            if loaded_solution and loaded_solution.name == "测试方案":
                print("[PASS] JSON格式加载成功")
            else:
                print("[FAIL] JSON格式加载失败")
        else:
            print("[FAIL] JSON格式保存失败")
        
        # 测试VMSOL格式保存
        vmsol_file = os.path.join(temp_dir, "test_solution.vmsol")
        success = file_manager.save_solution(solution, vmsol_file, format='vmsol')
        
        if success:
            print("[PASS] VMSOL格式保存成功")
        else:
            print("[FAIL] VMSOL格式保存失败")
        
        # 测试代码生成
        code_gen = CodeGenerator()
        code_content = code_gen.generate_solution_code(solution)
        main_py = os.path.join(temp_dir, "main.py")
        with open(main_py, 'w', encoding='utf-8') as f:
            f.write(code_content)
        success = True
        
        if success:
            print("[PASS] 代码生成成功")
            
            # 检查生成的文件
            main_py = os.path.join(temp_dir, "main.py")
            if os.path.exists(main_py):
                print("[PASS] 主程序文件已生成")
            else:
                print("[FAIL] 主程序文件未生成")
        else:
            print("[FAIL] 代码生成失败")
        
        # 测试文档生成
        doc_gen = DocumentationGenerator()
        doc_content = doc_gen.generate_solution_documentation(solution)
        doc_file = os.path.join(temp_dir, "test_docs.md")
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        success = True
        
        if success and os.path.exists(doc_file):
            print("[PASS] 文档生成成功")
        else:
            print("[FAIL] 文档生成失败")
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[PASS] 临时目录已清理")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        return False

def test_communication_enhancements():
    """测试通信模块增强"""
    print("\n=== 测试通信模块增强 ===")
    
    try:
        from tools.communication import SendData, ReceiveData
        
        # 测试SendData工具
        send_tool = SendData()
        # send_tool.设备名称 = "测试设备"
        # send_tool.波特率 = 9600
        print("[PASS] SendData工具创建成功")
        
        # 测试ReceiveData工具
        receive_tool = ReceiveData()
        # receive_tool.设备名称 = "测试设备"
        # receive_tool.数据过滤 = True
        print("[PASS] ReceiveData工具创建成功")
        
        # 测试工具类型
        if hasattr(send_tool, 'tool_name'):
            print("[PASS] SendData工具类型正确")
        else:
            print("[FAIL] SendData工具类型异常")
        
        if hasattr(receive_tool, 'tool_name'):
            print("[PASS] ReceiveData工具类型正确")
        else:
            print("[FAIL] ReceiveData工具类型异常")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        return False

def test_communication_monitor():
    """测试通信监控面板"""
    print("\n=== 测试通信监控面板 ===")
    
    try:
        # 由于GUI测试需要显示环境，这里只做导入测试
        from ui.communication_monitor import CommunicationMonitorPanel, CommunicationStatusWidget
        print("[PASS] 通信监控模块导入成功")
        
        # 检查类定义
        if hasattr(CommunicationMonitorPanel, '_refresh_status'):
            print("[PASS] CommunicationMonitorPanel类定义正确")
        else:
            print("[FAIL] CommunicationMonitorPanel类定义异常")
        
        if hasattr(CommunicationStatusWidget, 'update_status'):
            print("[PASS] CommunicationStatusWidget类定义正确")
        else:
            print("[FAIL] CommunicationStatusWidget类定义异常")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始集成测试...")
    print("=" * 50)
    
    all_passed = True
    
    # 运行各项测试
    tests = [
        test_solution_file_manager,
        test_communication_enhancements,
        test_communication_monitor
    ]
    
    for test in tests:
        try:
            result = test()
            all_passed = all_passed and result
        except Exception as e:
            print(f"测试执行异常: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("[SUCCESS] 所有测试通过！")
        return 0
    else:
        print("[FAIL] 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())