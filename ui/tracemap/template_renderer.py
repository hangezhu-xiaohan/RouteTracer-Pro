# -- coding: utf-8 --
"""模板渲染器

用于渲染HTML模板生成可视化页面
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from .config import TraceMapConfig


class TemplateRenderer:
    """HTML模板渲染器"""
    
    def __init__(self, config: TraceMapConfig = None):
        """初始化模板渲染器
        
        :param config: TraceMap配置对象，如果为None则使用默认配置
        """
        self.config = config or TraceMapConfig()
        self._default_template = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """获取默认的HTML模板
        
        :return: 默认HTML模板字符串
        """
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>路由追踪地图可视化 - {{hostname}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f0f0; }
        h1 { color: #333; text-align: center; }
        .route-table { width: 100%; border-collapse: collapse; margin: 20px 0; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .route-table th, .route-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .route-table th { background-color: #4CAF50; color: white; }
        .route-table tr:nth-child(even) { background-color: #f2f2f2; }
        .map-container { width: 100%; max-width: {{map_width}}px; margin: 20px auto; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        svg { width: 100%; height: {{map_height}}px; display: block; background-color: #fff; }
        .map-legend { padding: 10px 20px; background-color: #fff; border-top: 1px solid #ddd; font-size: 14px; color: #666; }
        .footer { text-align: center; margin-top: 30px; color: #666; }
        .tooltip { position: absolute; background-color: rgba(0, 0, 0, 0.8); color: white; padding: 10px; border-radius: 4px; font-size: 12px; pointer-events: none; display: none; z-index: 1000; }
        .node { cursor: pointer; }
        .node:hover { filter: brightness(1.2); }
    </style>
</head>
<body>
    <h1>路由追踪地图可视化 - {{hostname}}</h1>
    <div class="map-container">
        <svg id="map" viewBox="0 0 {{map_width}} {{map_height}}">
            <!-- 中国地图轮廓 -->
            {{china_map_svg}}
            <!-- 路由路径 -->
            <path id="route-path" d="{{path_data}}" fill="none" stroke="{{route_path_color}}" stroke-width="{{stroke_width}}" stroke-dasharray="5,3"/>
            <!-- 路由节点 -->
            {{svg_nodes}}
        </svg>
        {% if show_legend %}
        <div class="map-legend">
            <span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:{{start_node_color}};border-radius:50%;margin-right:5px;"></span>起始节点</span>
            <span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:{{end_node_color}};border-radius:50%;margin-right:5px;"></span>终点节点</span>
            <span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:{{middle_node_color}};border-radius:50%;margin-right:5px;"></span>中间节点</span>
            <span style="display:inline-block;"><span style="display:inline-block;width:20px;height:2px;background:{{route_path_color}};margin-right:5px;"></span>路由路径</span>
        </div>
        {% endif %}
    </div>
    {% if show_table %}
    <h2>路由节点详情</h2>
    <table class="route-table">
        <tr><th>序号</th><th>IP地址</th><th>城市</th><th>所有者</th><th>延迟(ms)</th></tr>
        {{table_rows}}
    </table>
    {% endif %}
    <div class="footer">
        <p>生成时间: {{generation_time}}</p>
        <p>包含 {{node_count}} 个路由节点的可视化</p>
    </div>
    <div class="tooltip" id="node-tooltip"></div>
    <script type="text/javascript">
        const tooltip = document.getElementById("node-tooltip");
        document.querySelectorAll(".node").forEach(node => {
            node.addEventListener("mouseover", function(e) {
                const hop = this.getAttribute("data-hop");
                const ip = this.getAttribute("data-ip");
                const city = this.getAttribute("data-city");
                const owner = this.getAttribute("data-owner");
                const rtt = this.getAttribute("data-rtt");
                tooltip.innerHTML = "<p><strong>序号:</strong> " + hop + "</p><p><strong>IP地址:</strong> " + ip + "</p><p><strong>城市:</strong> " + city + "</p><p><strong>所有者:</strong> " + owner + "</p><p><strong>延迟:</strong> " + rtt + "ms</p>";
                tooltip.style.display = "block";
                updateTooltipPosition(e);
            });
            node.addEventListener("mousemove", updateTooltipPosition);
            node.addEventListener("mouseout", function() { tooltip.style.display = "none"; });
        });
        function updateTooltipPosition(e) {
            const tooltipWidth = tooltip.offsetWidth;
            const tooltipHeight = tooltip.offsetHeight;
            let left = e.clientX + 10;
            let top = e.clientY - 10;
            if (left + tooltipWidth > window.innerWidth) { left = e.clientX - tooltipWidth - 10; }
            if (top < 0) { top = 10; }
            tooltip.style.left = left + "px";
            tooltip.style.top = top + "px";
        }
    </script>
</body>
</html>'''
    
    def _get_template_file_path(self) -> Optional[str]:
        """获取模板文件路径
        
        :return: 模板文件路径，如果不存在则返回None
        """
        if not self.config.template_dir:
            return None
        
        template_path = os.path.join(self.config.template_dir, self.config.template_file)
        if os.path.exists(template_path):
            return template_path
        return None
    
    def _load_template(self) -> str:
        """加载模板内容
        
        :return: 模板字符串
        """
        template_path = self._get_template_file_path()
        if template_path:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"加载模板文件失败: {e}，使用默认模板")
        
        return self._default_template
    
    def _get_china_map_svg(self) -> str:
        """获取中国地图SVG路径
        
        :return: 中国地图SVG路径字符串
        """
        # 简化的中国地图轮廓
        return '<path d="M 425,120 L 430,115 L 435,110 L 440,105 L 445,100 L 450,95 L 455,90 L 460,85 L 465,80 L 470,75 L 475,70 L 480,65 L 485,60 L 490,55 L 495,50 L 500,45 L 505,40 L 510,35 L 515,30 L 520,25 L 525,20 L 530,15 L 535,10 L 540,5 L 545,0 L 550,0 L 555,5 L 560,10 L 565,15 L 570,20 L 575,25 L 580,30 L 585,35 L 590,40 L 595,45 L 600,50 L 605,55 L 610,60 L 615,65 L 620,70 L 625,75 L 630,80 L 635,85 L 640,90 L 645,95 L 650,100 L 655,105 L 660,110 L 665,115 L 670,120 L 675,125 L 680,130 L 685,135 L 690,140 L 695,145 L 700,150 L 705,155 L 710,160 L 715,165 L 720,170 L 725,175 L 730,180 L 735,185 L 740,190 L 745,195 L 750,200 L 755,205 L 760,210 L 765,215 L 770,220 L 775,225 L 780,230 L 785,235 L 790,240 L 795,245 L 800,250 L 800,255 L 795,260 L 790,265 L 785,270 L 780,275 L 775,280 L 770,285 L 765,290 L 760,295 L 755,300 L 750,305 L 745,310 L 740,315 L 735,320 L 730,325 L 725,330 L 720,335 L 715,340 L 710,345 L 705,350 L 700,355 L 695,360 L 690,365 L 685,370 L 680,375 L 675,380 L 670,385 L 665,390 L 660,395 L 655,400 L 650,405 L 645,410 L 640,415 L 635,420 L 630,425 L 625,430 L 620,435 L 615,440 L 610,445 L 605,450 L 600,455 L 595,460 L 590,465 L 585,470 L 580,475 L 575,480 L 570,485 L 565,490 L 560,495 L 555,500 L 550,500 L 545,495 L 540,490 L 535,485 L 530,480 L 525,475 L 520,470 L 515,465 L 510,460 L 505,455 L 500,450 L 495,445 L 490,440 L 485,435 L 480,430 L 475,425 L 470,420 L 465,415 L 460,410 L 455,405 L 450,400 L 445,395 L 440,390 L 435,385 L 430,380 L 425,375 L 420,370 L 415,365 L 410,360 L 405,355 L 400,350 L 395,345 L 390,340 L 385,335 L 380,330 L 375,325 L 370,320 L 365,315 L 360,310 L 355,305 L 350,300 L 345,295 L 340,290 L 335,285 L 330,280 L 325,275 L 320,270 L 315,265 L 310,260 L 305,255 L 300,250 L 295,245 L 290,240 L 285,235 L 280,230 L 275,225 L 270,220 L 265,215 L 260,210 L 255,205 L 250,200 L 245,195 L 240,190 L 235,185 L 230,180 L 225,175 L 220,170 L 215,165 L 210,160 L 205,155 L 200,150 L 195,145 L 190,140 L 185,135 L 180,130 L 175,125 L 170,120 L 165,115 L 160,110 L 155,105 L 150,100 L 145,95 L 140,90 L 135,85 L 130,80 L 125,75 L 120,70 L 115,65 L 110,60 L 105,55 L 100,50 L 95,45 L 90,40 L 85,35 L 80,30 L 75,25 L 70,20 L 65,15 L 60,10 L 55,5 L 50,0 L 0,0 L 0,500 L 50,500 L 100,500 L 150,500 L 200,500 L 250,500 L 300,500 L 350,500 L 400,500 L 450,500 L 500,500 L 550,500 L 600,500 L 650,500 L 700,500 L 750,500 L 800,500 L 800,250 L 795,245 L 790,240 L 785,235 L 780,230 L 775,225 L 770,220 L 765,215 L 760,210 L 755,205 L 750,200 L 745,195 L 740,190 L 735,185 L 730,180 L 725,175 L 720,170 L 715,165 L 710,160 L 705,155 L 700,150 L 695,145 L 690,140 L 685,135 L 680,130 L 675,125 L 670,120 L 665,115 L 660,110 L 655,105 L 650,100 L 645,95 L 640,90 L 635,85 L 630,80 L 625,75 L 620,70 L 615,65 L 610,60 L 605,55 L 600,50 L 595,45 L 590,40 L 585,35 L 580,30 L 575,25 L 570,20 L 565,15 L 560,10 L 555,5 L 550,0 L 545,0 L 540,5 L 535,10 L 530,15 L 525,20 L 520,25 L 515,30 L 510,35 L 505,40 L 500,45 L 495,50 L 490,55 L 485,60 L 480,65 L 475,70 L 470,75 L 465,80 L 460,85 L 455,90 L 450,95 L 445,100 L 440,105 L 435,110 L 430,115 L 425,120 Z" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>'
    
    def _render_svg_nodes(self, svg_points: List[Dict[str, Any]]) -> str:
        """渲染SVG节点
        
        :param svg_points: SVG点数据列表
        :return: SVG节点字符串
        """
        svg_nodes = []
        for i, point in enumerate(svg_points):
            # 设置节点颜色
            if point['type'] == "start":
                color = self.config.start_node_color
            elif point['type'] == "end":
                color = self.config.end_node_color
            else:
                color = self.config.middle_node_color
            
            # 创建SVG节点
            node_info = point['info']
            svg_node = f'''<g class="node" data-hop="{node_info['hop']}" data-ip="{node_info['ip']}" data-city="{node_info['city']}" data-owner="{node_info['owner']}" data-rtt="{node_info['rtt']}">'''
            svg_node += f'''<circle cx="{point['x']}" cy="{point['y']}" r="{self.config.node_radius}" fill="{color}" stroke="#fff" stroke-width="2"/>'''
            svg_node += f'''<text x="{point['x']}" y="{point['y']}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="{self.config.font_size}" font-weight="bold">{node_info['hop']}</text>'''
            svg_node += '''</g>'''
            svg_nodes.append(svg_node)
        
        return ''.join(svg_nodes)
    
    def _render_table_rows(self, traceroute_data: List[List[Any]]) -> str:
        """渲染表格行
        
        :param traceroute_data: 路由追踪数据
        :return: 表格行HTML字符串
        """
        rows = []
        for i, node in enumerate(traceroute_data):
            ip = node[5] if len(node) > 5 else 'N/A'
            city = node[2] if len(node) > 2 else 'N/A'
            owner = node[3] if len(node) > 3 else 'N/A'
            rtt = node[8] if len(node) > 8 else 'N/A'
            hop = node[7] if len(node) > 7 else str(i+1)
            
            row = f'''<tr><td>{hop}</td><td>{ip}</td><td>{city}</td><td>{owner}</td><td>{rtt}</td></tr>'''
            rows.append(row)
        
        return ''.join(rows)
    
    def render(self, traceroute_data: List[List[Any]], hostname: str, svg_points: List[Dict[str, Any]], path_data: str) -> str:
        """渲染HTML内容
        
        :param traceroute_data: 路由追踪数据
        :param hostname: 目标主机名
        :param svg_points: SVG点数据列表
        :param path_data: SVG路径数据
        :return: 渲染后的HTML字符串
        """
        template = self._load_template()
        
        # 准备渲染数据
        context = {
            'hostname': hostname,
            'map_width': self.config.map_width,
            'map_height': self.config.map_height,
            'route_path_color': self.config.route_path_color,
            'start_node_color': self.config.start_node_color,
            'middle_node_color': self.config.middle_node_color,
            'end_node_color': self.config.end_node_color,
            'stroke_width': self.config.stroke_width,
            'show_legend': self.config.show_legend,
            'show_table': self.config.show_table,
            'china_map_svg': self._get_china_map_svg(),
            'path_data': path_data,
            'svg_nodes': self._render_svg_nodes(svg_points),
            'table_rows': self._render_table_rows(traceroute_data),
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'node_count': len(traceroute_data)
        }
        
        # 简单的模板替换
        html_content = template
        for key, value in context.items():
            # 处理条件表达式
            if key.startswith('show_'):
                placeholder = f'{{% if {key} %}}'
                if value:
                    # 保留内容
                    html_content = html_content.replace(placeholder, '')
                    # 移除结束标签
                    end_placeholder = f'{{% endif %}}'
                    html_content = html_content.replace(end_placeholder, '')
                else:
                    # 移除条件块
                    start_index = html_content.find(placeholder)
                    if start_index != -1:
                        end_index = html_content.find('{% endif %}', start_index)
                        if end_index != -1:
                            html_content = html_content[:start_index] + html_content[end_index + len('{% endif %}'):]
            else:
                # 替换变量
                html_content = html_content.replace(f'{{{{{key}}}}}', str(value))
        
        return html_content
    
    def save_to_file(self, html_content: str, filename: str) -> str:
        """保存HTML内容到文件
        
        :param html_content: HTML内容
        :param filename: 文件名
        :return: 文件保存路径
        """
        file_path = self.config.get_output_path(filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return file_path
