# -- coding: utf-8 --
"""traceMap配置类

用于管理路由追踪地图可视化的所有配置选项
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class TraceMapConfig:
    """traceMap配置类"""
    
    # 输出目录设置
    output_dir: str = './html'
    
    # 地图设置
    map_width: int = 800
    map_height: int = 500
    
    # 中国地图经纬度范围
    min_lng: float = 73.0
    max_lng: float = 135.0
    min_lat: float = 18.0
    max_lat: float = 53.0
    
    # 颜色配置
    start_node_color: str = '#2196F3'  # 起始节点蓝色
    middle_node_color: str = '#4CAF50'  # 中间节点绿色
    end_node_color: str = '#F44336'  # 终点节点红色
    route_path_color: str = '#FF9800'  # 路由路径橙色
    
    # 样式配置
    node_radius: int = 8
    stroke_width: int = 2
    font_size: int = 12
    
    # HTML模板配置
    template_dir: Optional[str] = None
    template_file: str = 'template.html'
    
    # 额外选项
    show_legend: bool = True
    show_table: bool = True
    
    def get_output_path(self, filename: str) -> str:
        """获取完整的输出文件路径
        
        :param filename: 文件名
        :return: 完整的文件路径
        """
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, filename)
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典
        
        :return: 配置字典
        """
        return {
            'output_dir': self.output_dir,
            'map_width': self.map_width,
            'map_height': self.map_height,
            'min_lng': self.min_lng,
            'max_lng': self.max_lng,
            'min_lat': self.min_lat,
            'max_lat': self.max_lat,
            'start_node_color': self.start_node_color,
            'middle_node_color': self.middle_node_color,
            'end_node_color': self.end_node_color,
            'route_path_color': self.route_path_color,
            'node_radius': self.node_radius,
            'stroke_width': self.stroke_width,
            'font_size': self.font_size,
            'template_dir': self.template_dir,
            'template_file': self.template_file,
            'show_legend': self.show_legend,
            'show_table': self.show_table
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TraceMapConfig':
        """从字典创建配置对象
        
        :param config_dict: 配置字典
        :return: 配置对象
        """
        return cls(**config_dict)
