#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU优化配置对话框和性能监控窗口组件

提供CPU优化配置界面和性能监控显示功能。

Author: Vision System Team
Date: 2026-01-26
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QCheckBox, QPushButton, QGroupBox, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDockWidget, QWidget, QStatusBar, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

try:
    from modules.cpu_optimization import (
        ParallelEngine,
        MemoryPool,
        SIMDOptimizer,
        PerformanceMonitor,
        get_performance_monitor
    )
    CPU_OPT_AVAILABLE = True
except ImportError:
    CPU_OPT_AVAILABLE = False


class CPUOptimizationDialog(QDialog):
    """CPU优化配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CPU优化配置")
        self.setMinimumSize(500, 400)
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 线程配置选项卡
        thread_tab = self._create_thread_tab()
        tab_widget.addTab(thread_tab, "线程配置")
        
        # 内存配置选项卡
        memory_tab = self._create_memory_tab()
        tab_widget.addTab(memory_tab, "内存配置")
        
        # SIMD信息选项卡
        simd_tab = self._create_simd_tab()
        tab_widget.addTab(simd_tab, "SIMD优化")
        
        layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.apply_settings)
        
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self.reset_settings)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _create_thread_tab(self):
        """创建线程配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 线程数配置
        thread_group = QGroupBox("线程配置")
        thread_layout = QGridLayout(thread_group)
        
        thread_layout.addWidget(QLabel("CPU核心数:"), 0, 0)
        self.cpu_count_label = QLabel(str(os.cpu_count() or 4))
        thread_layout.addWidget(self.cpu_count_label, 0, 1)
        
        thread_layout.addWidget(QLabel("建议线程数:"), 1, 0)
        suggested_threads = max(1, (os.cpu_count() or 4) - 1)
        self.suggested_label = QLabel(str(suggested_threads))
        thread_layout.addWidget(self.suggested_label, 1, 1)
        
        thread_layout.addWidget(QLabel("使用线程数:"), 2, 0)
        self.thread_spinner = QSpinBox()
        self.thread_spinner.setRange(0, 64)
        self.thread_spinner.setValue(0)
        self.thread_spinner.setToolTip("0表示自动检测所有CPU核心")
        thread_layout.addWidget(self.thread_spinner, 2, 1)
        
        layout.addWidget(thread_group)
        
        # OpenMP配置
        omp_group = QGroupBox("并行库配置")
        omp_layout = QVBoxLayout(omp_group)
        
        self.omp_check = QCheckBox("启用OpenMP并行支持")
        self.omp_check.setChecked(True)
        omp_layout.addWidget(self.omp_check)
        
        self.mkl_check = QCheckBox("启用Intel MKL优化")
        self.mkl_check.setChecked(True)
        omp_layout.addWidget(self.mkl_check)
        
        layout.addWidget(omp_group)
        layout.addStretch()
        
        return widget
    
    def _create_memory_tab(self):
        """创建内存配置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 内存池配置
        pool_group = QGroupBox("内存池配置")
        pool_layout = QGridLayout(pool_group)
        
        self.enable_pool_check = QCheckBox("启用内存池")
        self.enable_pool_check.setChecked(True)
        self.enable_pool_check.toggled.connect(self._on_pool_enabled_changed)
        pool_layout.addWidget(self.enable_pool_check, 0, 0, 1, 2)
        
        pool_layout.addWidget(QLabel("最大池大小 (MB):"), 1, 0)
        self.max_pool_size = QSpinBox()
        self.max_pool_size.setRange(64, 4096)
        self.max_pool_size.setValue(512)
        self.max_pool_size.setEnabled(False)
        pool_layout.addWidget(self.max_pool_size, 1, 1)
        
        layout.addWidget(pool_group)
        
        # 内存信息
        info_group = QGroupBox("当前内存状态")
        info_layout = QGridLayout(info_group)
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            
            info_layout.addWidget(QLabel("总内存:"), 0, 0)
            info_layout.addWidget(QLabel(f"{mem.total / (1024**3):.2f} GB"), 0, 1)
            
            info_layout.addWidget(QLabel("已用内存:"), 1, 0)
            info_layout.addWidget(QLabel(f"{mem.used / (1024**3):.2f} GB ({mem.percent}%)"), 1, 1)
            
            info_layout.addWidget(QLabel("可用内存:"), 2, 0)
            info_layout.addWidget(QLabel(f"{mem.available / (1024**3):.2f} GB"), 2, 1)
        except ImportError:
            info_layout.addWidget(QLabel("无法获取内存信息"), 0, 0, 1, 2)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def _create_simd_tab(self):
        """创建SIMD信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if not CPU_OPT_AVAILABLE:
            layout.addWidget(QLabel("CPU优化模块不可用"))
            layout.addStretch()
            return widget
        
        # SIMD能力检测
        simd_group = QGroupBox("SIMD指令集支持")
        simd_layout = QGridLayout(simd_group)
        
        optimizer = SIMDOptimizer()
        caps = optimizer.capabilities
        
        simd_flags = [
            ("SSE2", caps.sse2),
            ("SSE3", caps.sse3),
            ("SSE4.1", caps.sse4_1),
            ("SSE4.2", caps.sse4_2),
            ("AVX", caps.avx),
            ("AVX2", caps.avx2),
            ("AVX-512F", caps.avx512f),
        ]
        
        for i, (name, supported) in enumerate(simd_flags):
            simd_layout.addWidget(QLabel(f"{name}:"), i, 0)
            status = "✓ 支持" if supported else "✗ 不支持"
            color = "green" if supported else "red"
            label = QLabel(status)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            simd_layout.addWidget(label, i, 1)
        
        layout.addWidget(simd_group)
        
        # 优化级别
        level_group = QGroupBox("优化级别")
        level_layout = QVBoxLayout(level_group)
        
        level_layout.addWidget(QLabel(f"当前优化级别: {caps.optimization_level.upper()}"))
        
        if caps.avx512f:
            level_layout.addWidget(QLabel("✓ 已启用最高性能优化"))
        elif caps.avx2:
            level_layout.addWidget(QLabel("✓ 已启用AVX2优化"))
        elif caps.sse4_2:
            level_layout.addWidget(QLabel("✓ 已启用SSE4优化"))
        else:
            level_layout.addWidget(QLabel("⚠ 建议升级CPU以获得更好性能"))
        
        layout.addWidget(level_group)
        layout.addStretch()
        
        return widget
    
    def _on_pool_enabled_changed(self, enabled):
        """内存池启用状态改变"""
        self.max_pool_size.setEnabled(enabled)
    
    def load_current_settings(self):
        """加载当前设置"""
        # 读取当前环境变量设置
        omp_threads = os.environ.get('OMP_NUM_THREADS', '0')
        self.thread_spinner.setValue(int(omp_threads) if omp_threads.isdigit() else 0)
        
    def apply_settings(self):
        """应用设置"""
        try:
            threads = self.thread_spinner.value()
            
            # 设置环境变量
            if threads > 0:
                os.environ['OMP_NUM_THREADS'] = str(threads)
                os.environ['MKL_NUM_THREADS'] = str(threads)
            else:
                os.environ.pop('OMP_NUM_THREADS', None)
                os.environ.pop('MKL_NUM_THREADS', None)
            
            # 应用内存池设置
            if self.enable_pool_check.isChecked():
                if CPU_OPT_AVAILABLE:
                    pool = MemoryPool()
                    pool.set_max_size(self.max_pool_size.value())
            
            QMessageBox.information(self, "成功", "CPU优化设置已应用")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用设置失败:\n{str(e)}")
    
    def reset_settings(self):
        """重置设置"""
        self.thread_spinner.setValue(0)
        self.omp_check.setChecked(True)
        self.mkl_check.setChecked(True)
        self.enable_pool_check.setChecked(True)
        self.max_pool_size.setValue(512)


class PerformanceMonitorWidget(QWidget):
    """性能监控窗口部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self._monitor = None
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 实时指标显示
        metrics_group = QGroupBox("实时指标")
        metrics_layout = QGridLayout(metrics_group)
        
        # CPU利用率
        metrics_layout.addWidget(QLabel("CPU利用率:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setFixedWidth(200)
        metrics_layout.addWidget(self.cpu_progress, 0, 1)
        self.cpu_label = QLabel("0%")
        metrics_layout.addWidget(self.cpu_label, 0, 2)
        
        # 内存占用
        metrics_layout.addWidget(QLabel("内存占用:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setFixedWidth(200)
        metrics_layout.addWidget(self.memory_progress, 1, 1)
        self.memory_label = QLabel("0 MB")
        metrics_layout.addWidget(self.memory_label, 1, 2)
        
        # 推理速度
        metrics_layout.addWidget(QLabel("推理速度:"), 2, 0)
        self.fps_label = QLabel("0 FPS")
        self.fps_label.setStyleSheet("font-weight: bold; color: green;")
        metrics_layout.addWidget(self.fps_label, 2, 1, 1, 2)
        
        # 推理时间
        metrics_layout.addWidget(QLabel("推理时间:"), 3, 0)
        self.inference_label = QLabel("0 ms")
        metrics_layout.addWidget(self.inference_label, 3, 1, 1, 2)
        
        layout.addWidget(metrics_group)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout(stats_group)
        
        stats_layout.addWidget(QLabel("总推理次数:"), 0, 0)
        self.total_inferences_label = QLabel("0")
        stats_layout.addWidget(self.total_inferences_label, 0, 1)
        
        stats_layout.addWidget(QLabel("平均推理时间:"), 1, 0)
        self.avg_inference_label = QLabel("0 ms")
        stats_layout.addWidget(self.avg_inference_label, 1, 1)
        
        stats_layout.addWidget(QLabel("最快推理时间:"), 2, 0)
        self.min_inference_label = QLabel("0 ms")
        stats_layout.addWidget(self.min_inference_label, 2, 1)
        
        stats_layout.addWidget(QLabel("最慢推理时间:"), 3, 0)
        self.max_inference_label = QLabel("0 ms")
        stats_layout.addWidget(self.max_inference_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("导出数据")
        export_button.clicked.connect(self._export_data)
        
        reset_button = QPushButton("重置统计")
        reset_button.clicked.connect(self._reset_stats)
        
        button_layout.addStretch()
        button_layout.addWidget(export_button)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)
    
    def _start_monitoring(self):
        """开始监控"""
        try:
            if CPU_OPT_AVAILABLE:
                self._monitor = get_performance_monitor(0.5)
                self._monitor.start()
                
                # 启动更新定时器
                self._timer = QTimer()
                self._timer.timeout.connect(self._update_display)
                self._timer.start(500)  # 每500ms更新一次
        except Exception as e:
            print(f"性能监控启动失败: {e}")
    
    def _update_display(self):
        """更新显示"""
        if not self._monitor:
            return
        
        try:
            metrics = self._monitor.get_current_metrics()
            stats = self._monitor.get_statistics()
            
            # 更新实时指标
            self.cpu_progress.setValue(int(metrics.cpu_percent))
            self.cpu_label.setText(f"{metrics.cpu_percent:.1f}%")
            
            self.memory_progress.setValue(int(metrics.memory_percent))
            self.memory_label.setText(f"{metrics.memory_used_mb:.1f} MB")
            
            self.fps_label.setText(f"{metrics.fps:.1f} FPS")
            self.inference_label.setText(f"{metrics.inference_time_ms:.2f} ms")
            
            # 更新统计信息
            self.total_inferences_label.setText(str(stats.get("total_inferences", 0)))
            self.avg_inference_label.setText(f"{stats.get('avg_inference_time', 0):.2f} ms")
            self.min_inference_label.setText(f"{stats.get('min_inference_time', float('inf')):.2f} ms")
            self.max_inference_label.setText(f"{stats.get('max_inference_time', 0):.2f} ms")
            
        except Exception as e:
            pass
    
    def _export_data(self):
        """导出数据"""
        if not self._monitor:
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            filepath, _ = QFileDialog.getSaveFileName(
                self, "导出性能数据", "performance_data.json", 
                "JSON文件 (*.json);;CSV文件 (*.csv)"
            )
            
            if filepath:
                format = "json" if filepath.endswith(".json") else "csv"
                if self._monitor.export_history(filepath, format):
                    QMessageBox.information(self, "成功", f"数据已导出到:\n{filepath}")
                else:
                    QMessageBox.warning(self, "警告", "导出失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def _reset_stats(self):
        """重置统计"""
        if self._monitor:
            self._monitor.reset_stats()
            self._update_display()
    
    def closeEvent(self, event):
        """关闭事件"""
        if self._monitor:
            self._monitor.stop()
        super().closeEvent(event)
