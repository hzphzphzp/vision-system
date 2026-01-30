#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供集中的配置管理功能，支持从文件加载配置、运行时修改配置、配置验证等。

Author: Vision System Team
Date: 2026-01-27
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

import yaml

# 配置文件路径
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs"
)
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_PATH, "config.yaml")
DEFAULT_CONFIG_FILE_JSON = os.path.join(DEFAULT_CONFIG_PATH, "config.json")


@dataclass
class ConfigManager:
    """
    配置管理器
    """

    config_path: str = DEFAULT_CONFIG_PATH
    config_file: str = DEFAULT_CONFIG_FILE
    _config: Dict[str, Any] = field(default_factory=dict, init=False)
    _logger: logging.Logger = field(init=False)

    def __post_init__(self):
        """
        初始化配置管理器
        """
        self._logger = logging.getLogger("ConfigManager")
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self):
        """
        确保配置目录存在
        """
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
            self._logger.info(f"创建配置目录: {self.config_path}")

    def _load_config(self):
        """
        加载配置文件
        """
        # 尝试加载YAML配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f)
                self._logger.info(f"加载配置文件: {self.config_file}")
                return
            except Exception as e:
                self._logger.error(f"加载YAML配置失败: {e}")

        # 尝试加载JSON配置
        if os.path.exists(DEFAULT_CONFIG_FILE_JSON):
            try:
                with open(
                    DEFAULT_CONFIG_FILE_JSON, "r", encoding="utf-8"
                ) as f:
                    self._config = json.load(f)
                self._logger.info(f"加载配置文件: {DEFAULT_CONFIG_FILE_JSON}")
                return
            except Exception as e:
                self._logger.error(f"加载JSON配置失败: {e}")

        # 使用默认配置
        self._config = self._get_default_config()
        self._logger.info("使用默认配置")
        # 保存默认配置
        self.save_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            "system": {
                "name": "Vision System",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
                "max_concurrent_tools": 10,
            },
            "camera": {
                "default_id": 0,
                "fps": 30,
                "width": 640,
                "height": 480,
                "auto_exposure": True,
                "auto_gain": True,
            },
            "image_processing": {
                "default_kernel_size": 3,
                "default_blur_size": 5,
                "default_threshold": 128,
                "default_min_area": 100,
                "default_max_area": 10000,
                "default_sensitivity": 0.5,
            },
            "ocr": {
                "language": "ch_sim",
                "min_confidence": 0.5,
                "text_only": True,
                "skip_special": True,
            },
            "object_detection": {
                "model_path": "models/yolo26s.pt",
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "max_det": 1000,
            },
            "performance": {
                "enable_polars": True,
                "enable_gpu": False,
                "batch_size": 1,
                "enable_cache": True,
                "cache_size": 100,
            },
            "paths": {
                "templates": "templates",
                "models": "models",
                "output": "output",
                "logs": "logs",
            },
            "communication": {
                "default_timeout": 5.0,
                "default_port": 8080,
                "buffer_size": 4096,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值

        Returns:
            是否设置成功
        """
        keys = key.split(".")
        config = self._config

        # 遍历键路径，创建不存在的嵌套字典
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                self._logger.error(f"配置键 {'.'.join(keys[:i+1])} 不是字典")
                return False
            config = config[k]

        # 设置最终值
        config[keys[-1]] = value
        self._logger.info(f"设置配置: {key} = {value}")
        return True

    def save_config(self, config_file: str = None) -> bool:
        """
        保存配置到文件

        Args:
            config_file: 配置文件路径，默认为当前配置文件

        Returns:
            是否保存成功
        """
        target_file = config_file or self.config_file

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(target_file), exist_ok=True)

            # 根据文件扩展名选择格式
            ext = os.path.splitext(target_file)[1].lower()

            if ext in [".yaml", ".yml"]:
                with open(target_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self._config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                    )
            elif ext == ".json":
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            else:
                self._logger.error(f"不支持的配置文件格式: {ext}")
                return False

            self._logger.info(f"保存配置到: {target_file}")
            return True
        except Exception as e:
            self._logger.error(f"保存配置失败: {e}")
            return False

    def reload_config(self) -> bool:
        """
        重新加载配置

        Returns:
            是否加载成功
        """
        try:
            self._load_config()
            self._logger.info("重新加载配置成功")
            return True
        except Exception as e:
            self._logger.error(f"重新加载配置失败: {e}")
            return False

    def get_full_config(self) -> Dict[str, Any]:
        """
        获取完整配置

        Returns:
            完整配置字典
        """
        return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        更新配置

        Args:
            config: 配置字典

        Returns:
            是否更新成功
        """
        try:
            self._update_recursive(self._config, config)
            self._logger.info("更新配置成功")
            return True
        except Exception as e:
            self._logger.error(f"更新配置失败: {e}")
            return False

    def _update_recursive(
        self, target: Dict[str, Any], source: Dict[str, Any]
    ):
        """
        递归更新配置

        Args:
            target: 目标配置
            source: 源配置
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._update_recursive(target[key], value)
            else:
                target[key] = value

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            配置是否有效
        """
        try:
            # 验证必要的配置项
            required_sections = [
                "system",
                "camera",
                "image_processing",
                "paths",
            ]

            for section in required_sections:
                if section not in self._config:
                    self._logger.error(f"缺少必要的配置部分: {section}")
                    return False

            # 验证路径配置
            paths = self._config.get("paths", {})
            for path_key, path_value in paths.items():
                if not os.path.isabs(path_value):
                    # 相对路径，转换为绝对路径
                    abs_path = os.path.join(
                        os.path.dirname(
                            os.path.dirname(os.path.abspath(__file__))
                        ),
                        path_value,
                    )
                    paths[path_key] = abs_path
                    # 确保目录存在
                    os.makedirs(abs_path, exist_ok=True)

            self._logger.info("配置验证成功")
            return True
        except Exception as e:
            self._logger.error(f"配置验证失败: {e}")
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值

    Args:
        key: 配置键
        default: 默认值

    Returns:
        配置值
    """
    return config_manager.get(key, default)


def set_config(key: str, value: Any) -> bool:
    """
    设置配置值

    Args:
        key: 配置键
        value: 配置值

    Returns:
        是否设置成功
    """
    return config_manager.set(key, value)


def save_config(config_file: str = None) -> bool:
    """
    保存配置

    Args:
        config_file: 配置文件路径

    Returns:
        是否保存成功
    """
    return config_manager.save_config(config_file)


def reload_config() -> bool:
    """
    重新加载配置

    Returns:
        是否加载成功
    """
    return config_manager.reload_config()


def get_full_config() -> Dict[str, Any]:
    """
    获取完整配置

    Returns:
        完整配置
    """
    return config_manager.get_full_config()


def update_config(config: Dict[str, Any]) -> bool:
    """
    更新配置

    Args:
        config: 配置字典

    Returns:
        是否更新成功
    """
    return config_manager.update_config(config)


def validate_config() -> bool:
    """
    验证配置

    Returns:
        配置是否有效
    """
    return config_manager.validate_config()


if __name__ == "__main__":
    # 测试配置管理器
    print("测试配置管理器...")

    # 获取配置
    print(f"系统名称: {get_config('system.name')}")
    print(f"相机默认ID: {get_config('camera.default_id')}")
    print(f"默认阈值: {get_config('image_processing.default_threshold')}")

    # 设置配置
    print("\n设置配置...")
    set_config("system.debug", True)
    set_config("camera.default_id", 1)

    # 获取更新后的配置
    print(f"\n更新后 - 调试模式: {get_config('system.debug')}")
    print(f"更新后 - 相机默认ID: {get_config('camera.default_id')}")

    # 保存配置
    print("\n保存配置...")
    save_config()

    # 验证配置
    print("\n验证配置...")
    validate_config()

    print("\n配置管理器测试完成！")
