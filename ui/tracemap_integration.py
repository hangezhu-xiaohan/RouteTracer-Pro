# -- coding: utf-8 --
"""traceMap集成模块，用于将路由追踪结果转换为地图可视化"""

import os
import sys
import json
import datetime
import webbrowser
from pathlib import Path

# 添加项目根目录到Python路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# 简单检查tracemap目录是否存在
tracemap_dir = os.path.join(base_dir, 'tracemap')
TRACEMAP_AVAILABLE = os.path.exists(tracemap_dir) and os.path.exists(os.path.join(tracemap_dir, '__init__.py'))

# 如果tracemap目录存在，尝试导入必要的函数
try:
    if TRACEMAP_AVAILABLE:
        # 导入必要的函数（这里暂时用模拟函数，后续根据实际需要修改）
        # 实际使用时需要导入tracemap模块中的draw函数
        print("traceMap模块准备就绪")
    else:
        print(f"tracemap模块不可用，目录不存在或缺少必要文件: {tracemap_dir}")
except Exception as e:
    print(f"初始化traceMap模块时出错: {e}")
    TRACEMAP_AVAILABLE = False


def convert_traceroute_data_for_tracemap(trace_data):
    """
    将RouteTracer Pro的路由追踪结果转换为traceMap所需的格式

    :param trace_data: RouteTracer Pro的路由追踪结果列表
                       - 标准格式: [(hop, ip, delay, location), ...]
                       - NextTrace格式: [(hop, ip, delay, location, isp, (lat, lng)), ...]
    :return: traceMap需要的经纬度信息列表，格式为[[lat, lng, city, owner, asnumber, ip, whois, ttl, rtt, hostname], ...]
    """
    result = []
    
    # 确保目录存在
    output_dir = Path('./html')
    output_dir.mkdir(exist_ok=True)
    
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
                
                # 检查是否是NextTrace格式（包含经纬度信息）
                if len(item) >= 6 and isinstance(item[5], (tuple, list)) and len(item[5]) >= 2:
                    # 使用NextTrace提供的经纬度信息
                    lat, lng = item[5]
                    # 设置城市信息 - 从location字段获取，或者设置默认值
                    city = location if location else "未知城市"
                    # 如果有ISP信息
                    if len(item) > 4:
                        isp = item[4]
                    else:
                        isp = ""
                else:
                    # 从location字符串中提取ISP信息
                    isp = ""
                    city = location
                    
                    if location and '(' in location and ')' in location:
                        isp_start = location.find('(') + 1
                        isp_end = location.find(')')
                        if isp_end > isp_start:
                            isp = location[isp_start:isp_end]
                            city = location[:isp_start-1].strip()
                    
                    # 简单的经纬度估算（当没有NextTrace经纬度信息时使用）
                    # 从ip地址生成一些伪随机但固定的经纬度
                    lat = 30.0 + (hash(ip) % 20) - 10  # 大致范围在20-40度之间
                    lng = 100.0 + (hash(ip) % 60) - 30  # 大致范围在70-130度之间
                    
                    # 确保经纬度在有效范围内
                    lat = max(-90, min(90, lat))
                    lng = max(-180, min(180, lng))
            else:
                continue
            
            if hop <= 0 or not ip or delay <= 0:
                continue
            
            # 设置所有者为ISP
            owner = isp
        except Exception as e:
            print(f"处理路由节点时出错: {e}")
            continue
        
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


def generate_tracemap(trace_data, hostname, output_dir=None):
    """
    生成路由追踪地图可视化
    
    :param trace_data: RouteTracer Pro的路由追踪结果列表
    :param hostname: 目标主机名
    :param output_dir: 输出目录，默认为当前目录下的html文件夹
    :return: 生成的HTML文件路径
    """
    # 如果没有路由数据，返回错误
    if not trace_data:
        raise ValueError("没有有效的路由追踪数据")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = Path('./html')
    else:
        output_dir = Path(output_dir)
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 转换数据格式
    converted_data = convert_traceroute_data_for_tracemap(trace_data)
    
    if not converted_data:
        raise ValueError("无法转换路由追踪数据为地图格式")
    
    # 生成文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"traceroute_{hostname.replace('.', '_')}_{timestamp}.html"
    html_path = os.path.join(str(output_dir), filename)
    
    # 生成模拟的HTML文件（不依赖tracemap模块）
    try:
        generate_mock_tracemap_html(converted_data, hostname, html_path)
        print(f"模拟traceMap HTML已生成: {html_path}")
        return html_path
    except Exception as e:
        raise RuntimeError(f"生成traceMap失败: {str(e)}")

def generate_mock_tracemap_html(traceroute_data, hostname, output_path):
    """
    生成纯SVG中国地图可视化的HTML文件，不依赖外部地图API
    
    :param traceroute_data: 转换后的路由追踪数据
    :param hostname: 目标主机名
    :param output_path: 输出HTML文件路径
    """
    # 将经纬度转换为SVG坐标的函数
    def lat_lng_to_svg(lat, lng, width=800, height=500):
        # 中国地图的大致经纬度范围
        # 经度范围: 73°E - 135°E
        # 纬度范围: 18°N - 53°N
        min_lng, max_lng = 73, 135
        min_lat, max_lat = 18, 53
        
        # 计算SVG坐标（做一些简单的缩放和偏移）
        # 注意：这里使用了简化的映射，实际应用可能需要更复杂的投影
        x = ((lng - min_lng) / (max_lng - min_lng)) * width
        # 纬度需要反转，因为SVG的y轴向下
        y = height - ((lat - min_lat) / (max_lat - min_lat)) * height
        
        # 确保坐标在SVG范围内
        x = max(0, min(x, width))
        y = max(0, min(y, height))
        
        return x, y
    
    # 转换路由节点为SVG坐标
    svg_points = []
    for i, node in enumerate(traceroute_data):
        if len(node) >= 2:
            lat, lng = node[0], node[1]
            x, y = lat_lng_to_svg(lat, lng)
            
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
    
    # 生成路径数据
    path_data = ' '.join([f'M {p["x"]},{p["y"]} L {p["x"]},{p["y"]}' for p in svg_points])
    if len(svg_points) > 1:
        path_data = f'M {svg_points[0]["x"]},{svg_points[0]["y"]}' + ''.join([f' L {p["x"]},{p["y"]}' for p in svg_points[1:]])
    
    # 生成HTML内容
    html_content = '<!DOCTYPE html>\n'
    html_content += '<html lang="zh-CN">\n'
    html_content += '<head>\n'
    html_content += f'    <meta charset="UTF-8">\n'
    html_content += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html_content += f'    <title>路由追踪地图可视化 - {hostname}</title>\n'
    html_content += '    <style>\n'
    html_content += '        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f0f0; }\n'
    html_content += '        h1 { color: #333; text-align: center; }\n'
    html_content += '        .route-table { width: 100%; border-collapse: collapse; margin: 20px 0; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }\n'
    html_content += '        .route-table th, .route-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }\n'
    html_content += '        .route-table th { background-color: #4CAF50; color: white; }\n'
    html_content += '        .route-table tr:nth-child(even) { background-color: #f2f2f2; }\n'
    html_content += '        .map-container { width: 100%; max-width: 800px; margin: 20px auto; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }'
    html_content += '        svg { width: 100%; height: 500px; display: block; background-color: #fff; }\n'
    html_content += '        .map-legend { padding: 10px 20px; background-color: #fff; border-top: 1px solid #ddd; font-size: 14px; color: #666; }\n'
    html_content += '        .footer { text-align: center; margin-top: 30px; color: #666; }\n'
    html_content += '        .tooltip { position: absolute; background-color: rgba(0, 0, 0, 0.8); color: white; padding: 10px; border-radius: 4px; font-size: 12px; pointer-events: none; display: none; z-index: 1000; }\n'
    html_content += '        .node { cursor: pointer; }\n'
    html_content += '        .node:hover { filter: brightness(1.2); }\n'
    html_content += '    </style>\n'
    html_content += '</head>\n'
    html_content += '<body>\n'
    html_content += f'    <h1>路由追踪地图可视化 - {hostname}</h1>'
    html_content += '    <div class="map-container">'
    html_content += '        <svg id="map" viewBox="0 0 800 500">'
    html_content += '            <!-- 中国地图轮廓 -->'
    html_content += '            <path d="M 425,120 L 430,115 L 435,110 L 440,105 L 445,100 L 450,95 L 455,90 L 460,85 L 465,80 L 470,75 L 475,70 L 480,65 L 485,60 L 490,55 L 495,50 L 500,45 L 505,40 L 510,35 L 515,30 L 520,25 L 525,20 L 530,15 L 535,10 L 540,5 L 545,0 L 550,0 L 555,5 L 560,10 L 565,15 L 570,20 L 575,25 L 580,30 L 585,35 L 590,40 L 595,45 L 600,50 L 605,55 L 610,60 L 615,65 L 620,70 L 625,75 L 630,80 L 635,85 L 640,90 L 645,95 L 650,100 L 655,105 L 660,110 L 665,115 L 670,120 L 675,125 L 680,130 L 685,135 L 690,140 L 695,145 L 700,150 L 705,155 L 710,160 L 715,165 L 720,170 L 725,175 L 730,180 L 735,185 L 740,190 L 745,195 L 750,200 L 755,205 L 760,210 L 765,215 L 770,220 L 775,225 L 780,230 L 785,235 L 790,240 L 795,245 L 800,250 L 800,255 L 795,260 L 790,265 L 785,270 L 780,275 L 775,280 L 770,285 L 765,290 L 760,295 L 755,300 L 750,305 L 745,310 L 740,315 L 735,320 L 730,325 L 725,330 L 720,335 L 715,340 L 710,345 L 705,350 L 700,355 L 695,360 L 690,365 L 685,370 L 680,375 L 675,380 L 670,385 L 665,390 L 660,395 L 655,400 L 650,405 L 645,410 L 640,415 L 635,420 L 630,425 L 625,430 L 620,435 L 615,440 L 610,445 L 605,450 L 600,455 L 595,460 L 590,465 L 585,470 L 580,475 L 575,480 L 570,485 L 565,490 L 560,495 L 555,500 L 550,500 L 545,495 L 540,490 L 535,485 L 530,480 L 525,475 L 520,470 L 515,465 L 510,460 L 505,455 L 500,450 L 495,445 L 490,440 L 485,435 L 480,430 L 475,425 L 470,420 L 465,415 L 460,410 L 455,405 L 450,400 L 445,395 L 440,390 L 435,385 L 430,380 L 425,375 L 420,370 L 415,365 L 410,360 L 405,355 L 400,350 L 395,345 L 390,340 L 385,335 L 380,330 L 375,325 L 370,320 L 365,315 L 360,310 L 355,305 L 350,300 L 345,295 L 340,290 L 335,285 L 330,280 L 325,275 L 320,270 L 315,265 L 310,260 L 305,255 L 300,250 L 295,245 L 290,240 L 285,235 L 280,230 L 275,225 L 270,220 L 265,215 L 260,210 L 255,205 L 250,200 L 245,195 L 240,190 L 235,185 L 230,180 L 225,175 L 220,170 L 215,165 L 210,160 L 205,155 L 200,150 L 195,145 L 190,140 L 185,135 L 180,130 L 175,125 L 170,120 L 165,115 L 160,110 L 155,105 L 150,100 L 145,95 L 140,90 L 135,85 L 130,80 L 125,75 L 120,70 L 115,65 L 110,60 L 105,55 L 100,50 L 95,45 L 90,40 L 85,35 L 80,30 L 75,25 L 70,20 L 65,15 L 60,10 L 55,5 L 50,0 L 0,0 L 0,500 L 50,500 L 100,500 L 150,500 L 200,500 L 250,500 L 300,500 L 350,500 L 400,500 L 450,500 L 500,500 L 550,500 L 600,500 L 650,500 L 700,500 L 750,500 L 800,500 L 800,250 L 795,245 L 790,240 L 785,235 L 780,230 L 775,225 L 770,220 L 765,215 L 760,210 L 755,205 L 750,200 L 745,195 L 740,190 L 735,185 L 730,180 L 725,175 L 720,170 L 715,165 L 710,160 L 705,155 L 700,150 L 695,145 L 690,140 L 685,135 L 680,130 L 675,125 L 670,120 L 665,115 L 660,110 L 655,105 L 650,100 L 645,95 L 640,90 L 635,85 L 630,80 L 625,75 L 620,70 L 615,65 L 610,60 L 605,55 L 600,50 L 595,45 L 590,40 L 585,35 L 580,30 L 575,25 L 570,20 L 565,15 L 560,10 L 555,5 L 550,0 L 545,0 L 540,5 L 535,10 L 530,15 L 525,20 L 520,25 L 515,30 L 510,35 L 505,40 L 500,45 L 495,50 L 490,55 L 485,60 L 480,65 L 475,70 L 470,75 L 465,80 L 460,85 L 455,90 L 450,95 L 445,100 L 440,105 L 435,110 L 430,115 L 425,120 Z" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>\n'
    html_content += '            <!-- 路由路径 -->'
    html_content += f'            <path id="route-path" d="{path_data}" fill="none" stroke="#FF9800" stroke-width="2" stroke-dasharray="5,3"/>'
    html_content += '            <!-- 路由节点 -->'    
    # 添加SVG节点和表格数据
    svg_nodes = ""
    table_rows = ""
    for i, (node, svg_point) in enumerate(zip(traceroute_data, svg_points), 1):
        # 获取节点信息
        ip = node[5] if len(node) > 5 else 'N/A'
        city = node[2] if len(node) > 2 else 'N/A'
        owner = node[3] if len(node) > 3 else 'N/A'
        rtt = node[8] if len(node) > 8 else 'N/A'
        
        # 设置节点颜色
        color = "#4CAF50"  # 中间节点默认绿色
        if svg_point['type'] == "start":
            color = "#2196F3"  # 起始节点蓝色
        elif svg_point['type'] == "end":
            color = "#F44336"  # 终点节点红色
        
        # 创建SVG节点
        svg_nodes += '<g class="node" data-hop="{0}" data-ip="{1}" data-city="{2}" data-owner="{3}" data-rtt="{4}">'.format(i, ip, city, owner, rtt)
        svg_nodes += '<circle cx="{0}" cy="{1}" r="8" fill="{2}" stroke="#fff" stroke-width="2"/>'.format(svg_point['x'], svg_point['y'], color)
        svg_nodes += '<text x="{0}" y="{1}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="12" font-weight="bold">{2}</text>'.format(svg_point['x'], svg_point['y'], i)
        svg_nodes += '</g>'
        
        # 创建表格行
        table_rows += '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>'.format(i, ip, city, owner, rtt)
    
    # 完成HTML内容
    html_content += svg_nodes + '</svg>'
    html_content += '<div class="map-legend">'
    html_content += '<span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:#2196F3;border-radius:50%;margin-right:5px;"></span>起始节点</span>'
    html_content += '<span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:#F44336;border-radius:50%;margin-right:5px;"></span>终点节点</span>'
    html_content += '<span style="display:inline-block;margin-right:15px;"><span style="display:inline-block;width:16px;height:16px;background:#4CAF50;border-radius:50%;margin-right:5px;"></span>中间节点</span>'
    html_content += '<span style="display:inline-block;"><span style="display:inline-block;width:20px;height:2px;background:#FF9800;margin-right:5px;"></span>路由路径</span>'
    html_content += '</div>'
    html_content += '</div>'
    html_content += '<h2>路由节点详情</h2>'
    html_content += '<table class="route-table">'
    html_content += '<tr><th>序号</th><th>IP地址</th><th>城市</th><th>所有者</th><th>延迟(ms)</th></tr>'
    
    # 添加表格行
    html_content += table_rows
    html_content += '</table>'
    html_content += '<div class="footer">'
    html_content += '<p>生成时间: ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '</p>'
    html_content += '<p>包含 ' + str(len(traceroute_data)) + ' 个路由节点的可视化</p>'
    html_content += '</div>'
    html_content += '<div class="tooltip" id="node-tooltip"></div>'
    html_content += '<script type="text/javascript">'
    html_content += 'const tooltip = document.getElementById("node-tooltip");'
    html_content += 'document.querySelectorAll(".node").forEach(node => {'
    html_content += 'node.addEventListener("mouseover", function(e) {'
    html_content += 'const hop = this.getAttribute("data-hop");'
    html_content += 'const ip = this.getAttribute("data-ip");'
    html_content += 'const city = this.getAttribute("data-city");'
    html_content += 'const owner = this.getAttribute("data-owner");'
    html_content += 'const rtt = this.getAttribute("data-rtt");'
    html_content += 'tooltip.innerHTML = "<p><strong>序号:</strong> " + hop + "</p><p><strong>IP地址:</strong> " + ip + "</p><p><strong>城市:</strong> " + city + "</p><p><strong>所有者:</strong> " + owner + "</p><p><strong>延迟:</strong> " + rtt + "ms</p>";'
    html_content += 'tooltip.style.display = "block";'
    html_content += 'updateTooltipPosition(e);'
    html_content += '});'
    html_content += 'node.addEventListener("mousemove", updateTooltipPosition);'
    html_content += 'node.addEventListener("mouseout", function() { tooltip.style.display = "none"; });'
    html_content += '});'
    html_content += 'function updateTooltipPosition(e) {'
    html_content += 'const tooltipWidth = tooltip.offsetWidth;'
    html_content += 'const tooltipHeight = tooltip.offsetHeight;'
    html_content += 'let left = e.clientX + 10;'
    html_content += 'let top = e.clientY - 10;'
    html_content += 'if (left + tooltipWidth > window.innerWidth) { left = e.clientX - tooltipWidth - 10; }'
    html_content += 'if (top < 0) { top = 10; }'
    html_content += 'tooltip.style.left = left + "px";'
    html_content += 'tooltip.style.top = top + "px";'
    html_content += '}'
    html_content += '</script>'
    html_content += '</body></html>'
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_and_open_tracemap(trace_data, hostname):
    """
    生成路由追踪地图并在浏览器中打开
    
    :param trace_data: RouteTracer Pro的路由追踪结果列表
    :param hostname: 目标主机名
    :return: 生成的HTML文件路径
    """
    html_path = generate_tracemap(trace_data, hostname)
    
    # 在浏览器中打开生成的HTML文件
    try:
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
    except Exception as e:
        print(f"无法在浏览器中打开地图: {str(e)}")
    
    return html_path


# 用于测试的函数
def test_tracemap_integration():
    """
    测试traceMap集成功能
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
        html_path = generate_and_open_tracemap(mock_trace_data, 'google.com')
        print(f"traceMap已生成: {html_path}")
        return html_path
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None


if __name__ == '__main__':
    test_tracemap_integration()
