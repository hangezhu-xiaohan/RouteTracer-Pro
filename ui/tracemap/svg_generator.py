# -- coding: utf-8 --
"""SVG路由追踪地图生成器

使用SVG技术实现的路由追踪地图可视化生成器
"""

from typing import List, Any
from .base_generator import BaseTraceMapGenerator
from .geo_converter import GeoConverter
from .template_renderer import TemplateRenderer
from .config import TraceMapConfig


class SVGTraceMapGenerator(BaseTraceMapGenerator):
    """SVG路由追踪地图生成器"""
    
    def __init__(self, config: TraceMapConfig = None):
        """初始化SVG地图生成器
        
        :param config: TraceMap配置对象，如果为None则使用默认配置
        """
        super().__init__(config)
        self.geo_converter = GeoConverter(config)
        self.template_renderer = TemplateRenderer(config)
    
    def generate(self, traceroute_data: List[List[Any]], hostname: str) -> str:
        """生成SVG格式的路由追踪地图可视化
        
        :param traceroute_data: 路由追踪数据，格式为[[lat, lng, city, owner, asnumber, ip, whois, ttl, rtt, hostname], ...]
        :param hostname: 目标主机名
        :return: 生成的HTML文件路径
        """
        # 验证数据
        if not self.validate_traceroute_data(traceroute_data):
            raise ValueError("无效的路由追踪数据")
        
        # 预处理数据
        processed_data = self.preprocess_traceroute_data(traceroute_data)
        
        if not processed_data:
            raise ValueError("处理后没有有效的路由追踪数据")
        
        # 确保输出目录存在
        self.ensure_output_directory()
        
        # 将经纬度转换为SVG坐标
        svg_points = self.geo_converter.convert_traceroute_to_svg_points(processed_data)
        
        # 生成SVG路径数据
        path_data = self.geo_converter.generate_path_data(svg_points)
        
        # 渲染HTML内容
        html_content = self.template_renderer.render(
            traceroute_data=processed_data,
            hostname=hostname,
            svg_points=svg_points,
            path_data=path_data
        )
        
        # 生成文件名并保存文件
        filename = self.generate_filename(hostname)
        html_path = self.template_renderer.save_to_file(html_content, filename)
        
        # 后处理
        html_path = self.post_process(html_path)
        
        return html_path
    
    def preprocess_traceroute_data(self, traceroute_data: List[List[Any]]) -> List[List[Any]]:
        """预处理路由追踪数据，添加额外的验证和过滤
        
        :param traceroute_data: 原始路由追踪数据
        :return: 预处理后的路由追踪数据
        """
        # 调用父类的预处理方法
        processed_data = super().preprocess_traceroute_data(traceroute_data)
        
        # 进一步验证经纬度范围
        valid_data = []
        for node in processed_data:
            lat, lng = node[0], node[1]
            # 检查经纬度是否在有效范围内
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                valid_data.append(node)
        
        return valid_data
    
    def customize_map(self, html_content: str, **kwargs) -> str:
        """自定义地图样式和内容
        
        :param html_content: 原始HTML内容
        :param kwargs: 自定义参数
        :return: 自定义后的HTML内容
        """
        # 示例：允许自定义地图背景颜色
        if 'map_background' in kwargs:
            # 替换地图背景颜色
            html_content = html_content.replace(
                'background-color: #f5f5f5;',
                f'background-color: {kwargs["map_background"]};'
            )
        
        # 示例：允许自定义节点大小
        if 'node_radius' in kwargs:
            # 替换节点半径
            radius = kwargs['node_radius']
            html_content = html_content.replace(
                f'r="{self.config.node_radius}"',
                f'r="{radius}"'
            )
        
        return html_content
