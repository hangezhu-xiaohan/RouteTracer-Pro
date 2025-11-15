# -- coding: utf-8 --
"""traceMap 包初始化

路由追踪地图可视化框架包
"""

# 导出核心类和函数
from .base_generator import BaseTraceMapGenerator
from .svg_generator import SVGTraceMapGenerator
from .config import TraceMapConfig
from .geo_converter import GeoConverter
from .template_renderer import TemplateRenderer

# 从utils导入常用函数，确保与原有API兼容
from .utils import generate_tracemap, generate_and_open_tracemap, convert_traceroute_data_for_tracemap, create_custom_config, test_integration

# 定义公共接口
__all__ = [
    # 核心类
    'BaseTraceMapGenerator',
    'SVGTraceMapGenerator',
    'TraceMapConfig',
    'GeoConverter',
    'TemplateRenderer',
    # 工具函数
    'generate_tracemap',
    'generate_and_open_tracemap',
    'convert_traceroute_data_for_tracemap',
    'create_custom_config',
    'test_integration'
]
