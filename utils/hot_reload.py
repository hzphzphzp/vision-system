#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热重载功能实现

提供文件系统监控和模块自动重载功能，提高开发效率。

Author: Vision System Team
Date: 2026-01-27
"""

import importlib
import os
import sys
import threading
import time
from typing import Callable, Dict, List, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class HotReloadEventHandler(FileSystemEventHandler):
    """文件系统事件处理器"""

    def __init__(self, callback: Callable[[List[str]], None]):
        """
        初始化事件处理器

        Args:
            callback: 文件变化时的回调函数
        """
        self.callback = callback
        self.changed_files: Set[str] = set()
        self.last_notify_time = 0
        self.notify_interval = 0.5  # 通知间隔，避免频繁触发

    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if not event.is_directory and event.src_path.endswith(".py"):
            self.changed_files.add(event.src_path)
            self._notify_if_needed()

    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        if not event.is_directory and event.src_path.endswith(".py"):
            self.changed_files.add(event.src_path)
            self._notify_if_needed()

    def _notify_if_needed(self):
        """如果需要，通知文件变化"""
        current_time = time.time()
        if current_time - self.last_notify_time >= self.notify_interval:
            changed_files = list(self.changed_files)
            self.changed_files.clear()
            self.last_notify_time = current_time
            self.callback(changed_files)


class HotReloadManager:
    """热重载管理器"""

    def __init__(self, paths: List[str] = None):
        """
        初始化热重载管理器

        Args:
            paths: 需要监控的路径列表
        """
        self.paths = paths or [os.getcwd()]
        self.observer = Observer()
        self.event_handler = HotReloadEventHandler(self._on_files_changed)
        self.is_running = False
        self.reload_callbacks: List[Callable] = []
        self.modules_to_reload: Dict[str, str] = {}

        # 初始化模块路径映射
        self._initialize_module_mapping()

    def _initialize_module_mapping(self):
        """初始化模块路径映射（优化版：只监控指定路径）"""
        # 只遍历需要监控的路径，而不是整个sys.path
        for path in self.paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(".py") and not file.startswith("__"):
                            module_path = os.path.join(root, file)
                            # 计算相对于项目根目录的模块名
                            relative_path = os.path.relpath(module_path, path)
                            module_name = relative_path.replace(os.sep, ".")[:-3]
                            # 添加项目前缀
                            parent_dir = os.path.basename(path)
                            full_module_name = f"{parent_dir}.{module_name}"
                            self.modules_to_reload[module_path] = full_module_name

    def _on_files_changed(self, changed_files: List[str]):
        """文件变化处理函数"""
        print(
            f"[热重载] 检测到文件变化: {[os.path.basename(f) for f in changed_files]}"
        )

        # 重新加载相关模块
        for file_path in changed_files:
            # 尝试多种方式查找模块
            module_names_to_try = []
            
            # 方式1：使用预计算的模块名
            if file_path in self.modules_to_reload:
                module_names_to_try.append(self.modules_to_reload[file_path])
            
            # 方式2：从文件路径推导模块名
            for path in self.paths:
                if file_path.startswith(path):
                    relative_path = os.path.relpath(file_path, path)
                    module_name = relative_path.replace(os.sep, ".")[:-3]
                    parent_dir = os.path.basename(path)
                    full_module_name = f"{parent_dir}.{module_name}"
                    if full_module_name not in module_names_to_try:
                        module_names_to_try.append(full_module_name)
                    # 也尝试不带父目录前缀的版本
                    if module_name not in module_names_to_try:
                        module_names_to_try.append(module_name)
            
            # 尝试重新加载模块
            for module_name in module_names_to_try:
                try:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                        print(f"[热重载] 重新加载模块: {module_name}")
                        break  # 成功加载后跳出
                except Exception as e:
                    print(f"[热重载] 重新加载模块失败 {module_name}: {e}")

        # 调用所有回调函数
        for callback in self.reload_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[热重载] 回调函数执行失败: {e}")

    def add_reload_callback(self, callback: Callable):
        """
        添加重载回调函数

        Args:
            callback: 重载时的回调函数
        """
        self.reload_callbacks.append(callback)

    def start(self):
        """启动热重载监控"""
        if not self.is_running:
            # 注册监控路径
            for path in self.paths:
                if os.path.exists(path):
                    self.observer.schedule(
                        self.event_handler, path, recursive=True
                    )

            # 启动观察者
            self.observer.start()
            self.is_running = True
            print(f"[热重载] 启动监控: {self.paths}")

    def stop(self):
        """停止热重载监控"""
        if self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("[热重载] 停止监控")

    def is_active(self) -> bool:
        """
        检查热重载是否活跃

        Returns:
            是否活跃
        """
        return self.is_running


def create_hot_reload_manager(paths: List[str] = None) -> HotReloadManager:
    """
    创建热重载管理器

    Args:
        paths: 需要监控的路径列表

    Returns:
        热重载管理器实例
    """
    return HotReloadManager(paths)
