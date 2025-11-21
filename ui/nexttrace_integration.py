# -- coding: utf-8 --
"""NextTrace集成模块，用于通过子进程调用NextTrace工具

NextTrace是一个基于Go语言的开源路由追踪工具，具有地理位置可视化、ASN查询等功能
"""

import os
import sys
import json
import subprocess
import datetime
import platform
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# 添加项目根目录到Python路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)


class NextTraceIntegration:
    """NextTrace集成类，提供调用NextTrace工具的接口"""
    
    def __init__(self):
        """初始化NextTrace集成"""
        self.nexttrace_path = self._find_nexttrace()
        self.available = self.nexttrace_path is not None
        
        # 支持的输出格式
        self.supported_formats = ['json', 'plain', 'table']
        
        # 默认参数
        self.default_timeout = 200  # 默认超时时间200ms
        self.default_max_hops = 64  # 默认最大跳数64
        
        if not self.available:
            print("警告: 未找到NextTrace工具，请先安装NextTrace")
            print("安装方法: 从 https://github.com/nxtrace/NTrace-core/releases 下载对应平台的可执行文件")
            print("推荐: 将nexttrace可执行文件放置在项目的tools目录下")
            print("或: 将nexttrace可执行文件放置在PATH环境变量包含的目录中，或放置在项目根目录下")
    
    def _find_nexttrace(self) -> Optional[str]:
        """查找NextTrace可执行文件
        
        :return: NextTrace可执行文件路径，如果未找到则返回None
        """
        # 检查tools文件夹（推荐位置）
        tools_path = os.path.join(base_dir, 'tools', 'nexttrace')
        if platform.system() == 'Windows':
            tools_path += '.exe'
            if os.path.exists(tools_path):
                return tools_path
        else:
            if os.path.exists(tools_path):
                return tools_path
        
        # 检查项目根目录
        project_path = os.path.join(base_dir, 'nexttrace')
        if platform.system() == 'Windows':
            project_path += '.exe'
            if os.path.exists(project_path):
                return project_path
        else:
            if os.path.exists(project_path):
                return project_path
        
        # 在PATH环境变量中查找
        try:
            if platform.system() == 'Windows':
                # Windows下使用where命令
                result = subprocess.run(['where', 'nexttrace'], capture_output=True, text=True, check=False, **self._get_subprocess_kwargs())
                if result.returncode == 0:
                    # 返回第一个找到的路径
                    return result.stdout.strip().split('\n')[0]
            else:
                # Linux/macOS下使用which命令
                result = subprocess.run(['which', 'nexttrace'], capture_output=True, text=True, check=False, **self._get_subprocess_kwargs())
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception as e:
            print(f"查找NextTrace时出错: {e}")
        
        return None
    
    def is_available(self) -> bool:
        """检查NextTrace是否可用
        
        :return: True如果NextTrace可用，否则False
        """
        return self.available
    
    def _get_subprocess_kwargs(self):
        """获取subprocess调用的关键字参数，用于隐藏Windows控制台窗口"""
        kwargs = {
            'env': {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        }
        
        # 在Windows系统中隐藏控制台窗口
        if platform.system() == 'Windows':
            # 创建标志：隐藏窗口
            CREATE_NO_WINDOW = 0x08000000
            kwargs['creationflags'] = CREATE_NO_WINDOW
        
        return kwargs
    
    def run_traceroute(self, hostname: str, callback=None, ip_selection_callback=None, **kwargs) -> Dict[str, Any]:
        """运行NextTrace路由追踪
        
        :param hostname: 目标主机名或IP地址
        :param callback: 实时回调函数，接收(hop, ip, delay, location, isp)参数
        :param ip_selection_callback: IP选择回调函数，当遇到多个IP时调用
        :param kwargs: 其他参数
            - max_hops: 最大跳数，默认30
            - timeout: 超时时间（毫秒），默认5000ms (5秒)
            - format: 输出格式，默认'text'
            - lang: 语言，'en'或'cn'，默认'cn'
            - dns_query: 是否进行DNS查询，默认True
            - queries: 每跳探测次数，默认3
            - parallel_requests: 并发请求数，默认18
            - fast_trace: 快速追踪模式，默认False
            - tcp: 使用TCP模式，默认False
            - udp: 使用UDP模式，默认False
            - port: 目标端口，TCP默认80，UDP默认33494
            - no_rdns: 不解析反向DNS，默认False
            - always_rdns: 总是解析反向DNS，默认False
            - data_provider: 地理数据提供商，默认LeoMoeAPI
            - disable_map: 禁用地图显示，默认False
        
        :return: 包含路由追踪结果的字典
        :raises RuntimeError: 如果NextTrace不可用或执行失败
        """
        if not self.available:
            raise RuntimeError("NextTrace不可用，请先安装")
        
        # 参数处理
        max_hops = kwargs.get('max_hops', 64)
        timeout = kwargs.get('timeout', 200)  # NextTrace使用毫秒为单位，修改为200ms
        output_format = kwargs.get('format', 'text')  # 默认为文本格式
        lang = kwargs.get('lang', 'cn')  # 修正：使用'cn'而不是'zh'
        dns_query = kwargs.get('dns_query', True)
        queries = kwargs.get('queries', 3)
        parallel_requests = kwargs.get('parallel_requests', 18)
        fast_trace = kwargs.get('fast_trace', False)
        tcp_mode = kwargs.get('tcp', False)
        udp_mode = kwargs.get('udp', False)
        port = kwargs.get('port', None)
        no_rdns = kwargs.get('no_rdns', False)
        always_rdns = kwargs.get('always_rdns', False)
        data_provider = kwargs.get('data_provider', None)
        disable_map = kwargs.get('disable_map', False)
        
        # 构建命令参数
        cmd = [
            self.nexttrace_path,
            hostname,
            '-m', str(max_hops),
            '--timeout', str(timeout),  # 使用毫秒
            '-C',  # 禁用彩色输出
            '-g', lang,
            '-q', str(queries),
            '--parallel-requests', str(parallel_requests)
        ]
        
        # 添加可选参数
        if fast_trace:
            cmd.append('-F')  # 快速追踪模式
        
        if tcp_mode:
            cmd.append('-T')  # TCP模式
            if port:
                cmd.extend(['-p', str(port)])
        elif udp_mode:
            cmd.append('-U')  # UDP模式
            if port:
                cmd.extend(['-p', str(port)])
        
        if no_rdns:
            cmd.append('-n')  # 不解析反向DNS
        elif always_rdns:
            cmd.append('-a')  # 总是解析反向DNS
        
        if data_provider:
            cmd.extend(['-d', data_provider])
        
        if disable_map:
            cmd.append('-M')  # 禁用地图显示
        
        try:
            print(f"执行NextTrace命令: {' '.join(cmd)}")
            
            # 如果提供了回调函数，使用实时处理模式
            if callback:
                return self._run_with_realtime_callback(cmd, callback, max_hops, timeout, ip_selection_callback)
            else:
                # 执行命令，使用正确的编码处理
                subprocess_kwargs = self._get_subprocess_kwargs()
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    encoding='utf-8',  # 修改为UTF-8编码
                    errors='replace',  # 处理无法解码的字符
                    check=True,
                    timeout=max_hops * (timeout / 1000) + 30,  # 总超时时间，转换为秒
                    **subprocess_kwargs
                )
                
                # 解析文本输出
                if output_format == 'text' or output_format == 'json':
                    # 无论请求什么格式，我们都解析文本输出
                    return self._parse_text_output(result.stdout)
                else:
                    # 对于其他格式，返回原始输出
                    return {"output": result.stdout, "format": output_format}
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"NextTrace执行失败: {e.stderr or e.stdout}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"NextTrace执行超时")
        except Exception as e:
            raise RuntimeError(f"NextTrace执行出错: {e}")
    
    def _run_with_realtime_callback(self, cmd, callback, max_hops, timeout, ip_selection_callback=None):
        """使用实时回调模式执行NextTrace命令
        
        :param cmd: NextTrace命令列表
        :param callback: 回调函数
        :param max_hops: 最大跳数
        :param timeout: 超时时间
        :param ip_selection_callback: IP选择回调函数
        :return: 最终结果字典，包含MapTrace URL
        """
        import re
        
        # 启动子进程
        try:
            # 启动进程，使用实时输出
            subprocess_kwargs = self._get_subprocess_kwargs()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,  # 添加标准输入支持
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                **subprocess_kwargs
            )
        except Exception as e:
            raise RuntimeError(f"启动NextTrace进程失败: {e}")
        
        hops = []
        current_hop = None
        line_buffer = ""
        processed_hops = set()  # 跟踪已处理的跳数，避免重复回调
        ip_selection_mode = False  # 标记是否处于IP选择模式
        ip_options = []  # 存储IP选项
        waiting_for_selection = False  # 标记是否正在等待用户选择
        ip_selection_timeout = 5  # IP选择超时时间（秒）
        ip_selection_start_time = None  # IP选择开始时间
        maptrace_url = None  # 存储MapTrace URL
        
        try:
            # 逐行读取输出
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                print(f"NextTrace输出: {line}")  # 调试输出
                
                # 检测IP选择界面
                if 'Please Choose the IP You Want To TraceRoute' in line:
                    ip_selection_mode = True
                    ip_options = []
                    waiting_for_selection = True
                    ip_selection_start_time = time.time()
                    print("检测到IP选择界面，正在收集IP选项...")
                    continue
                
                # 处理IP选择选项
                if ip_selection_mode and waiting_for_selection and line:
                    # 解析IP选项行
                    if line[0].isdigit() and ('.' in line or ':' in line):
                        # 格式可能是: "0. 180.101.51.73" 或 "0) 180.101.49.11 (IPv4)"
                        parts = re.split(r'[.)]\s*', line, 1)
                        if len(parts) >= 2:
                            try:
                                index = int(parts[0].strip())
                                ip_info = parts[1].strip()
                                
                                # 提取IP地址和类型
                                ip_type = "IPv4" if '.' in ip_info else "IPv6"
                                # 移除可能的类型标识
                                ip_address = ip_info.split()[0] if ip_info.split() else ip_info
                                
                                ip_options.append({
                                    "index": index,
                                    "ip": ip_address,
                                    "type": ip_type,
                                    "location": "未知"
                                })
                                
                                print(f"发现IP选项 {index}: {ip_address} ({ip_type})")
                                
                                # 如果收集到4个IP选项，立即触发选择
                                if len(ip_options) >= 4:
                                    print("已收集到4个IP选项，立即触发选择...")
                                    waiting_for_selection = False
                                    
                                    # 立即处理IP选择
                                    if ip_selection_callback:
                                        # 调用IP选择回调
                                        try:
                                            selected_ip, selected_index = ip_selection_callback(ip_options)
                                            
                                            if selected_ip and selected_index is not None:
                                                # 发送用户选择到NextTrace
                                                try:
                                                    process.stdin.write(f'{selected_index}\n')
                                                    process.stdin.flush()
                                                    print(f"用户选择IP: {selected_ip} (索引: {selected_index})")
                                                    ip_selection_mode = False
                                                except Exception as e:
                                                    print(f"发送IP选择失败: {e}")
                                                    # 如果无法发送选择，取消进程
                                                    process.terminate()
                                                    raise RuntimeError("无法发送IP选择到NextTrace")
                                            else:
                                                # 用户取消选择
                                                print("用户取消了IP选择")
                                                process.terminate()
                                                raise RuntimeError("用户取消了IP选择")
                                                
                                        except Exception as e:
                                            print(f"IP选择回调出错: {e}")
                                            process.terminate()
                                            raise RuntimeError(f"IP选择失败: {e}")
                                    else:
                                        # 如果没有提供回调，自动选择第一个IPv4地址
                                        auto_selected = None
                                        for ip_option in ip_options:
                                            if ip_option["type"] == "IPv4":
                                                auto_selected = ip_option
                                                break
                                        
                                        if not auto_selected:
                                            auto_selected = ip_options[0]  # 如果没有IPv4，选择第一个
                                        
                                        try:
                                            process.stdin.write(f'{auto_selected["index"]}\n')
                                            process.stdin.flush()
                                            print(f"自动选择IP: {auto_selected['ip']} (索引: {auto_selected['index']})")
                                            ip_selection_mode = False
                                        except Exception as e:
                                            print(f"发送自动IP选择失败: {e}")
                                            process.terminate()
                                            raise RuntimeError("无法发送IP选择到NextTrace")
                                    
                                    continue  # 跳过当前行的其余处理
                                
                            except (ValueError, IndexError) as e:
                                print(f"解析IP选项失败: {e}")
                    
                    # 检查是否收集完所有IP选项
                    # 如果已经收集到IP选项且下一行不是IP选项，或者已经收集了4个选项（通常NextTrace最多显示4个），则认为收集完成
                    elif ip_options and (len(ip_options) >= 4 or not (line[0].isdigit() and ('.' in line or ':' in line))):
                        waiting_for_selection = False
                        
                        if ip_selection_callback:
                            # 调用IP选择回调
                            try:
                                selected_ip, selected_index = ip_selection_callback(ip_options)
                                
                                if selected_ip and selected_index is not None:
                                    # 发送用户选择到NextTrace
                                    try:
                                        process.stdin.write(f'{selected_index}\n')
                                        process.stdin.flush()
                                        print(f"用户选择IP: {selected_ip} (索引: {selected_index})")
                                        ip_selection_mode = False
                                    except Exception as e:
                                        print(f"发送IP选择失败: {e}")
                                        # 如果无法发送选择，取消进程
                                        process.terminate()
                                        raise RuntimeError("无法发送IP选择到NextTrace")
                                else:
                                    # 用户取消选择
                                    print("用户取消了IP选择")
                                    process.terminate()
                                    raise RuntimeError("用户取消了IP选择")
                                    
                            except Exception as e:
                                print(f"IP选择回调出错: {e}")
                                process.terminate()
                                raise RuntimeError(f"IP选择失败: {e}")
                        else:
                            # 如果没有提供回调，自动选择第一个IPv4地址
                            auto_selected = None
                            for ip_option in ip_options:
                                if ip_option["type"] == "IPv4":
                                    auto_selected = ip_option
                                    break
                            
                            if not auto_selected:
                                auto_selected = ip_options[0]  # 如果没有IPv4，选择第一个
                            
                            try:
                                process.stdin.write(f'{auto_selected["index"]}\n')
                                process.stdin.flush()
                                print(f"自动选择IP: {auto_selected['ip']} (索引: {auto_selected['index']})")
                                ip_selection_mode = False
                            except Exception as e:
                                print(f"发送自动IP选择失败: {e}")
                                process.terminate()
                                raise RuntimeError("无法发送IP选择到NextTrace")
                        
                        continue
                
                # 检查IP选择超时
                if ip_selection_mode and waiting_for_selection and ip_selection_start_time:
                    if time.time() - ip_selection_start_time > ip_selection_timeout:
                        print("IP选择超时，强制进行选择...")
                        waiting_for_selection = False
                        
                        if ip_options:
                            if ip_selection_callback:
                                # 超时时调用回调
                                try:
                                    selected_ip, selected_index = ip_selection_callback(ip_options)
                                    
                                    if selected_ip and selected_index is not None:
                                        process.stdin.write(f'{selected_index}\n')
                                        process.stdin.flush()
                                        print(f"超时后用户选择IP: {selected_ip} (索引: {selected_index})")
                                        ip_selection_mode = False
                                    else:
                                        # 超时自动选择第一个IPv4
                                        auto_selected = None
                                        for ip_option in ip_options:
                                            if ip_option["type"] == "IPv4":
                                                auto_selected = ip_option
                                                break
                                        
                                        if not auto_selected:
                                            auto_selected = ip_options[0]
                                        
                                        process.stdin.write(f'{auto_selected["index"]}\n')
                                        process.stdin.flush()
                                        print(f"超时自动选择IP: {auto_selected['ip']} (索引: {auto_selected['index']})")
                                        ip_selection_mode = False
                                except Exception as e:
                                    print(f"超时IP选择回调出错: {e}")
                                    process.terminate()
                                    raise RuntimeError(f"超时IP选择失败: {e}")
                            else:
                                # 超时自动选择第一个IPv4
                                auto_selected = None
                                for ip_option in ip_options:
                                    if ip_option["type"] == "IPv4":
                                        auto_selected = ip_option
                                        break
                                
                                if not auto_selected:
                                    auto_selected = ip_options[0]
                                
                                try:
                                    process.stdin.write(f'{auto_selected["index"]}\n')
                                    process.stdin.flush()
                                    print(f"超时自动选择IP: {auto_selected['ip']} (索引: {auto_selected['index']})")
                                    ip_selection_mode = False
                                except Exception as e:
                                    print(f"超时发送自动IP选择失败: {e}")
                                    process.terminate()
                                    raise RuntimeError("无法发送IP选择到NextTrace")
                        else:
                            print("没有收集到IP选项，终止进程")
                            process.terminate()
                            raise RuntimeError("没有收集到IP选项")
                
                # 如果正在等待IP选择，跳过其他处理
                if waiting_for_selection:
                    continue
                
                # 检查并捕获MapTrace URL
                if line.startswith('MapTrace URL:'):
                    maptrace_url = line.replace('MapTrace URL:', '').strip()
                    print(f"捕获到MapTrace URL: {maptrace_url}")
                    continue
                
                # 跳过无关行
                if (line.startswith('NextTrace') or 'NextTrace API' in line or
                    line.startswith('traceroute to') or
                    line.startswith('Please Choose the IP') or
                    any(x in line for x in ['Sponsored by', 'Copyright', 'Founder', 'Developer', 'Usage:', 'Flags:', 'Examples:', 'Output trace results as', 'Start from the first_ttl hop', 'Disable Print Trace Map', 'Disable MPLS', 'Print version info and exit', 'Use source address', 'Use the following Network Devices', 'Set how many [milliseconds]', 'The number of [milliseconds]', 'Set the payload size', 'Choose the language', 'Read IP Address', 'Disable Colorful Output'])):
                    continue
                
                # 尝试解析路由跳数行
                try:
                    parts = line.split()
                    if not parts:
                        continue
                    
                    # 检查是否是新的路由跳数行（第一个部分是数字）
                    if parts[0].isdigit():
                        # 如果有上一个跳数，先保存并调用回调（如果还未调用过）
                        if current_hop and current_hop["hop"] not in processed_hops:
                            hops.append(current_hop)
                            self._call_callback_for_hop(current_hop, callback)
                            processed_hops.add(current_hop["hop"])
                        
                        # 开始新的跳数
                        hop_num = int(parts[0])
                        
                        # 跳过超时的跳数
                        if len(parts) > 1 and parts[1] == '*':
                            current_hop = {
                                "hop": hop_num,
                                "ip": "*",
                                "delay": [-1],  # 使用-1表示超时
                                "geo": {"country": "超时", "region": "", "city": ""},
                                "asn": {}
                            }
                            # 立即调用回调处理超时
                            hops.append(current_hop)
                            self._call_callback_for_hop(current_hop, callback)
                            processed_hops.add(hop_num)
                            current_hop = None
                            continue
                        
                        # 解析IP地址
                        if len(parts) > 1:
                            ip = parts[1]
                            
                            # 解析地理位置信息
                            geo = {"country": "未知", "region": "未知", "city": "未知"}
                            asn = {}
                            
                            # 查找ASN信息（AS开头）
                            for part in parts[2:]:
                                if part.startswith('AS'):
                                    asn["as"] = part
                                    break
                            
                            # 查找地理位置信息（跳过ASN和IP相关部分）
                            location_parts = []
                            for part in parts[2:]:
                                if part.startswith('AS'):
                                    continue
                                # 跳过主机名和域名（包含点但没有中文字符）
                                if '.' in part and not any(char in part for char in '中文美国新加坡日本韩国香港台湾'):
                                    continue
                                # 跳过技术术语
                                if part in ['-', 'LLC', 'Gbps', 'about.google', 'Equinix', 'Singapore']:
                                    continue
                                location_parts.append(part)
                            
                            # 过滤出地理位置信息
                            geo_location = []
                            for part in location_parts:
                                if any(char in part for char in '中文美国新加坡日本韩国香港台湾') or len(part) <= 10:
                                    geo_location.append(part)
                            
                            if geo_location:
                                if len(geo_location) >= 1:
                                    geo["country"] = geo_location[0]
                                if len(geo_location) >= 2:
                                    geo["region"] = geo_location[1]
                                if len(geo_location) >= 3:
                                    geo["city"] = geo_location[2]
                            
                            current_hop = {
                                "hop": hop_num,
                                "ip": ip,
                                "delay": [0],  # 延迟将在下一行解析
                                "geo": geo,
                                "asn": asn
                            }
                            # 不要立即调用回调，等待延迟信息
                        else:
                            current_hop = None
                    
                    # 如果不是新的跳数行，可能是当前跳数的延迟信息
                    elif current_hop and not parts[0].isdigit():
                        # 检查是否包含延迟信息（延迟信息通常在单独一行）
                        if 'ms' in line:
                            # 解析各种延迟格式
                            delays = []
                            # 使用正则表达式更准确地提取延迟值
                            import re
                            # 匹配延迟模式：数字.数字 ms 或 数字 ms
                            delay_matches = re.findall(r'(\d+\.?\d*)\s*ms', line)
                            
                            for match in delay_matches:
                                try:
                                    delay_value = float(match)
                                    if delay_value > 0:
                                        delays.append(delay_value)
                                except:
                                    pass
                            
                            # 如果正则表达式没有匹配到，尝试原始方法
                            if not delays:
                                parts = line.split()
                                has_timeout = False
                                for part in parts:
                                    if 'ms' in part:
                                        try:
                                            # 处理 "* ms" 格式 - 表示超时
                                            if part.strip() == '*':
                                                has_timeout = True
                                                continue
                                            # 提取数字部分
                                            delay_str = ''.join(c for c in part if c.isdigit() or c == '.')
                                            if delay_str:
                                                delay_value = float(delay_str)
                                                if delay_value > 0:
                                                    delays.append(delay_value)
                                        except:
                                            pass
                                
                                # 如果检测到超时但没有有效延迟，设置为超时
                                if has_timeout and not delays:
                                    current_hop["delay"] = [-1]
                                    # 调用回调以更新超时状态
                                    self._call_callback_for_hop(current_hop, callback)
                                    # 确保标记为已处理
                                    processed_hops.add(current_hop["hop"])
                                    # 将完整的跳数信息添加到结果数组
                                    hops.append(current_hop.copy())
                                    continue
                            
                            # 如果找到有效延迟，使用平均值或第一个值
                            if delays:
                                avg_delay = sum(delays) / len(delays)
                                current_hop["delay"] = [avg_delay]
                                # 调用回调以更新延迟（无论是否已经处理过）
                                self._call_callback_for_hop(current_hop, callback)
                                # 确保标记为已处理
                                processed_hops.add(current_hop["hop"])
                                # 将完整的跳数信息添加到结果数组
                                hops.append(current_hop.copy())
                        
                        # 检查是否包含地理位置信息（用于补充）
                        elif any(word in line for word in ['中国', '美国', '新加坡', '日本', '韩国', '香港', '台湾']):
                            # 更新地理位置信息
                            location_words = []
                            for part in parts:
                                if not part.startswith('AS') and 'ms' not in part and not part.replace('.', '').isdigit():
                                    location_words.append(part)
                            
                            if location_words:
                                if len(location_words) >= 1 and current_hop["geo"]["country"] == "未知":
                                    current_hop["geo"]["country"] = location_words[0]
                                if len(location_words) >= 2 and current_hop["geo"]["region"] == "未知":
                                    current_hop["geo"]["region"] = location_words[1]
                                if len(location_words) >= 3 and current_hop["geo"]["city"] == "未知":
                                    current_hop["geo"]["city"] = location_words[2]
                            
                            # 只有在还未处理过时才调用回调（避免覆盖延迟信息）
                            if current_hop["hop"] not in processed_hops:
                                self._call_callback_for_hop(current_hop, callback)
                                processed_hops.add(current_hop["hop"])
                                # 将完整的跳数信息添加到结果数组
                                hops.append(current_hop.copy())
                
                except Exception as e:
                    print(f"解析NextTrace输出行时出错: {e}")
                    continue
                
            # 等待进程完成
            process.wait(timeout=max_hops * (timeout / 1000) + 30)
            
            # 保存最后一个跳数（如果还未处理过）
            if current_hop and current_hop["hop"] not in processed_hops:
                hops.append(current_hop)
                self._call_callback_for_hop(current_hop, callback)
            
            return {"hops": hops, "raw_output": "", "maptrace_url": maptrace_url}
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError(f"NextTrace执行超时")
        except Exception as e:
            process.kill()
            raise RuntimeError(f"NextTrace执行出错: {e}")
    
    def _call_callback_for_hop(self, hop_data, callback):
        """为单个跳数调用回调函数
        
        :param hop_data: 跳数数据字典
        :param callback: 回调函数
        """
        try:
            hop = hop_data.get("hop", 0)
            ip = hop_data.get("ip", "")
            delay = hop_data.get("delay", [0])[0]
            
            # 构建位置信息
            geo = hop_data.get("geo", {})
            location_parts = []
            if geo.get("country"):
                location_parts.append(geo["country"])
            if geo.get("region") and geo["region"] != geo["country"]:
                location_parts.append(geo["region"])
            if geo.get("city") and geo["city"] not in location_parts:
                location_parts.append(geo["city"])
            
            location = " ".join(location_parts) if location_parts else "未知"
            
            # 获取ISP信息
            asn = hop_data.get("asn", {})
            isp = ""
            if asn.get("as"):
                isp = asn["as"]
            
            # 调用回调函数
            if callback:
                callback(hop, ip, delay, location, isp)
                
        except Exception as e:
            print(f"调用回调函数时出错: {e}")
    
    def _parse_text_output(self, output: str) -> Dict[str, Any]:
        """解析NextTrace的文本输出
        
        :param output: NextTrace的文本输出
        :return: 结构化的路由追踪结果
        """
        result = {
            "hops": [],
            "raw_output": output
        }
        
        lines = output.strip().split('\n')
        current_hop = None
        
        for line in lines:
            # 跳过空行和版本信息行
            line = line.strip()
            if not line or line.startswith('NextTrace') or 'NextTrace API' in line:
                continue
                
            # 跳过MapTrace URL行
            if line.startswith('MapTrace URL:'):
                continue
                
            # 跳过帮助信息和提示行
            if line.startswith('Usage:') or line.startswith('Flags:') or line.startswith('Examples:'):
                continue
                
            # 跳过赞助商信息
            if any(x in line for x in ['Sponsored by', 'Copyright', 'Founder', 'Developer']):
                continue
                
            # 跳过traceroute to行
            if line.startswith('traceroute to'):
                continue
                
            # 尝试解析路由跳数行
            try:
                parts = line.split()
                if not parts:
                    continue
                    
                # 检查是否是新的路由跳数行（第一个部分是数字）
                if parts[0].isdigit():
                    # 如果有上一个跳数，先保存
                    if current_hop:
                        result["hops"].append(current_hop)
                    
                    # 开始新的跳数
                    hop_num = int(parts[0])
                    
                    # 跳过超时的跳数
                    if len(parts) > 1 and parts[1] == '*':
                        current_hop = {
                            "hop": hop_num,
                            "ip": "",
                            "delay": [-1],  # 使用-1表示超时
                            "geo": {"country": "未知", "region": "未知", "city": "未知"},
                            "asn": {}
                        }
                        continue
                    
                    # 解析IP地址
                    if len(parts) > 1:
                        ip = parts[1]
                        
                        # 解析延迟信息（寻找包含ms的部分）
                        delay = [0]
                        for part in parts:
                            if 'ms' in part:
                                try:
                                    # 提取数字部分
                                    delay_str = ''.join(c for c in part if c.isdigit() or c == '.')
                                    if delay_str:
                                        delay_value = float(delay_str)
                                        if delay_value > 0:
                                            delay = [delay_value]
                                            break
                                except:
                                    pass
                        
                        # 如果没有找到延迟，设置默认值为超时
                        if delay[0] == 0:
                            delay = [-1]  # 使用-1表示超时
                        
                        # 解析地理位置信息
                        geo = {"country": "未知", "region": "未知", "city": "未知"}
                        asn = {}
                        
                        # 查找ASN信息（AS开头）
                        for part in parts[2:]:
                            if part.startswith('AS'):
                                asn["as"] = part
                                break
                        
                        # 查找地理位置信息（在IP和延迟之间）
                        location_parts = []
                        delay_start = False
                        for part in parts[2:]:
                            if 'ms' in part:
                                delay_start = True
                                continue
                            if delay_start:
                                continue
                            if part.startswith('AS'):
                                continue
                            location_parts.append(part)
                        
                        if location_parts:
                            # 简单的地理位置解析
                            if len(location_parts) >= 1:
                                geo["country"] = location_parts[0]
                            if len(location_parts) >= 2:
                                geo["region"] = location_parts[1]
                            if len(location_parts) >= 3:
                                geo["city"] = location_parts[2]
                        
                        current_hop = {
                            "hop": hop_num,
                            "ip": ip,
                            "delay": delay,
                            "geo": geo,
                            "asn": asn
                        }
                    else:
                        current_hop = None
                
                # 如果不是新的跳数行，可能是当前跳数的补充信息
                elif current_hop and not parts[0].isdigit():
                    # 检查是否包含延迟信息（延迟信息通常在单独一行）
                    if 'ms' in line and len(parts) == 2:
                        try:
                            # 格式通常是 "延迟值 ms"
                            delay_value = float(parts[0])
                            if delay_value > 0 and current_hop["delay"][0] == 0:
                                current_hop["delay"] = [delay_value]
                        except:
                            pass
                    
                    # 检查是否包含地理位置信息（用于补充）
                    elif any(word in line for word in ['中国', '美国', '新加坡', '日本', '韩国', '香港', '台湾']):
                        # 更新地理位置信息
                        location_words = []
                        for part in parts:
                            if not part.startswith('AS') and 'ms' not in part and not part.replace('.', '').isdigit():
                                location_words.append(part)
                        
                        if location_words:
                            if len(location_words) >= 1 and current_hop["geo"]["country"] == "未知":
                                current_hop["geo"]["country"] = location_words[0]
                            if len(location_words) >= 2 and current_hop["geo"]["region"] == "未知":
                                current_hop["geo"]["region"] = location_words[1]
                            if len(location_words) >= 3 and current_hop["geo"]["city"] == "未知":
                                current_hop["geo"]["city"] = location_words[2]
                
            except Exception as e:
                # 如果解析失败，跳过此行
                continue
        
        # 保存最后一个跳数
        if current_hop:
            result["hops"].append(current_hop)
        
        return result
        
    def _extract_simplified_hops(self, output: str) -> List[Tuple[int, str, float, str, str, Tuple[float, float]]]:
        """简化版的路由跳数提取，用于备用方案
        
        :param output: NextTrace的原始输出
        :return: 简化的路由追踪数据列表
        """
        import re
        hops = []
        
        # 按行解析，寻找路由跳数行
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和无关行
            if not line or line.startswith('NextTrace') or 'NextTrace API' in line:
                continue
            if line.startswith('MapTrace URL:') or line.startswith('traceroute to'):
                continue
            if any(x in line for x in ['Sponsored by', 'Copyright', 'Founder', 'Developer']):
                continue
                
            # 检查是否是路由跳数行（以数字开头）
            parts = line.split()
            if not parts or not parts[0].isdigit():
                continue
                
            # 解析跳数
            try:
                hop_num = int(parts[0])
            except ValueError:
                continue
                
            # 跳过超时的跳数
            if len(parts) > 1 and parts[1] == '*':
                continue
                
            # 解析IP地址
            if len(parts) > 1:
                ip = parts[1]
                
                # 验证IP地址格式
                if not self._is_valid_ip(ip):
                    continue
                
                # 跳过目标IP（通常是最后一跳）
                if ip == '8.8.8.8' or ip == '1.1.1.1':
                    continue
                
                # 解析延迟信息
                delay = 1.0
                for part in parts:
                    if 'ms' in part and '/' not in part:
                        try:
                            delay_str = ''.join(c for c in part if c.isdigit() or c == '.')
                            if delay_str:
                                delay_value = float(delay_str)
                                if delay_value > 0:
                                    delay = delay_value
                                    break
                        except:
                            pass
                
                # 为IP生成伪随机的经纬度（中国范围内）
                import hashlib
                hash_obj = hashlib.md5(ip.encode())
                hash_val = int(hash_obj.hexdigest()[:8], 16)
                
                # 生成中国范围内的经纬度 (经度 73-135, 纬度 18-53)
                lat = 18.0 + (hash_val % 3500) / 100.0
                lon = 73.0 + (hash_val % 6200) / 100.0
                
                # 创建简化的路由数据
                hop_data = (
                    hop_num,      # 跳数
                    ip,           # IP地址
                    delay,        # 延迟
                    "未知",       # 城市
                    "未知ISP",    # ISP
                    (lon, lat)    # 经纬度
                )
                hops.append(hop_data)
        
        return hops
    
    def _is_valid_ip(self, ip: str) -> bool:
        """简单验证IP地址格式是否有效
        
        :param ip: IP地址字符串
        :return: True如果IP格式基本有效，否则False
        """
        # 简化IP验证，只要包含数字和点就认为可能是IP
        # 因为NextTrace输出可能包含特殊格式或内网IP
        if not ip or len(ip) < 4 or len(ip) > 40:
            return False
        
        # 至少包含一个数字和一个点
        if not any(c.isdigit() for c in ip) or '.' not in ip:
            return False
        
        # 排除明显不是IP的字符串
        if any(c in ip for c in ['/', 'http', ':', '@']):
            return False
        
        return True
    
    def convert_nexttrace_result_to_dns_tool_format(self, nexttrace_result: Dict[str, Any]) -> List[Tuple[int, str, float, str, str, Tuple[float, float]]]:
        """
        将NextTrace结果转换为DNS分析工具所需的格式
        
        :param nexttrace_result: 将NextTrace结果转换为RouteTracer Pro所需的格式

    :return: RouteTracer Pro需要的路由追踪结果列表，格式为[(hop, ip, delay, location, isp, (lat, lng)), ...]
        """
        result = []
        
        try:
            # 解析NextTrace的JSON输出
            hops = nexttrace_result.get('hops', [])
            
            for hop_data in hops:
                # 获取跳数
                hop = hop_data.get('hop', 0)
                if hop <= 0:
                    continue
                
                # 获取IP地址
                ip = hop_data.get('ip', '').strip()
                if not ip:
                    # 跳过没有IP的跳数
                    continue
                
                # 获取延迟（取第一个ICMP探测的延迟）
                delays = hop_data.get('delay', [])
                if not delays or delays[0] == 0:
                    # 如果没有延迟数据，使用默认值
                    delay = 0.0
                else:
                    delay = float(delays[0])
                
                # 构建位置信息
                location_parts = []
                
                # 获取地理位置信息
                geo = hop_data.get('geo', {})
                country = geo.get('country', '')
                city = geo.get('city', '')
                
                if country:
                    location_parts.append(country)
                if city and city != country:
                    location_parts.append(city)
                
                # 构建位置字符串
                location = ' '.join(location_parts)
                if not location:
                    location = '未知位置'
                
                # 获取ISP信息
                isp = ''
                asn = hop_data.get('asn', {})
                if asn:
                    isp = asn.get('isp', '')
                    if isp and not location_parts[-1].startswith('('):
                        location_parts.append(f"({isp})")
                        location = ' '.join(location_parts)
                
                # 生成伪随机但固定的经纬度（基于IP地址）
                # 这样相同的IP会映射到相同的地理位置
                lat = 30.0 + (hash(ip) % 20) - 10  # 大致范围在20-40度之间
                lng = 100.0 + (hash(ip) % 60) - 30  # 大致范围在70-130度之间
                
                # 确保经纬度在有效范围内
                lat = max(-90, min(90, lat))
                lng = max(-180, min(180, lng))
                
                # 添加到结果列表，返回格式: (hop, ip, delay, location, isp, (lat, lng))
                result.append((hop, ip, delay, location, isp, (lat, lng)))
                
        except Exception as e:
            print(f"转换NextTrace结果时出错: {e}")
            
        return result
    
    def traceroute_and_convert(self, hostname: str, **kwargs) -> List[Tuple[int, str, float, str]]:
        """执行路由追踪并转换结果格式
        
        :param hostname: 目标主机名或IP地址
        :param kwargs: 其他参数，传递给run_traceroute
        :return: 转换后的路由追踪结果列表
        """
        # 执行路由追踪
        nexttrace_result = self.run_traceroute(hostname, **kwargs)
        
        # 转换结果格式
        return self.convert_nexttrace_result_to_dns_tool_format(nexttrace_result)
    
    def get_nexttrace_version(self) -> str:
        """获取NextTrace版本信息
        
        :return: 版本信息字符串
        :raises RuntimeError: 如果NextTrace不可用或执行失败
        """
        if not self.available:
            raise RuntimeError("NextTrace不可用")
        
        try:
            result = subprocess.run(
                [self.nexttrace_path, '-V'],
                capture_output=True,
                encoding='utf-8',
                check=True,
                **self._get_subprocess_kwargs()
            )
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"获取NextTrace版本失败: {e}")


# 创建全局NextTrace集成实例
nexttrace_integration = NextTraceIntegration()


def run_nexttrace_traceroute(hostname: str, **kwargs) -> List[Tuple[int, str, float, str]]:
    """执行NextTrace路由追踪的便捷函数
    
    :param hostname: 目标主机名或IP地址
    :param kwargs: 其他参数
    :return: 路由追踪结果列表
    """
    return nexttrace_integration.traceroute_and_convert(hostname, **kwargs)


def is_nexttrace_available() -> bool:
    """检查NextTrace是否可用
    
    :return: True如果NextTrace可用，否则False
    """
    return nexttrace_integration.is_available()


def get_nexttrace_info() -> Dict[str, Any]:
    """获取NextTrace信息
    
    :return: 包含NextTrace信息的字典
    """
    info = {
        "available": nexttrace_integration.is_available(),
        "path": nexttrace_integration.nexttrace_path
    }
    
    if info["available"]:
        try:
            info["version"] = nexttrace_integration.get_nexttrace_version()
        except Exception as e:
            info["version_error"] = str(e)
    
    return info


def integrate_with_tracemap(hostname: str, **kwargs) -> Optional[str]:
    """
    集成NextTrace和tracemap，执行路由追踪并生成地图
    
    :param hostname: 目标主机名或IP地址
    :param kwargs: 其他参数
    :return: 生成的HTML文件路径，如果失败则返回None
    """
    try:
        # 设置默认参数，使用毫秒作为超时单位
        kwargs.setdefault('max_hops', 15)
        kwargs.setdefault('timeout', 200)  # 200ms
        kwargs.setdefault('lang', 'cn')  # 确保使用正确的语言参数
        
        # 执行NextTrace路由追踪
        print(f"使用NextTrace执行路由追踪: {hostname}")
        trace_data = run_nexttrace_traceroute(hostname, **kwargs)
        
        # 检查数据有效性，如果数据无效则尝试备用方案
        valid_data = False
        if trace_data:
            # 检查是否有有效的IP地址（不是"when"等无效值）
            for hop in trace_data:
                if len(hop) >= 2 and hop[1] not in ['when', 'unknown', ''] and hop[1].count('.') == 3:
                    valid_data = True
                    break
        
        if not valid_data:
            print("未获取到有效路由数据，尝试备用解析方法")
            
            # 创建集成实例
            integration = NextTraceIntegration()
            if not integration.is_available():
                return None
                
            # 直接执行命令获取原始输出
            cmd = [
                integration.nexttrace_path,
                hostname,
                '-m', str(kwargs.get('max_hops', 15)),
                '--timeout', str(kwargs.get('timeout', 10000)),  # 使用毫秒
                '-C',  # 禁用彩色输出
                '-g', 'cn'  # 使用正确的语言参数
            ]
            
            print(f"执行NextTrace命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding='utf-8',
                timeout=(kwargs.get('max_hops', 15) * kwargs.get('timeout', 10000) / 1000) + 30,  # 转换为秒
                **integration._get_subprocess_kwargs()
            )
            
            # 使用备用方法提取路由数据
            output = result.stdout + result.stderr
            if hasattr(integration, '_extract_simplified_hops'):
                trace_data = integration._extract_simplified_hops(output)
                print(f"备用方法提取到 {len(trace_data)} 个路由节点")
            else:
                print("备用方法不可用")
                return None
        
        if not trace_data:
            print("仍未获取到有效路由数据")
            return None
        
        print(f"获取到 {len(trace_data)} 个路由节点")
        
        # 尝试导入tracemap模块
        from ui.tracemap_integration import generate_and_open_tracemap
        
        # 生成地图并在浏览器中打开
        html_path = generate_and_open_tracemap(trace_data, hostname)
        print(f"使用NextTrace数据生成的地图: {html_path}")
        
        return html_path
        
    except ImportError:
        print("无法导入tracemap模块")
        return None
    except Exception as e:
        print(f"集成NextTrace和tracemap时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


# 测试函数
def test_nexttrace_integration():
    """测试NextTrace集成功能"""
    print("=== NextTrace集成测试 ===")
    
    # 显示NextTrace信息
    info = get_nexttrace_info()
    print(f"NextTrace信息: {info}")
    
    if not info["available"]:
        print("NextTrace不可用，无法进行测试")
        return
    
    # 测试路由追踪
    test_hosts = ['8.8.8.8', '1.1.1.1']
    
    for host in test_hosts:
        try:
            print(f"\n测试路由追踪到: {host}")
            trace_data = run_nexttrace_traceroute(host, max_hops=10)
            
            print(f"获取到 {len(trace_data)} 个路由节点")
            for hop, ip, delay, location in trace_data:
                print(f"{hop:2d}: {ip:15s} | 延迟: {delay:6.2f}ms | {location}")
                
        except Exception as e:
            print(f"路由追踪失败: {e}")
    
    # 测试与tracemap集成
    try:
        print("\n测试与tracemap集成...")
        html_path = integrate_with_tracemap('8.8.8.8', max_hops=10)
        if html_path:
            print(f"集成成功！生成的地图路径: {html_path}")
    except Exception as e:
        print(f"集成测试失败: {e}")
    
    print("\n=== 测试完成 ===")


if __name__ == '__main__':
    test_nexttrace_integration()