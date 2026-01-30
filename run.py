#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision System 启动脚本

这是Vision System的主启动入口，提供简单的命令行界面来选择启动模式。

Usage:
    python run.py [--gui] [--demo] [--test]

Options:
    --gui     启动图形界面（默认）
    --demo    运行演示程序
    --test    运行测试套件
    --help    显示帮助信息
"""

import argparse
import logging
import os
import sys

# 设置protobuf兼容模式（解决paddlepaddle兼容性问题）
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("vision_system.log", encoding="utf-8"),
        ],
    )


def start_gui():
    """启动GUI界面"""
    try:
        from PyQt5.QtWidgets import QApplication

        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        print("Vision System GUI 已启动")
        print("提示：")
        print("  - 从右侧工具库拖拽工具到算法编辑器")
        print("  - 连接工具输入输出端口构建处理流程")
        print("  - 双击工具编辑参数")
        print("  - 按F5运行单次检测")
        print("  - 按F6开始连续运行")

        sys.exit(app.exec_())

    except ImportError as e:
        print(f"GUI启动失败，缺少依赖: {e}")
        print("请运行: pip install PyQt5")
        return False
    except Exception as e:
        print(f"GUI启动出现异常: {e}")
        return False

    return True


def run_demo():
    """运行演示程序"""
    try:
        from professional_app import main as demo_main

        print("运行Vision System演示程序...")
        demo_main()
        return True

    except Exception as e:
        print(f"演示程序运行失败: {e}")
        return False


def run_tests():
    """运行测试套件"""
    try:
        import subprocess

        print("运行Vision System测试套件...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=project_root,
        )

        return result.returncode == 0

    except ImportError:
        print("测试需要pytest，请运行: pip install pytest")
        return False
    except Exception as e:
        print(f"测试运行失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Vision System - 专业视觉检测系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run.py              # 启动GUI（默认）
    python run.py --gui         # 启动GUI
    python run.py --demo        # 运行演示
    python run.py --test        # 运行测试
        """,
    )

    parser.add_argument(
        "--gui", action="store_true", help="启动图形界面（默认模式）"
    )
    parser.add_argument("--demo", action="store_true", help="运行演示程序")
    parser.add_argument("--test", action="store_true", help="运行测试套件")
    parser.add_argument(
        "--version", action="version", version="Vision System 1.0.0"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging()
    logger = logging.getLogger("RunScript")

    print("=" * 60)
    print("Vision System - 专业视觉检测系统 v1.0.0")
    print("=" * 60)

    # 如果没有指定参数，默认启动GUI
    if not any([args.gui, args.demo, args.test]):
        args.gui = True

    success = False

    if args.demo:
        logger.info("启动演示模式")
        success = run_demo()
    elif args.test:
        logger.info("启动测试模式")
        success = run_tests()
    else:
        logger.info("启动GUI模式")
        success = start_gui()

    if success:
        print("\n程序执行完成")
        sys.exit(0)
    else:
        print("\n程序执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
