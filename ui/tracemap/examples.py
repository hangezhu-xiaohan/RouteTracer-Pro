# -- coding: utf-8 --
"""traceMap 使用示例

本文件提供了traceMap模块的各种使用示例，帮助开发者快速上手
"""

import os
from typing import List, Tuple, Any

# 导入traceMap模块
from ui.tracemap import (
    generate_tracemap,
    generate_and_open_tracemap,
    TraceMapConfig,
    SVGTraceMapGenerator,
    BaseTraceMapGenerator,
    GeoConverter,
    TemplateRenderer,
    create_custom_config,
    convert_traceroute_data_for_tracemap
)


def example_basic_usage():
    """示例1: 基本使用"""
    print("=== 示例1: 基本使用 ===")
    
    # 模拟路由追踪数据
    trace_data = [
        (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
        (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
        (3, '202.96.128.166', 8.7, '中国 北京 (联通)'),
        (4, '219.158.3.13', 12.3, '中国 北京 (联通骨干网)'),
        (5, '219.158.10.42', 15.6, '中国 上海 (联通骨干网)'),
    ]
    
    print("生成地图...")
    html_path = generate_tracemap(trace_data, 'example.com')
    print(f"地图已生成: {os.path.abspath(html_path)}")
    print("\n")


def example_open_in_browser():
    """示例2: 生成地图并在浏览器中打开"""
    print("=== 示例2: 生成地图并在浏览器中打开 ===")
    
    # 模拟路由追踪数据（更短的路径）
    trace_data = [
        (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
        (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
        (3, '202.96.128.166', 8.7, '中国 北京 (联通)'),
    ]
    
    print("生成地图并在浏览器中打开...")
    html_path = generate_and_open_tracemap(trace_data, 'browser.example.com')
    print(f"地图已生成并打开: {os.path.abspath(html_path)}")
    print("\n")


def example_custom_config():
    """示例3: 使用自定义配置"""
    print("=== 示例3: 使用自定义配置 ===")
    
    # 模拟路由追踪数据
    trace_data = [
        (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
        (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
        (3, '202.96.128.166', 8.7, '中国 北京 (联通)'),
    ]
    
    # 方法1: 直接创建配置对象
    config = TraceMapConfig()
    config.map_width = 1200
    config.map_height = 800
    config.start_node_color = '#FF0000'  # 红色起点
    config.end_node_color = '#00FF00'    # 绿色终点
    config.middle_node_color = '#0000FF' # 蓝色中间节点
    config.route_path_color = '#FFA500'  # 橙色路径
    config.node_radius = 8              # 更大的节点
    config.line_width = 3               # 更粗的路径
    
    print("使用自定义配置生成地图...")
    html_path = generate_tracemap(trace_data, 'custom_config.example.com', config=config)
    print(f"地图已生成: {os.path.abspath(html_path)}")
    
    # 方法2: 使用create_custom_config辅助函数
    custom_config = create_custom_config(
        output_dir='./custom_html',
        map_width=1000,
        map_height=600,
        background_color='#f0f0f0'
    )
    
    html_path2 = generate_tracemap(trace_data, 'custom_config2.example.com', config=custom_config)
    print(f"使用辅助函数生成的地图: {os.path.abspath(html_path2)}")
    print("\n")


def example_direct_generator():
    """示例4: 直接使用生成器类"""
    print("=== 示例4: 直接使用生成器类 ===")
    
    # 模拟路由追踪数据
    trace_data = [
        (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
        (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
    ]
    
    # 转换数据格式
    converted_data = convert_traceroute_data_for_tracemap(trace_data)
    
    # 创建配置
    config = TraceMapConfig()
    config.map_width = 900
    config.map_height = 500
    
    # 创建生成器实例
    generator = SVGTraceMapGenerator(config)
    
    # 生成地图
    print("直接使用生成器类生成地图...")
    html_path = generator.generate(converted_data, 'direct_generator.example.com')
    print(f"地图已生成: {os.path.abspath(html_path)}")
    print("\n")


def example_custom_generator():
    """示例5: 创建自定义生成器"""
    print("=== 示例5: 创建自定义生成器 ===")
    
    # 自定义生成器类
    class MyCustomGenerator(BaseTraceMapGenerator):
        """自定义地图生成器示例"""
        
        def __init__(self, config=None):
            super().__init__(config)
            # 可以在这里初始化自定义组件
            self.custom_param = "这是一个自定义参数"
        
        def preprocess_traceroute_data(self, traceroute_data):
            """自定义数据预处理"""
            # 调用父类方法
            processed = super().preprocess_traceroute_data(traceroute_data)
            
            # 添加自定义处理
            print(f"{self.custom_param} - 预处理了 {len(processed)} 个路由节点")
            
            return processed
        
        def generate(self, traceroute_data, hostname):
            """实现自定义生成逻辑"""
            print(f"使用自定义生成器为 {hostname} 生成地图...")
            
            # 验证数据
            if not self.validate_traceroute_data(traceroute_data):
                raise ValueError("无效的路由追踪数据")
            
            # 预处理数据
            processed_data = self.preprocess_traceroute_data(traceroute_data)
            
            # 使用标准的SVG生成器来完成实际工作
            # 在实际应用中，这里可以实现完全自定义的生成逻辑
            svg_generator = SVGTraceMapGenerator(self.config)
            html_path = svg_generator.generate(processed_data, hostname)
            
            print(f"自定义生成完成！")
            return html_path
    
    # 模拟路由数据
    trace_data = [(1, '192.168.1.1', 1.2, '本地网络 (局域网)')]
    converted_data = convert_traceroute_data_for_tracemap(trace_data)
    
    # 使用自定义生成器
    custom_generator = MyCustomGenerator()
    html_path = custom_generator.generate(converted_data, 'custom_gen.example.com')
    print(f"自定义生成器生成的地图: {os.path.abspath(html_path)}")
    print("\n")


def example_custom_geo_converter():
    """示例6: 自定义地理坐标转换器"""
    print("=== 示例6: 自定义地理坐标转换器 ===")
    
    class MyGeoConverter(GeoConverter):
        """自定义地理坐标转换器"""
        
        def lat_lng_to_svg(self, lat: float, lng: float) -> Tuple[float, float]:
            """自定义的坐标转换方法"""
            # 这里可以实现更复杂的坐标转换逻辑
            # 例如使用真实的地理投影或特定区域的映射
            print(f"转换坐标: ({lat}, {lng})")
            
            # 调用父类方法但添加一些偏移
            x, y = super().lat_lng_to_svg(lat, lng)
            # 可以在这里修改坐标，例如添加一些装饰效果
            return x, y
    
    # 这个示例展示了如何扩展GeoConverter类
    # 在实际应用中，您可以在SVG生成器中替换默认的地理转换器
    print("在实际应用中，您可以通过继承SVGTraceMapGenerator并覆盖geo_converter属性来使用自定义转换器")
    print("\n")


def example_error_handling():
    """示例7: 错误处理"""
    print("=== 示例7: 错误处理 ===")
    
    # 测试空数据
    try:
        generate_tracemap([], 'empty.example.com')
    except ValueError as e:
        print(f"正确捕获到空数据错误: {e}")
    
    # 测试无效数据
    invalid_data = [(0, '', 0, '')]  # 无效的hop, ip和delay
    try:
        generate_tracemap(invalid_data, 'invalid.example.com')
        print("无效数据测试: 可能内部过滤了无效数据")
    except Exception as e:
        print(f"无效数据测试: 捕获到异常: {e}")
    
    print("\n")


def run_all_examples():
    """运行所有示例"""
    print("开始运行traceMap使用示例...\n")
    
    examples = [
        example_basic_usage,
        example_open_in_browser,
        example_custom_config,
        example_direct_generator,
        example_custom_generator,
        example_custom_geo_converter,
        example_error_handling
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"示例 {i} ({example_func.__name__}) 运行失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("所有示例运行完成！")


if __name__ == "__main__":
    # 运行所有示例
    run_all_examples()
    
    # 提示如何集成到RouteTracer Pro中
print("\n")
print("=== 如何将traceMap集成到RouteTracer Pro中 ===")
    print("1. 在需要使用地图可视化的地方导入:")
    print("   from ui.tracemap import generate_and_open_tracemap")
    print("\n2. 在路由追踪完成后调用:")
    print("   # 假设route_data是路由追踪的结果")
    print("   # hostname是目标主机名")
    print("   html_path = generate_and_open_tracemap(route_data, hostname)")
    print("\n3. 您也可以使用自定义配置:")
    print("   from ui.tracemap import TraceMapConfig")
    print("   config = TraceMapConfig()")
    print("   config.map_width = 1000")
    print("   html_path = generate_and_open_tracemap(route_data, hostname, config=config)")
