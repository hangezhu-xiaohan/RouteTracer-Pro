# -- coding: utf-8 --
"""路由追踪地图生成器的抽象基类

定义地图生成器的核心接口和共享功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import datetime
from pathlib import Path
from .config import TraceMapConfig


class BaseTraceMapGenerator(ABC):
    """路由追踪地图生成器抽象基类"""
    
    def __init__(self, config: TraceMapConfig = None):
        """初始化地图生成器
        
        :param config: TraceMap配置对象，如果为None则使用默认配置
        """
        self.config = config or TraceMapConfig()
    
    @abstractmethod
    def generate(self, traceroute_data: List[List[Any]], hostname: str) -> str:
        """生成路由追踪地图可视化
        
        :param traceroute_data: 路由追踪数据，格式为[[lat, lng, city, owner, asnumber, ip, whois, ttl, rtt, hostname], ...]
        :param hostname: 目标主机名
        :return: 生成的HTML文件路径
        """
        pass
    
    def generate_filename(self, hostname: str) -> str:
        """生成文件名
        
        :param hostname: 目标主机名
        :return: 生成的文件名
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_hostname = hostname.replace('.', '_')
        return f"traceroute_{safe_hostname}_{timestamp}.html"
    
    def validate_traceroute_data(self, traceroute_data: List[List[Any]]) -> bool:
        """验证路由追踪数据的有效性
        
        :param traceroute_data: 路由追踪数据
        :return: 如果数据有效返回True，否则返回False
        """
        if not traceroute_data or not isinstance(traceroute_data, list):
            return False
        
        # 检查每个节点是否至少包含经纬度信息
        for node in traceroute_data:
            if not isinstance(node, (list, tuple)) or len(node) < 2:
                return False
            
            # 检查经纬度是否为数字
            try:
                float(node[0])
                float(node[1])
            except (ValueError, TypeError):
                return False
        
        return True
    
    def ensure_output_directory(self) -> None:
        """确保输出目录存在"""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def get_node_info(self, node: List[Any], index: int) -> Dict[str, str]:
        """获取节点信息
        
        :param node: 节点数据
        :param index: 节点索引
        :return: 节点信息字典
        """
        return {
            'hop': node[7] if len(node) > 7 else str(index + 1),
            'ip': node[5] if len(node) > 5 else 'N/A',
            'city': node[2] if len(node) > 2 else 'N/A',
            'owner': node[3] if len(node) > 3 else 'N/A',
            'rtt': node[8] if len(node) > 8 else 'N/A',
            'type': 'start' if index == 0 else 'end' if index == len(node) - 1 else 'middle'
        }
    
    def preprocess_traceroute_data(self, traceroute_data: List[List[Any]]) -> List[List[Any]]:
        """预处理路由追踪数据
        
        可以在子类中重写此方法以实现特定的预处理逻辑
        
        :param traceroute_data: 原始路由追踪数据
        :return: 预处理后的路由追踪数据
        """
        # 默认实现：移除无效节点
        return [node for node in traceroute_data if len(node) >= 2 and isinstance(node[0], (int, float)) and isinstance(node[1], (int, float))]
    
    def post_process(self, html_path: str) -> str:
        """后处理生成的HTML文件
        
        可以在子类中重写此方法以实现特定的后处理逻辑
        
        :param html_path: HTML文件路径
        :return: 处理后的HTML文件路径
        """
        # 默认实现：直接返回原路径
        return html_path
