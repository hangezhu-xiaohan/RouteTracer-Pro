# traceMap 路由追踪地图可视化框架

一个可继承的路由追踪地图可视化框架，用于RouteTracer Pro中展示路由路径的地理可视化效果。

## 架构设计

本框架采用了面向对象的设计模式，提供了灵活的扩展接口，可以轻松集成到RouteTracer Pro中。

### 核心组件

- **BaseTraceMapGenerator**: 抽象基类，定义了地图生成器的通用接口
- **SVGTraceMapGenerator**: 具体实现类，使用SVG技术生成地图可视化
- **GeoConverter**: 地理坐标转换工具，处理经纬度与SVG坐标的转换
- **TemplateRenderer**: HTML模板渲染器，负责生成最终的HTML内容
- **TraceMapConfig**: 配置类，集中管理所有配置选项

## 安装与使用

### 导入方式

```python
# 导入常用函数（与原有API兼容）
from ui.tracemap import generate_tracemap, generate_and_open_tracemap

# 导入核心组件（用于扩展和自定义）
from ui.tracemap import TraceMapConfig, SVGTraceMapGenerator, BaseTraceMapGenerator
```

### 基本使用

#### 使用默认配置生成地图

```python
from ui.tracemap import generate_tracemap

# 路由追踪数据，格式为 [(hop, ip, delay, location), ...]
trace_data = [
    (1, '192.168.1.1', 1.2, '本地网络 (局域网)'),
    (2, '100.64.0.1', 3.5, '中国 北京 (联通)'),
    (3, '202.96.128.166', 8.7, '中国 北京 (联通)'),
]

# 生成地图文件
html_path = generate_tracemap(trace_data, 'example.com')
print(f"地图已生成: {html_path}")
```

#### 生成地图并在浏览器中打开

```python
from ui.tracemap import generate_and_open_tracemap

# 生成地图并自动在浏览器中打开
html_path = generate_and_open_tracemap(trace_data, 'example.com')
```

#### 使用自定义配置

```python
from ui.tracemap import generate_tracemap, TraceMapConfig

# 创建自定义配置
config = TraceMapConfig()
config.map_width = 1200
config.map_height = 800
config.start_node_color = '#FF0000'  # 红色起点
config.end_node_color = '#00FF00'    # 绿色终点
config.middle_node_color = '#0000FF' # 蓝色中间节点
config.route_path_color = '#FFA500'  # 橙色路径
config.node_radius = 6              # 节点半径
config.line_width = 3               # 路径线宽

# 使用自定义配置生成地图
html_path = generate_tracemap(trace_data, 'example.com', config=config)
```

## 高级功能

### 创建自定义生成器

如果需要自定义地图生成逻辑，可以继承`BaseTraceMapGenerator`类：

```python
from ui.tracemap import BaseTraceMapGenerator, TraceMapConfig
from typing import List, Any

class CustomTraceMapGenerator(BaseTraceMapGenerator):
    """自定义地图生成器"""
    
    def __init__(self, config: TraceMapConfig = None):
        super().__init__(config)
        # 初始化自定义组件
    
    def generate(self, traceroute_data: List[List[Any]], hostname: str) -> str:
        """实现自定义的地图生成逻辑"""
        # 验证数据
        if not self.validate_traceroute_data(traceroute_data):
            raise ValueError("无效的路由追踪数据")
        
        # 实现自定义的生成逻辑
        # ...
        
        return html_file_path

# 使用自定义生成器
custom_generator = CustomTraceMapGenerator()
html_path = custom_generator.generate(converted_data, 'example.com')
```

### 自定义地理坐标转换

可以扩展`GeoConverter`类来实现自定义的坐标转换逻辑：

```python
from ui.tracemap import GeoConverter, TraceMapConfig

class CustomGeoConverter(GeoConverter):
    """自定义地理坐标转换器"""
    
    def lat_lng_to_svg(self, lat: float, lng: float) -> tuple:
        """自定义经纬度到SVG坐标的转换"""
        # 实现自定义的转换逻辑
        # ...
        return (x, y)
```

## 配置选项

`TraceMapConfig`类提供了以下配置选项：

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|-------|------|
| output_dir | str | './html' | HTML输出目录 |
| map_width | int | 800 | 地图宽度(像素) |
| map_height | int | 500 | 地图高度(像素) |
| china_lat_range | tuple | (18, 53) | 中国地图纬度范围 |
| china_lng_range | tuple | (73, 135) | 中国地图经度范围 |
| start_node_color | str | '#0000FF' | 起点颜色 |
| end_node_color | str | '#FF0000' | 终点颜色 |
| middle_node_color | str | '#00FF00' | 中间节点颜色 |
| route_path_color | str | '#000000' | 路径颜色 |
| node_radius | int | 5 | 节点半径(像素) |
| line_width | int | 2 | 路径线宽(像素) |
| title_font_size | int | 16 | 标题字体大小 |
| table_font_size | int | 12 | 表格字体大小 |
| background_color | str | '#f5f5f5' | 背景颜色 |

## 与原有API的兼容性

本框架保持了与原有API的兼容性，您可以直接替换原有导入：

```python
# 原有导入
from ui.tracemap_integration import generate_and_open_tracemap

# 替换为新的导入，无需修改其他代码
from ui.tracemap import generate_and_open_tracemap
```

## 目录结构

```
ui/tracemap/
├── __init__.py        # 包初始化文件
├── base_generator.py  # 基础生成器抽象类
├── svg_generator.py   # SVG地图生成器实现
├── geo_converter.py   # 地理坐标转换器
├── template_renderer.py # HTML模板渲染器
├── config.py          # 配置类
├── utils.py           # 工具函数
├── README.md          # 本说明文档
└── test_tracemap.py   # 测试脚本
```

## 注意事项

1. 确保输出目录有写入权限
2. 地图使用的是简化的中国地图轮廓
3. 路由节点的地理位置是通过IP地址生成的近似位置，非精确地理定位
4. 生成的HTML文件可以在任何现代浏览器中打开查看

## 扩展建议

1. 添加真实的IP地理位置数据库支持
2. 增加世界地图或其他区域地图的支持
3. 添加更多的交互功能，如缩放、平移等
4. 支持更多的可视化样式和主题
