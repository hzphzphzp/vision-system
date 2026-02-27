#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型缓存模块

提供模型单例缓存，避免重复加载模型消耗资源

Author: Vision System Team
Date: 2026-02-26
"""

import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ModelCache:
    """
    模型缓存类 - 确保同类模型只加载一次
    
    Usage:
        detector = ModelCache.get_model(
            "yolo26",
            lambda: YOLO26CPUDetector(config),
            "path/to/model.pt"
        )
    """
    
    _cache: Dict[str, Any] = {}
    _locks: Dict[str, threading.Lock] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_model(
        cls,
        model_type: str,
        factory_fn,
        model_path: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        获取缓存的模型，如果不存在则创建
        
        Args:
            model_type: 模型类型标识符 (如 "yolo26", "ocr", "template")
            factory_fn: 模型工厂函数，无参数或接受model_path
            model_path: 模型文件路径，用于生成缓存键
            
        Returns:
            缓存的模型实例
        """
        cache_key = cls._make_key(model_type, model_path)
        
        if cache_key in cls._cache:
            logger.debug(f"从缓存获取模型: {cache_key}")
            return cls._cache[cache_key]
        
        with cls._get_lock(cache_key):
            if cache_key in cls._cache:
                return cls._cache[cache_key]
            
            logger.info(f"创建新模型实例: {cache_key}")
            try:
                if model_path:
                    model = factory_fn(model_path, *args, **kwargs)
                else:
                    model = factory_fn(*args, **kwargs)
                cls._cache[cache_key] = model
                return model
            except Exception as e:
                logger.error(f"模型创建失败 {cache_key}: {e}")
                raise
    
    @classmethod
    def _make_key(cls, model_type: str, model_path: Optional[str] = None) -> str:
        """生成缓存键"""
        if model_path:
            return f"{model_type}:{model_path}"
        return model_type
    
    @classmethod
    def _get_lock(cls, key: str) -> threading.Lock:
        """获取特定key的锁"""
        with cls._lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]
    
    @classmethod
    def clear(cls, model_type: Optional[str] = None):
        """
        清除缓存的模型
        
        Args:
            model_type: 如果指定，只清除该类型的模型；否则清除所有
        """
        if model_type:
            keys_to_remove = [k for k in cls._cache if k.startswith(f"{model_type}:")]
            for key in keys_to_remove:
                del cls._cache[key]
                logger.info(f"已清除模型缓存: {key}")
        else:
            count = len(cls._cache)
            cls._cache.clear()
            logger.info(f"已清除所有模型缓存 ({count}个)")
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cached_models": list(cls._cache.keys()),
            "cache_count": len(cls._cache),
        }
