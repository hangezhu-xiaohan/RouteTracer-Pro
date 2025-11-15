# -- coding: utf-8 --
"""traceMap工具函数

提供一些实用函数，保持与原有API的兼容性
"""

import os
import webbrowser
from typing import List, Tuple, Any
from .svg_generator import SVGTraceMapGenerator
from .config import TraceMapConfig


def convert_traceroute_data_for_tracemap(trace_data: List[Tuple[Any]]) -> List[List[Any]]:
    """将RouteTracer Pro的路由追踪结果转换为traceMap所需的格式
    
    保持与原有API的兼容性
    
    :param trace_data: RouteTracer Pro的路由追踪结果列表，格式为[(hop, ip, delay, location), ...]
    :return: traceMap需要的经纬度信息列表，格式为[[lat, lng, city, owner, asnumber, ip, whois, ttl, rtt, hostname], ...]
    """
    result = []
    
    # 处理每个路由跳点
    for idx, item in enumerate(trace_data):
        # 安全地提取必要字段，避免解包错误
        try:
            # 根据不同的数据格式提取字段
            if isinstance(item, (list, tuple)):
                # 获取至少4个必要字段
                hop = item[0] if len(item) > 0 else 0
                ip = item[1] if len(item) > 1 else ''
                delay = item[2] if len(item) > 2 else 0
                location = item[3] if len(item) > 3 else ''
            else:
                continue
            
            if hop <= 0 or not ip or delay <= 0:
                continue
            
            # 从location字符串中提取ISP信息
            owner = ""
            isp = ""
            city = location
            
            if location and '(' in location and ')' in location:
                isp_start = location.find('(') + 1
                isp_end = location.find(')')
                if isp_end > isp_start:
                    isp = location[isp_start:isp_end]
                    city = location[:isp_start-1].strip()
                    owner = isp
        except Exception as e:
            print(f"处理路由节点时出错: {e}")
            continue
        
        # 简单的经纬度估算（实际应用中应该使用更准确的地理位置数据库）
        # 从ip地址生成一些伪随机但固定的经纬度
        lat = 30.0 + (hash(ip) % 20) - 10  # 大致范围在20-40度之间
        lng = 100.0 + (hash(ip) % 60) - 30  # 大致范围在70-130度之间
        
        # 确保经纬度在有效范围内
        lat = max(-90, min(90, lat))
        lng = max(-180, min(180, lng))
        
        # 添加到结果列表
        result.append([
            lat,                      # 纬度
            lng,                      # 经度
            city,                     # 城市
            owner,                    # 所有者
            "",                       # AS号（如果有）
            ip,                       # IP地址
            "",                       # WHOIS信息
            str(hop),                 # TTL
            f"{delay:.2f}",            # RTT (ms)
            ""                        # 主机名
        ])
    
    return result

def generate_tracemap(trace_data: List[Tuple[Any]], hostname: str, output_dir: str = None, config: TraceMapConfig = None) -> str:
    """生成路由追踪地图可视化
    
    保持与原有API的兼容性
    
    :param trace_data: RouteTracer Pro的路由追踪结果列表
    :param hostname: 目标主机名
    :param output_dir: 输出目录，默认为当前目录下的html文件夹
    :param config: TraceMap配置对象，如果为None则使用默认配置
    :return: 生成的HTML文件路径
    """
    # 如果没有路由数据，返回错误
    if not trace_data:
        raise ValueError("没有有效的路由追踪数据")
    
    # 创建配置对象
    if config is None:
        config = TraceMapConfig()
    
    # 如果指定了输出目录，更新配置
    if output_dir is not None:
        config.output_dir = output_dir
    
    # 转换数据格式
    converted_data = convert_traceroute_data_for_tracemap(trace_data)
    
    if not converted_data:
        raise ValueError("无法转换路由追踪数据为地图格式")
    
    # 使用SVG生成器生成地图
    generator = SVGTraceMapGenerator(config)
    html_path = generator.generate(converted_data, hostname)
    
    print(f"traceMap已生成: {html_path}")
    return html_path

def generate_and_open_tracemap(trace_data: List[Tuple[Any]], hostname: str, output_dir: str = None, config: TraceMapConfig = None) -> str:
    """生成路由追踪地图并在浏览器中打开
    
    保持与原有API的兼容性
    
    :param trace_data: RouteTracer Pro的路由追踪结果列表
    :param hostname: 目标主机名
    :param output_dir: 输出目录，默认为当前目录下的html文件夹
    :param config: TraceMap配置对象，如果为None则使用默认配置
    :return: 生成的HTML文件路径
    """
    html_path = generate_tracemap(trace_data, hostname, output_dir, config)
    
    # 在浏览器中打开生成的HTML文件
    try:
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
    except Exception as e:
        print(f"无法在浏览器中打开地图: {str(e)}")
    
    return html_path

def create_custom_config(**kwargs) -> TraceMapConfig:
    """创建自定义配置
    
    :param kwargs: 配置参数
    :return: TraceMapConfig对象
    """
    # 创建默认配置
    config = TraceMapConfig()
    
    # 更新配置参数
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config

def test_integration():
    """测试集成功能
    
    提供一个简单的测试函数，用于验证新架构的功能是否正常
    """
    # 模拟的路由追踪数据
    mock_trace_data = [
        (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
        (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
        (3, '202.96.128.166', 8.7, '中国 北京 (联通)'),
        (4, '219.158.3.13', 12.3, '中国 北京 (联通骨干网)'),
        (5, '219.158.10.42', 15.6, '中国 上海 (联通骨干网)'),
        (6, '219.158.97.22', 22.8, '中国 上海 (联通)'),
        (7, '103.235.46.242', 25.1, '美国 加利福尼亚 (Google)')
    ]
    
    try:
        # 使用默认配置
        print("使用默认配置测试...")
        html_path = generate_and_open_tracemap(mock_trace_data, 'google.com')
        print(f"默认配置测试成功，生成文件: {html_path}")
        
        # 使用自定义配置
        print("使用自定义配置测试...")
        custom_config = create_custom_config(
            map_width=1000,
            map_height=600,
            start_node_color='#0000FF',
            end_node_color='#FF0000',
            middle_node_color='#00FF00',
            route_path_color='#FFA500'
        )
        html_path = generate_tracemap(mock_trace_data, 'custom_google.com', config=custom_config)
        print(f"自定义配置测试成功，生成文件: {html_path}")
        
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False
