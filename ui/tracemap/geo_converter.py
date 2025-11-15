# -- coding: utf-8 --
"""地理坐标转换工具类

用于处理经纬度与SVG坐标之间的转换
"""

from typing import Tuple, List, Dict, Any
from .config import TraceMapConfig


class GeoConverter:
    """地理坐标转换器"""
    
    def __init__(self, config: TraceMapConfig = None):
        """初始化地理坐标转换器
        
        :param config: TraceMap配置对象，如果为None则使用默认配置
        """
        self.config = config or TraceMapConfig()
    
    def lat_lng_to_svg(self, lat: float, lng: float) -> Tuple[float, float]:
        """将经纬度转换为SVG坐标
        
        :param lat: 纬度
        :param lng: 经度
        :return: SVG坐标(x, y)元组
        """
        # 获取配置的地图范围
        min_lng, max_lng = self.config.min_lng, self.config.max_lng
        min_lat, max_lat = self.config.min_lat, self.config.max_lat
        width, height = self.config.map_width, self.config.map_height
        
        # 计算SVG坐标（做一些简单的缩放和偏移）
        x = ((lng - min_lng) / (max_lng - min_lng)) * width
        # 纬度需要反转，因为SVG的y轴向下
        y = height - ((lat - min_lat) / (max_lat - min_lat)) * height
        
        # 确保坐标在SVG范围内
        x = max(0, min(x, width))
        y = max(0, min(y, height))
        
        return x, y
    
    def svg_to_lat_lng(self, x: float, y: float) -> Tuple[float, float]:
        """将SVG坐标转换为经纬度
        
        :param x: SVG x坐标
        :param y: SVG y坐标
        :return: 经纬度(lat, lng)元组
        """
        # 获取配置的地图范围
        min_lng, max_lng = self.config.min_lng, self.config.max_lng
        min_lat, max_lat = self.config.min_lat, self.config.max_lat
        width, height = self.config.map_width, self.config.map_height
        
        # 计算经纬度
        lng = min_lng + (x / width) * (max_lng - min_lng)
        # 注意：SVG的y轴向下，需要反转
        lat = min_lat + ((height - y) / height) * (max_lat - min_lat)
        
        # 确保经纬度在有效范围内
        lat = max(-90, min(90, lat))
        lng = max(-180, min(180, lng))
        
        return lat, lng
    
    def convert_traceroute_to_svg_points(self, traceroute_data: List[List[Any]]) -> List[Dict[str, Any]]:
        """将路由追踪数据转换为SVG点数据
        
        :param traceroute_data: 路由追踪数据，格式为[[lat, lng, city, owner, asnumber, ip, whois, ttl, rtt, hostname], ...]
        :return: SVG点数据列表
        """
        svg_points = []
        for i, node in enumerate(traceroute_data):
            if len(node) >= 2:
                lat, lng = node[0], node[1]
                x, y = self.lat_lng_to_svg(lat, lng)
                
                # 获取节点信息
                ip = node[5] if len(node) > 5 else 'N/A'
                city = node[2] if len(node) > 2 else 'N/A'
                owner = node[3] if len(node) > 3 else 'N/A'
                rtt = node[8] if len(node) > 8 else 'N/A'
                hop = node[7] if len(node) > 7 else str(i+1)
                
                svg_points.append({
                    'x': x,
                    'y': y,
                    'type': 'start' if i == 0 else 'end' if i == len(traceroute_data) - 1 else 'middle',
                    'info': {
                        'hop': hop,
                        'ip': ip,
                        'city': city,
                        'owner': owner,
                        'rtt': rtt
                    }
                })
        
        return svg_points
    
    def generate_path_data(self, svg_points: List[Dict[str, Any]]) -> str:
        """生成SVG路径数据
        
        :param svg_points: SVG点数据列表
        :return: SVG路径数据字符串
        """
        if not svg_points:
            return ''
        
        if len(svg_points) == 1:
            p = svg_points[0]
            return f'M {p["x"]},{p["y"]} L {p["x"]},{p["y"]}'
        
        # 生成多点路径
        path_data = f'M {svg_points[0]["x"]},{svg_points[0]["y"]}'
        for p in svg_points[1:]:
            path_data += f' L {p["x"]},{p["y"]}'
        
        return path_data
