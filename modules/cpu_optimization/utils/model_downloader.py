#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO26模型下载管理器

自动下载和管理YOLO26预训练模型

Author: Vision System Team
Date: 2026-01-26
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ModelDownloader")

# YOLO26模型下载URL（使用Ultralytics官方仓库）
MODEL_DOWNLOAD_URLS = {
    "yolo26n": "https://github.com/ultralytics/ultralytics/raw/main/weights/yolo26n.pt",
    "yolo26s": "https://github.com/ultralytics/ultralytics/raw/main/weights/yolo26s.pt",
    "yolo26m": "https://github.com/ultralytics/ultralytics/raw/main/weights/yolo26m.pt",
    "yolo26l": "https://github.com/ultralytics/ultralytics/raw/main/weights/yolo26l.pt",
    "yolo26x": "https://github.com/ultralytics/ultralytics/raw/main/weights/yolo26x.pt",
}

# 模型大小（MB）
MODEL_SIZES = {
    "yolo26n": 180,
    "yolo26s": 400,
    "yolo26m": 800,
    "yolo26l": 1600,
    "yolo26x": 3200,
}


class YOLO26ModelDownloader:
    """YOLO26模型下载器"""

    def __init__(self, models_dir: str = "modules/cpu_optimization/models"):
        """
        初始化下载器

        Args:
            models_dir: 模型保存目录
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def get_model_path(self, model_type: str) -> Optional[Path]:
        """获取模型文件路径"""
        if model_type == "custom":
            return None

        # YOLO26模型文件名
        model_filename = f"{model_type}.pt"
        model_path = self.models_dir / model_filename

        return model_path if model_path.exists() else None

    def is_model_available(self, model_type: str) -> bool:
        """检查模型是否可用"""
        model_path = self.get_model_path(model_type)
        return model_path is not None and model_path.exists()

    def get_model_info(self, model_type: str) -> dict:
        """获取模型信息"""
        return {
            "type": model_type,
            "size_mb": MODEL_SIZES.get(model_type, 0),
            "available": self.is_model_available(model_type),
            "path": (
                str(self.get_model_path(model_type))
                if self.get_model_path(model_type)
                else None
            ),
        }

    def download_model(self, model_type: str, progress_callback=None) -> bool:
        """
        下载模型

        Args:
            model_type: 模型类型
            progress_callback: 进度回调函数

        Returns:
            是否下载成功
        """
        if model_type == "custom":
            logger.warning("自定义模型不需要下载")
            return False

        if model_type not in MODEL_DOWNLOAD_URLS:
            logger.error(f"不支持的模型类型: {model_type}")
            return False

        url = MODEL_DOWNLOAD_URLS[model_type]
        model_filename = f"{model_type}.pt"
        model_path = self.models_dir / model_filename

        # 检查是否已存在
        if model_path.exists():
            logger.info(f"模型已存在: {model_path}")
            return True

        try:
            import urllib.request

            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    progress = block_num * block_size / total_size * 100
                    progress_callback(progress)

            logger.info(
                f"开始下载模型: {model_type} ({MODEL_SIZES[model_type]}MB)"
            )
            logger.info(f"下载URL: {url}")
            urllib.request.urlretrieve(
                url, model_path, reporthook=report_progress
            )

            logger.info(f"模型下载完成: {model_path}")
            return True

        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            return False

    def list_available_models(self) -> list:
        """列出所有可用的模型"""
        return [
            {
                "type": model_type,
                "size_mb": MODEL_SIZES[model_type],
                "available": self.is_model_available(model_type),
            }
            for model_type in MODEL_SIZES.keys()
        ]


def get_downloader(models_dir: str = "models") -> YOLO26ModelDownloader:
    """获取模型下载器实例"""
    return YOLO26ModelDownloader(models_dir)


if __name__ == "__main__":
    downloader = get_downloader()

    print("=" * 60)
    print("  YOLO26 模型下载管理器")
    print("=" * 60)

    models = downloader.list_available_models()
    print("\n可用的模型:")
    for i, model in enumerate(models, 1):
        status = "✓" if model["available"] else "✗"
        print(f"  {i}. {model['type']:10} - {model['size_mb']:5}MB [{status}]")

    print("\n使用方法:")
    print("  python model_downloader.py download <model_type>")
    print("\n示例:")
    print("  python model_downloader.py download yolo26n")
