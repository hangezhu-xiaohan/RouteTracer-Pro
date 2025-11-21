import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import dns.resolver
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import matplotlib.pyplot as plt
from .font_utils import setup_chinese_font, set_plot_chinese_font
from .network_utils import network_utils
import csv
from scapy.layers.inet import traceroute
import os

# 导入traceMap集成模块
try:
    from .tracemap_integration import generate_and_open_tracemap, TRACEMAP_AVAILABLE
except ImportError:
    print("traceMap集成模块导入失败")
    TRACEMAP_AVAILABLE = False

# 导入NextTrace集成模块
try:
    from .nexttrace_integration import NextTraceIntegration, is_nexttrace_available
    NEXTTRACE_AVAILABLE = is_nexttrace_available()
except ImportError as e:
    print(f"NextTrace集成模块导入失败: {e}")
    NEXTTRACE_AVAILABLE = False


matplotlib.use('TkAgg')
import socket



class DNSAnalyzerApp:
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("RouteTracer Pro v2.0 - 专业路由追踪工具 - 作者：小韩-www.xiaohan.ac.cn")
        self.root.geometry("1200x800")

        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 初始化中文字体
        self.setup_chinese_font()

        # 存储测试结果
        self.results = []
        self.is_monitoring = False
        self.monitor_thread = None
        self.comparison_data = []
        self.trace_data = []  # 添加traceroute数据存储

        # 初始化线程控制变量
        self.running_threads = []
        self.is_closing = False

        self.setup_ui()
        self.setup_about_info()

    def setup_ui(self):
        """设置用户界面"""
        # 创建笔记本（选项卡）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 快速测试标签页
        self.setup_quick_test_tab(notebook)

        # 批量测试标签页
        self.setup_batch_test_tab(notebook)

        # 实时监控标签页
        self.setup_monitor_tab(notebook)

        # DNS 比较标签页
        self.setup_dns_compare_tab(notebook)

        # Traceroute 标签页 - 新增
        self.setup_traceroute_tab(notebook)

        # 结果分析标签页
        self.setup_analysis_tab(notebook)

    def setup_traceroute_tab(self, notebook):
        """Traceroute 路由跟踪标签页 - 添加多种方法"""
        trace_frame = ttk.Frame(notebook)
        notebook.add(trace_frame, text="路由跟踪")

        # 输入参数区域
        input_frame = ttk.LabelFrame(trace_frame, text="跟踪参数", padding=10)
        input_frame.pack(fill='x', padx=5, pady=5)

        # 第一行：基本参数
        ttk.Label(input_frame, text="目标域名/IP:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.trace_host_entry = ttk.Entry(input_frame, width=30)
        self.trace_host_entry.insert(0, "www.baidu.com")
        self.trace_host_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="最大跳数:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.max_hops_entry = ttk.Spinbox(input_frame, from_=1, to=64, width=10)
        self.max_hops_entry.set("64")
        self.max_hops_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="超时时间(毫秒):").grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.timeout_entry = ttk.Spinbox(input_frame, from_=100, to=5000, width=10)
        self.timeout_entry.set("300" if NEXTTRACE_AVAILABLE else "1000")  # NextTrace使用300ms超时
        self.timeout_entry.grid(row=0, column=5, padx=5, pady=5)

        # 第二行：方法选择
        method_frame = ttk.Frame(input_frame)
        method_frame.grid(row=1, column=0, columnspan=6, sticky='w', pady=5)

        ttk.Label(method_frame, text="跟踪方法:").pack(side='left', padx=5)

        self.trace_method = tk.StringVar(value="nexttrace" if NEXTTRACE_AVAILABLE else "system")
        methods = [
            ("NextTrace (推荐)", "nexttrace"),
            ("系统命令", "system")
        ]
        
        # 如果NextTrace不可用，从方法列表中移除
        if not NEXTTRACE_AVAILABLE:
            methods = [method for method in methods if method[1] != "nexttrace"]

        for text, value in methods:
            ttk.Radiobutton(method_frame, text=text, variable=self.trace_method,
                            value=value).pack(side='left', padx=5)

        # 按钮区域
        button_frame = ttk.Frame(trace_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        # 跟踪控制按钮
        self.trace_button = ttk.Button(button_frame, text="开始路由跟踪",
                                       command=self.start_traceroute)
        self.trace_button.pack(side='left', padx=5)

        self.cancel_trace_button = ttk.Button(button_frame, text="取消跟踪",
                                              command=self.cancel_traceroute, state='disabled')
        self.cancel_trace_button.pack(side='left', padx=5)

        # 其他功能按钮
        ttk.Button(button_frame, text="Ping测试",
                   command=self.start_ping_test).pack(side='left', padx=5)

        ttk.Button(button_frame, text="清除结果",
                   command=self.clear_traceroute_results).pack(side='left', padx=5)

        ttk.Button(button_frame, text="导出路由图",
                   command=self.export_traceroute).pack(side='left', padx=5)
        
        # 添加生成traceMap按钮 - 使用模拟方式生成地图可视化
        self.generate_map_button = ttk.Button(button_frame, text="生成地图可视化", command=self.generate_tracemap)
        self.generate_map_button.pack(side='left', padx=5)
        self.generate_map_button.config(state='disabled')

        # 进度条
        progress_frame = ttk.Frame(trace_frame)
        progress_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(progress_frame, text="进度:").pack(side='left', padx=5)
        self.trace_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.trace_progress.pack(side='left', fill='x', expand=True, padx=5)

        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side='left', padx=5)

        # 结果显示区域
        result_notebook = ttk.Notebook(trace_frame)
        result_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # 表格结果标签页
        table_frame = ttk.Frame(result_notebook)
        result_notebook.add(table_frame, text="路由详情")

        # 创建树形视图
        columns = ("跳数", "IP地址", "延迟(ms)", "地理位置", "运营商", "状态")
        self.trace_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        column_widths = {
            "跳数": 60,
            "IP地址": 150,
            "延迟(ms)": 80,
            "地理位置": 200,
            "运营商": 150,
            "状态": 80
        }

        for col in columns:
            self.trace_tree.heading(col, text=col)
            self.trace_tree.column(col, width=column_widths.get(col, 100))

        self.trace_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # 添加右键菜单
        self.setup_traceroute_context_menu()

        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.trace_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.trace_tree.configure(yscrollcommand=scrollbar.set)

        # 路由图可视化标签页
        self.trace_chart_frame = ttk.Frame(result_notebook)
        result_notebook.add(self.trace_chart_frame, text="路由图")

        # 初始化路由图
        self.setup_traceroute_chart()

        # 统计信息标签页
        stats_frame = ttk.Frame(result_notebook)
        result_notebook.add(stats_frame, text="统计信息")

        self.stats_text = tk.Text(stats_frame, wrap='word', height=10)
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.stats_text.config(state='disabled')

        scrollbar_stats = ttk.Scrollbar(stats_frame, orient="vertical", command=self.stats_text.yview)
        scrollbar_stats.pack(side='right', fill='y')
        self.stats_text.configure(yscrollcommand=scrollbar_stats.set)

        # 状态显示
        self.trace_status = ttk.Label(trace_frame, text="就绪 - 请输入目标地址并点击开始跟踪")
        self.trace_status.pack(fill='x', padx=5, pady=5)

        # 初始化跟踪控制变量
        self.is_tracing = False
        self.trace_process = None
        self.trace_thread = None

    def setup_traceroute_context_menu(self):
        """设置路由跟踪的右键菜单"""
        self.trace_context_menu = tk.Menu(self.root, tearoff=0)
        self.trace_context_menu.add_command(label="复制IP地址", command=self.copy_trace_ip)
        self.trace_context_menu.add_command(label="复制地理位置", command=self.copy_trace_location)
        self.trace_context_menu.add_command(label="查询详细信息", command=self.show_trace_details)
        self.trace_context_menu.add_separator()
        self.trace_context_menu.add_command(label="Ping此IP", command=self.ping_selected_ip)

        # 绑定右键事件
        self.trace_tree.bind("<Button-3>", self.show_trace_context_menu)

    def show_trace_context_menu(self, event):
        """显示右键菜单"""
        item = self.trace_tree.identify_row(event.y)
        if item:
            self.trace_tree.selection_set(item)
            self.trace_context_menu.post(event.x_root, event.y_root)

    def copy_trace_ip(self):
        """复制选中的IP地址"""
        selection = self.trace_tree.selection()
        if selection:
            item = selection[0]
            ip = self.trace_tree.item(item, 'values')[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(ip)
            self.trace_status.config(text=f"已复制IP地址: {ip}")

    def copy_trace_location(self):
        """复制选中的地理位置"""
        selection = self.trace_tree.selection()
        if selection:
            item = selection[0]
            location = self.trace_tree.item(item, 'values')[3]
            self.root.clipboard_clear()
            self.root.clipboard_append(location)
            self.trace_status.config(text=f"已复制地理位置: {location}")

    def show_trace_details(self):
        """显示选中IP的详细信息"""
        selection = self.trace_tree.selection()
        if selection:
            item = selection[0]
            values = self.trace_tree.item(item, 'values')
            ip = values[1]

            # 获取详细信息
            location_info = network_utils.get_ip_location(ip)

            # 显示详情窗口
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"IP详细信息 - {ip}")
            detail_window.geometry("400x300")

            # 创建详情内容
            detail_text = f"""IP地址: {ip}
    跳数: {values[0]}
    延迟: {values[2]}
    地理位置: {values[3]}
    运营商: {values[4]}

    详细信息:
    国家: {location_info['country']}
    地区: {location_info['region']}
    城市: {location_info['city']}
    ISP: {location_info['isp']}
    时区: {location_info['timezone']}
    国家代码: {location_info['country_code']}"""

            text_widget = tk.Text(detail_window, wrap='word')
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', detail_text)
            text_widget.config(state='disabled')

            ttk.Button(detail_window, text="关闭",
                       command=detail_window.destroy).pack(pady=10)

    def ping_selected_ip(self):
        """Ping选中的IP地址"""
        selection = self.trace_tree.selection()
        if selection:
            item = selection[0]
            ip = self.trace_tree.item(item, 'values')[1]
            self.trace_host_entry.delete(0, 'end')
            self.trace_host_entry.insert(0, ip)
            self.start_ping_test()

    def toggle_fast_mode(self):
        """切换快速模式"""
        if self.fast_mode_var.get():
            self.max_hops_entry.set("15")  # 快速模式使用较少的跳数
            self.timeout_entry.set("1")  # 快速模式使用较短的超时
            self.trace_status.config(text="已切换到快速模式 (跳数: 15, 超时: 1秒)")
        else:
            self.max_hops_entry.set("30")  # 标准模式
            self.timeout_entry.set("2")
            self.trace_status.config(text="已切换到标准模式 (跳数: 30, 超时: 2秒)")

    def cancel_traceroute(self):
        """取消路由跟踪"""
        if self.is_tracing:
            if self.trace_process:
                try:
                    self.trace_process.terminate()
                except:
                    pass

            self.is_tracing = False
            self.trace_button.config(state='normal')
            self.cancel_trace_button.config(state='disabled')
            self.trace_progress.stop()
            self.progress_label.config(text="0%")
            self.trace_status.config(text="路由跟踪已取消")

            # 更新最后一条记录的状态
            if self.trace_tree.get_children():
                last_item = self.trace_tree.get_children()[-1]
                values = list(self.trace_tree.item(last_item, 'values'))
                if len(values) > 5:
                    values[5] = "已取消"
                    self.trace_tree.item(last_item, values=values)

    def setup_chinese_font(self):
        """设置中文字体支持"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            self.chinese_font = True
        except:
            self.chinese_font = False
            print("警告: 中文字体设置失败")

    def setup_about_info(self):
        """设置关于信息"""
        # 在状态栏显示作者信息
        self.status_bar = ttk.Label(self.root, text="作者：小韩 - www.xiaohan.ac.cn", relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

        # 添加关于菜单
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def show_about(self):
        """显示关于对话框"""
        about_text = """DNS 解析分析工具 v2.0

    功能特点：
    • DNS解析时间测试
    • 批量域名测试
    • 实时监控
    • DNS服务器比较
    • 访问时延测试
    • 数据导出功能

    作者：小韩
    网站：www.xiaohan.ac.cn
    邮箱：contact@xiaohan.ac.cn

    版权所有 © 2024"""

        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("400x300")
        about_window.resizable(False, False)

        # 居中显示
        about_window.transient(self.root)
        about_window.grab_set()

        # 作者信息框架
        author_frame = ttk.LabelFrame(about_window, text="作者信息", padding=10)
        author_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(author_frame, text="小韩", font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(author_frame, text="www.xiaohan.ac.cn", font=('Arial', 10)).pack(anchor='w')

        # 功能特点框架
        feature_frame = ttk.LabelFrame(about_window, text="功能特点", padding=10)
        feature_frame.pack(fill='both', expand=True, padx=10, pady=5)

        features = [
            "• DNS解析时间测试",
            "• 批量域名测试",
            "• 实时监控",
            "• DNS服务器比较",
            "• 访问时延测试",
            "• 数据导出功能"
        ]

        for feature in features:
            ttk.Label(feature_frame, text=feature).pack(anchor='w')

        # 版权信息
        copyright_frame = ttk.Frame(about_window)
        copyright_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(copyright_frame, text="版权所有 © 2024 小韩", font=('Arial', 8)).pack(side='bottom')

        # 关闭按钮
        ttk.Button(about_window, text="关闭", command=about_window.destroy).pack(pady=10)

    def on_closing(self):
        """处理窗口关闭事件"""
        if self.is_closing:
            return  # 防止重复调用
        
        self.is_closing = True
        
        try:
            # 停止所有正在进行的操作
            self.stop_all_operations()
            
            # 等待所有线程结束
            self.wait_for_threads_to_finish()
            
            # 销毁窗口
            self.root.destroy()
            
            # 强制退出程序，确保所有进程都结束
            import sys
            import os
            
            # 获取当前进程ID
            current_pid = os.getpid()
            
            # 在Windows上强制终止进程
            if platform.system() == "Windows":
                import subprocess
                try:
                    subprocess.run(['taskkill', '/F', '/PID', str(current_pid)], 
                                 check=False, capture_output=True)
                except:
                    pass
            else:
                # Unix-like系统
                os._exit(0)
            
        except Exception as e:
            print(f"关闭窗口时出错: {e}")
            # 强制退出
            try:
                import sys
                sys.exit(0)
            except:
                import os
                os._exit(0)

    def stop_all_operations(self):
        """停止所有正在进行的操作"""
        try:
            # 停止监控
            if self.is_monitoring and self.monitor_thread:
                self.is_monitoring = False
                if hasattr(self, 'monitor_button'):
                    self.monitor_button.config(text="开始监控", state='normal')
                if hasattr(self, 'monitor_progress'):
                    self.monitor_progress.stop()

            # 停止路由跟踪
            if hasattr(self, 'is_tracing') and self.is_tracing:
                self.is_tracing = False
                if hasattr(self, 'trace_process') and self.trace_process:
                    try:
                        self.trace_process.terminate()
                    except:
                        pass
                if hasattr(self, 'trace_button'):
                    self.trace_button.config(state='normal')
                if hasattr(self, 'cancel_trace_button'):
                    self.cancel_trace_button.config(state='disabled')
                if hasattr(self, 'trace_progress'):
                    self.trace_progress.stop()

            # 停止批量测试
            if hasattr(self, 'is_batch_testing') and self.is_batch_testing:
                self.is_batch_testing = False
                if hasattr(self, 'batch_test_button'):
                    self.batch_test_button.config(text="开始批量测试", state='normal')
                if hasattr(self, 'batch_progress'):
                    self.batch_progress.stop()

        except Exception as e:
            print(f"停止操作时出错: {e}")

    def wait_for_threads_to_finish(self):
        """等待所有线程结束"""
        try:
            # 等待监控线程结束
            if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1.0)  # 减少等待时间

            # 等待路由跟踪线程结束
            if hasattr(self, 'trace_thread') and self.trace_thread and self.trace_thread.is_alive():
                self.trace_thread.join(timeout=1.0)

            # 等待其他线程结束
            for thread in self.running_threads:
                if thread.is_alive():
                    thread.join(timeout=0.5)  # 更短的等待时间

        except Exception as e:
            print(f"等待线程结束时出错: {e}")

    def add_running_thread(self, thread):
        """添加正在运行的线程到列表"""
        if thread not in self.running_threads:
            self.running_threads.append(thread)

    def remove_running_thread(self, thread):
        """从列表中移除已结束的线程"""
        if thread in self.running_threads:
            self.running_threads.remove(thread)


    def setup_traceroute_chart(self):
        """设置路由图"""
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        self.fig_trace, self.ax_trace = plt.subplots(figsize=(10, 6))
        self.ax_trace.set_title('路由跟踪可视化图')
        self.ax_trace.set_xlabel('延迟 (ms)')
        self.ax_trace.set_ylabel('网络跳数')
        self.ax_trace.grid(True, alpha=0.3)

        self.canvas_trace = FigureCanvasTkAgg(self.fig_trace, self.trace_chart_frame)
        self.canvas_trace.get_tk_widget().pack(fill='both', expand=True)

        self.trace_data = []

    def update_traceroute_chart(self, results):
        """更新路由图"""
        if not results:
            return

        self.ax_trace.clear()

        # 提取数据并进行类型转换
        valid_results = []
        for r in results:
            if len(r) >= 4:
                try:
                    hop = int(r[0]) if isinstance(r[0], (str, int, float)) else 0
                    delay = float(r[2]) if isinstance(r[2], (str, int, float)) else 0
                    location = str(r[3]) if len(r) > 3 else ""
                    if hop > 0:  # 只处理有效跳数
                        valid_results.append((hop, delay, location))
                except (ValueError, TypeError):
                    continue
        
        if not valid_results:
            return
        
        hops = [r[0] for r in valid_results]
        delays = [r[1] for r in valid_results]
        locations = [r[2] for r in valid_results]

        if hops and delays:
            # 创建水平条形图
            y_pos = range(len(hops))
            bars = self.ax_trace.barh(y_pos, delays, color='lightblue', alpha=0.7)

            # 设置标题和标签
            self.ax_trace.set_title('路由跟踪可视化图')
            self.ax_trace.set_xlabel('延迟 (ms)')
            self.ax_trace.set_ylabel('网络跳数')

            # 设置Y轴标签为跳数
            self.ax_trace.set_yticks(y_pos)
            self.ax_trace.set_yticklabels([f'跳点 {h}' for h in hops])

            # 在条形图上添加延迟值
            for bar, delay in zip(bars, delays):
                width = bar.get_width()
                self.ax_trace.text(width + 0.1, bar.get_y() + bar.get_height() / 2,
                                   f'{delay:.1f}ms', ha='left', va='center', fontsize=8)

            # 添加地理位置注释（每3个跳点显示一个）
            for i, (y, location) in enumerate(zip(y_pos, locations)):
                if i % 3 == 0:  # 每3个跳点显示一个位置信息
                    self.ax_trace.text(0.1, y, location,
                                       ha='left', va='center', fontsize=7,
                                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

            self.ax_trace.grid(True, alpha=0.3)
            self.fig_trace.tight_layout()
            self.canvas_trace.draw()

    def start_traceroute(self):
        """开始路由跟踪"""
        if self.is_tracing:
            messagebox.showinfo("提示", "路由跟踪正在进行中，请等待完成或取消当前跟踪")
            return

        hostname = self.trace_host_entry.get().strip()
        if not hostname:
            messagebox.showerror("错误", "请输入目标域名或IP地址")
            return

        # 验证输入
        if not self.is_valid_hostname(hostname):
            messagebox.showerror("错误", "请输入有效的域名或IP地址")
            return

        # 如果输入的是域名，先进行DNS解析并让用户选择IP
        if not self._is_ip_address(hostname):
            selected_ip = self._show_ip_selection_dialog(hostname)
            if selected_ip is None:  # 用户取消了选择
                return
            # 将选择的IP显示在输入框中
            self.trace_host_entry.delete(0, 'end')
            self.trace_host_entry.insert(0, selected_ip)
            hostname = selected_ip  # 使用选择的IP进行跟踪

        max_hops = int(self.max_hops_entry.get())
        # 获取超时时间，保持毫秒单位传递给NextTrace
        timeout_ms = int(self.timeout_entry.get())
        # 对于NextTrace，直接使用毫秒值；对于其他方法，转换为秒
        timeout = timeout_ms / 1000.0

        # 更新UI状态
        self.is_tracing = True
        self.trace_button.config(state='disabled')
        self.cancel_trace_button.config(state='normal')
        self.trace_progress.start(10)
        self.progress_label.config(text="0%")

        # 清空之前的结果
        self.trace_tree.delete(*self.trace_tree.get_children())
        self.trace_data = []
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', 'end')
        self.stats_text.config(state='disabled')

        # 更新状态
        self.trace_status.config(text=f"开始路由跟踪到: {hostname} (最大跳数: {max_hops})")

        # 在新线程中执行traceroute
        self.trace_thread = threading.Thread(
            target=self.run_traceroute,
            args=(hostname, max_hops, timeout, timeout_ms)
        )
        self.trace_thread.daemon = True
        self.add_running_thread(self.trace_thread)
        self.trace_thread.start()

    def _is_ip_address(self, hostname):
        """检查输入是否是IP地址"""
        try:
            socket.inet_aton(hostname)
            return True
        except socket.error:
            return False

    def _show_ip_selection_dialog(self, hostname):
        """显示IP选择对话框"""
        try:
            # 执行DNS查询获取所有IP地址
            import dns.resolver
            answers = dns.resolver.resolve(hostname, 'A')
            ip_list = [str(answer) for answer in answers]
            
            # 如果只有一个IP，直接返回
            if len(ip_list) == 1:
                return ip_list[0]
            
            # 创建IP选择对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("选择IP地址")
            dialog.geometry("400x300")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()  # 模态对话框
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            selected_ip = tk.StringVar(value=ip_list[0])
            
            # 标题
            title_label = ttk.Label(dialog, text=f"域名 '{hostname}' 解析到多个IP地址：", 
                                   font=("Arial", 10, "bold"))
            title_label.pack(pady=10)
            
            # IP选择框架
            ip_frame = ttk.Frame(dialog)
            ip_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # 创建单选按钮
            for i, ip in enumerate(ip_list):
                rb = ttk.Radiobutton(ip_frame, text=ip, variable=selected_ip, value=ip)
                rb.pack(anchor="w", pady=2)
            
            # 按钮框架
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            def on_ok():
                dialog.destroy()
            
            def on_cancel():
                selected_ip.set(None)
                dialog.destroy()
            
            ok_button = ttk.Button(button_frame, text="确定", command=on_ok)
            ok_button.pack(side="left", padx=5)
            
            cancel_button = ttk.Button(button_frame, text="取消", command=on_cancel)
            cancel_button.pack(side="left", padx=5)
            
            # 等待对话框关闭
            dialog.wait_window()
            
            return selected_ip.get()
            
        except Exception as e:
            # DNS查询失败，直接使用原始hostname
            messagebox.showwarning("DNS查询失败", f"无法解析域名 '{hostname}': {str(e)}\n将直接使用域名进行跟踪。")
            return hostname

    def is_valid_hostname(self, hostname):
        """验证主机名或IP地址是否有效 - 简化版本"""
        if not hostname or not hostname.strip():
            return False

        hostname = hostname.strip()

        # 检查是否是有效的IP地址
        try:
            socket.inet_aton(hostname)
            return True
        except socket.error:
            pass

        # 简单的主机名格式检查
        if len(hostname) > 253:
            return False

        # 检查是否包含非法字符
        illegal_chars = set(' !@#$%^&*()+=[]{}|;:"<>?')
        if any(char in illegal_chars for char in hostname):
            return False

        # 必须包含点号（对于域名）
        if '.' not in hostname:
            return False

        # 尝试DNS解析作为最终验证
        try:
            socket.getaddrinfo(hostname, None)
            return True
        except:
            # 即使解析失败，也认为是有效的主机名格式
            # 因为可能是网络问题导致的解析失败
            parts = hostname.split('.')
            if len(parts) >= 2 and all(part for part in parts):
                return True
            return False

    def update_trace_result(self, result):
        """实时更新路由跟踪结果到界面"""
        if len(result) == 4:
            hop, ip, delay, location = result
            isp = "未知"
        else:
            hop, ip, delay, location, isp = result
        
        # 确定状态和延迟文本
        if delay == -1:
            status = "超时"
            delay_text = "超时"
        else:
            status = "正常"
            # 以毫秒显示延迟，保留一位小数
            delay_text = f"{delay:.1f} ms"
        
        # 插入到树形视图并保存插入项的ID
        item_id = self.trace_tree.insert("", "end", values=(
            hop,
            ip,
            delay_text,
            location,
            isp,
            status
        ))
        
        # 使用保存的item_id滚动到最新添加的项
        if item_id:
            self.trace_tree.see(item_id)
        
        # 更新进度
        progress = int((hop / int(self.max_hops_entry.get())) * 100)
        self.root.after(0, lambda: self.progress_label.config(text=f"{progress}%"))
    
    def reset_trace_ui(self):
        """重置路由跟踪UI状态"""
        self.is_tracing = False
        self.trace_button.config(state='normal')
        self.cancel_trace_button.config(state='disabled')
        self.trace_progress.stop()
        self.progress_label.config(text="100%")
    
    def _run_nexttrace_with_process(self, process, cmd, callback, max_hops, timeout, ip_selection_callback=None):
        """使用预创建的进程运行NextTrace实时回调模式
        
        :param process: 预创建的子进程
        :param cmd: NextTrace命令列表
        :param callback: 回调函数
        :param max_hops: 最大跳数
        :param timeout: 超时时间
        :param ip_selection_callback: IP选择回调函数
        :return: 最终结果字典，包含MapTrace URL
        """
        import re
        import time
        
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

    def run_traceroute(self, hostname, max_hops, timeout, timeout_ms):
        """执行路由跟踪 - 根据选择的方法调用network_utils中对应的方法"""
        self.root.after(0, lambda: self.trace_status.config(text="路由跟踪进行中..."))

        try:
            # 清空之前的数据
            self.trace_data = []

            def execute_traceroute():
                try:
                    results = []
                    method = self.trace_method.get()

                    self.root.after(0, lambda: self.trace_status.config(text=f"使用 {method.upper()} 方法进行路由跟踪..."))

                    # 根据选择的方法调用对应的traceroute函数
                    if method == "system":
                        # 对于system方法，使用回调函数实时更新结果
                        def trace_callback(result):
                            # 在主线程中更新UI
                            self.root.after(0, self.update_trace_result, result)
                        
                        # 添加进程回调函数来保存进程引用
                        def process_callback(process):
                            # 保存进程引用以便取消功能使用
                            self.trace_process = process
                        
                        results = network_utils.traceroute(
                            hostname, 
                            max_hops=max_hops, 
                            timeout=timeout, 
                            callback=trace_callback,
                            process_callback=process_callback
                        )
                        # 清理进程引用
                        self.trace_process = None
                        # 保存结果但不在此处重置UI，让finalize_traceroute_results统一处理
                    elif method == "nexttrace" and NEXTTRACE_AVAILABLE:
                        # 使用NextTrace进行路由追踪
                        nexttrace = NextTraceIntegration()
                        # 使用实时回调函数更新结果
                        def nexttrace_callback(hop, ip, delay, location, isp):
                            # 在主线程中更新UI
                            result = (hop, ip, delay, location, isp)
                            self.root.after(0, self.update_trace_result, result)
                        # NextTrace需要毫秒单位的超时值
                        # 创建一个包装器来保存进程引用
                        original_run_with_realtime_callback = nexttrace._run_with_realtime_callback
                        def wrapped_run_with_realtime_callback(cmd, callback, max_hops, timeout, ip_selection_callback=None):
                            # 调用原始方法并保存进程引用
                            process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE,
                                encoding='utf-8',
                                errors='replace',
                                universal_newlines=True,
                                bufsize=1,
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                                creationflags=0x08000000 if os.name == 'nt' else 0
                            )
                            # 保存进程引用以便取消功能使用
                            self.trace_process = process
                            
                            # 使用try-except确保进程引用被正确管理
                            try:
                                # 调用原始逻辑，但使用我们创建的进程
                                return self._run_nexttrace_with_process(process, cmd, callback, max_hops, timeout, ip_selection_callback)
                            except Exception as e:
                                # 如果发生错误，清理进程引用
                                self.trace_process = None
                                raise e
                        
                        # 替换方法
                        nexttrace._run_with_realtime_callback = wrapped_run_with_realtime_callback
                        
                        try:
                            nexttrace_result = nexttrace.run_traceroute(hostname, max_hops=max_hops, timeout=timeout_ms, callback=nexttrace_callback)
                            # 提取路由数据和MapTrace URL
                            if isinstance(nexttrace_result, dict) and "hops" in nexttrace_result:
                                results = nexttrace_result["hops"]
                                # 存储MapTrace URL到实例变量
                                self.maptrace_url = nexttrace_result.get("maptrace_url")
                                if self.maptrace_url:
                                    print(f"存储MapTrace URL: {self.maptrace_url}")
                            else:
                                results = nexttrace_result
                        finally:
                            # 清理进程引用
                            self.trace_process = None
                    else:
                        # 默认使用系统命令方法
                        def trace_callback(result):
                            # 在主线程中更新UI
                            self.root.after(0, self.update_trace_result, result)
                        
                        # 添加进程回调函数来保存进程引用
                        def process_callback(process):
                            # 保存进程引用以便取消功能使用
                            self.trace_process = process
                        
                        results = network_utils.traceroute(
                            hostname, 
                            max_hops=max_hops, 
                            timeout=timeout, 
                            callback=trace_callback,
                            process_callback=process_callback
                        )
                        # 清理进程引用
                        self.trace_process = None

                    # 更新UI
                    self.root.after(0, self.finalize_traceroute_results, results, hostname, method)

                except Exception as e:
                    # 清理进程引用
                    self.trace_process = None
                    error_msg = f"{method.upper()} 路由跟踪失败: {str(e)}"
                    # 提供更友好的错误提示和建议
                    if method == "nexttrace":
                        error_msg += "。请确保NextTrace可执行文件已正确安装并在系统PATH中。"
                    self.root.after(0, lambda: self.trace_status.config(text=error_msg))
                finally:
                    # 线程结束时从运行线程列表中移除
                    current_thread = threading.current_thread()
                    self.remove_running_thread(current_thread)

            # 在后台线程中执行
            thread = threading.Thread(target=execute_traceroute)
            thread.daemon = True
            self.add_running_thread(thread)
            thread.start()

        except Exception as e:
            # 清理进程引用
            self.trace_process = None
            self.root.after(0, lambda: self.trace_status.config(text=f"路由跟踪失败: {str(e)}"))

    def finalize_traceroute_results(self, results, hostname, method):
        """完成路由跟踪后的最终处理"""
        # 重置UI状态
        self.is_tracing = False
        self.trace_button.config(state='normal')
        self.cancel_trace_button.config(state='disabled')
        self.trace_progress.stop()
        self.progress_label.config(text="100%")

        # 保存结果数据
        self.trace_data = results
        
        # 对于system和nexttrace模式，结果已经通过回调函数实时添加，不要清空已有的结果
        if method not in ["system", "nexttrace"]:
            self.trace_tree.delete(*self.trace_tree.get_children())

        # 只在非system和非nexttrace模式下添加结果（这些模式下结果已经通过回调实时添加）
        valid_hops = 0
        total_delay = 0
        
        if method not in ["system", "nexttrace"]:
            for result in results:
                if len(result) == 4:
                    hop, ip, delay, location = result
                    isp = "未知"
                else:
                    hop, ip, delay, location, isp = result
                
                # 确保hop是数字类型
                try:
                    hop = int(hop) if isinstance(hop, (str, int, float)) else 0
                except (ValueError, TypeError):
                    hop = 0
                    
                if hop < 0:  # 错误信息
                    # 显示错误信息
                    self.trace_tree.insert("", "end", values=(
                        "错误", ip, "N/A", location, "N/A", "失败"
                    ))
                    continue

                # 确定状态和延迟文本 - 使用-1表示超时
                if delay == -1:
                    status = "超时"
                    delay_text = "超时"
                else:
                    status = "正常"
                    # 以毫秒显示延迟，保留一位小数
                    delay_text = f"{delay:.1f} ms"
                    valid_hops += 1
                    total_delay += delay

                # 插入到树形视图
                self.trace_tree.insert("", "end", values=(
                    hop,
                    ip,
                    delay_text,
                    location,
                    isp,
                    status
                ))
        else:
            # 对于system和nexttrace模式，计算统计信息但不添加结果
            for result in results:
                # 处理NextTrace返回的字典格式数据
                if isinstance(result, dict):
                    hop = result.get('hop', 0)
                    delay = result.get('delay', -1)
                elif len(result) >= 3:
                    try:
                        hop = int(result[0]) if isinstance(result[0], (str, int, float)) else 0
                        delay = result[2]
                    except (ValueError, TypeError, IndexError):
                        continue
                else:
                    continue
                    
                if hop > 0:  # 有效跳数
                    if delay != -1:  # 不是超时
                        # 处理NextTrace返回的延迟列表格式
                        if isinstance(delay, list):
                            # 取列表中的第一个值（平均值）
                            delay_value = delay[0] if delay else -1
                        else:
                            delay_value = delay
                        
                        if delay_value != -1:  # 不是超时
                            valid_hops += 1
                            total_delay += delay_value

        # 更新统计信息
        if valid_hops > 0:
            avg_delay = total_delay / valid_hops
            status_text = f"{method.upper()}跟踪完成: {hostname}, 有效跳数: {valid_hops}, 平均延迟: {avg_delay:.1f} ms"
        else:
            status_text = f"{method.upper()}跟踪完成: 无法到达目标 {hostname}"

        # 启用生成地图按钮（如果traceMap可用且有有效的路由数据）
        if TRACEMAP_AVAILABLE and valid_hops > 0:
            self.generate_map_button.config(state='normal')
            
        self.trace_status.config(text=status_text)

        # 更新图表
        valid_data = []
        for r in results:
            try:
                # 处理NextTrace返回的字典格式数据
                if isinstance(r, dict):
                    hop = r.get('hop', 0)
                    delay = r.get('delay', -1)
                    # 处理延迟列表格式
                    if isinstance(delay, list):
                        delay_value = delay[0] if delay else -1
                    else:
                        delay_value = delay
                    # 转换为列表格式以兼容图表更新函数
                    r_list = [hop, r.get('ip', ''), delay_value, r.get('location', ''), r.get('isp', '')]
                    if hop > 0 and delay_value > 0:
                        valid_data.append(r_list)
                elif len(r) >= 3:
                    hop = int(r[0]) if isinstance(r[0], (str, int, float)) else 0
                    delay = r[2]
                    if hop > 0 and delay > 0:
                        valid_data.append(r)
            except (ValueError, TypeError, IndexError):
                continue
        self.update_traceroute_chart(valid_data)

    def parse_traceroute_line(self, line, system):
        """解析traceroute输出行"""
        try:
            if system == 'windows':
                # Windows tracert 输出格式: 1     1 ms     1 ms     1 ms  192.168.1.1
                if line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    parts = line.split()
                    if len(parts) >= 5:
                        hop = int(parts[0])
                        # 取第一个延迟值
                        delay_str = parts[2]
                        if delay_str.isdigit():
                            delay = int(delay_str)
                        else:
                            delay = 0
                        ip = parts[-1]
                        return hop, ip, delay

            else:
                # Linux/macOS traceroute 输出格式: 1  192.168.1.1 (192.168.1.1)  1.234 ms
                if line.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    parts = line.split()
                    if len(parts) >= 2:
                        hop = int(parts[0])
                        # 提取IP地址
                        ip = parts[1]
                        if ip.startswith('(') and ip.endswith(')'):
                            ip = ip[1:-1]

                        # 提取延迟
                        delay = 0
                        for part in parts:
                            if part.endswith('ms'):
                                try:
                                    delay_str = part.replace('ms', '')
                                    delay = float(delay_str)
                                    break
                                except:
                                    pass

                        return hop, ip, delay

            return None
        except:
            return None

    def update_traceroute_results(self, results, hostname):
        """更新路由跟踪结果"""
        self.trace_tree.delete(*self.trace_tree.get_children())
        self.trace_data = results

        total_hops = 0
        total_delay = 0
        valid_hops = 0

        for result in results:
            # 确保数据格式正确
            if len(result) >= 4:
                try:
                    hop, ip, delay, location = result[:4]
                    # 确保hop是数字类型
                    hop = int(hop) if isinstance(hop, (str, int, float)) else 0
                    # 确保delay是数字类型
                    delay = float(delay) if isinstance(delay, (str, int, float)) else 0
                except (ValueError, TypeError):
                    continue
                    
                if hop > 0:  # 只统计有效跳点
                    total_hops += 1
                    if delay > 0:
                        total_delay += delay
                        valid_hops += 1

                # 从位置信息中提取运营商
                isp = "未知"
                if '(' in location and ')' in location:
                    isp_start = location.find('(') + 1
                    isp_end = location.find(')')
                    if isp_end > isp_start:
                        isp = location[isp_start:isp_end]

                self.trace_tree.insert("", "end", values=(
                    hop if hop > 0 else "超时",
                    ip,
                    f"{delay:.1f}" if delay > 0 else "超时",
                    location,
                    isp
                ))

        # 更新图表
        self.update_traceroute_chart(results)

        # 更新状态
        if total_hops > 0:
            avg_delay = total_delay / valid_hops if valid_hops > 0 else 0
            status_text = (f"跟踪完成: 目标 {hostname}, 总跳数 {total_hops}, "
                           f"平均延迟 {avg_delay:.1f}ms")
        else:
            status_text = f"跟踪完成: 无法到达目标 {hostname}"

        self.root.after(0, lambda: self.trace_status.config(text=status_text))

    def start_ping_test(self):
        """开始Ping测试"""
        hostname = self.trace_host_entry.get().strip()
        if not hostname:
            messagebox.showerror("错误", "请输入目标域名或IP地址")
            return

        thread = threading.Thread(target=self.run_ping_test, args=(hostname,))
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()

    def run_ping_test(self, hostname):
        """执行Ping测试"""
        self.root.after(0, lambda: self.trace_status.config(text="Ping测试进行中..."))

        try:
            result = network_utils.ping_test(hostname, count=4)

            # 显示Ping结果
            ping_window = tk.Toplevel(self.root)
            ping_window.title(f"Ping测试结果 - {hostname}")
            ping_window.geometry("600x400")

            text_widget = tk.Text(ping_window, wrap='word')
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', result)
            text_widget.config(state='disabled')

            scrollbar = ttk.Scrollbar(ping_window, orient="vertical", command=text_widget.yview)
            scrollbar.pack(side='right', fill='y')
            text_widget.configure(yscrollcommand=scrollbar.set)

            ttk.Button(ping_window, text="关闭", command=ping_window.destroy).pack(pady=10)

            self.root.after(0, lambda: self.trace_status.config(text="Ping测试完成"))

        except Exception as e:
            self.root.after(0, lambda: self.trace_status.config(text=f"Ping测试失败: {str(e)}"))
        finally:
            # 移除当前线程
            current_thread = threading.current_thread()
            self.root.after(0, lambda: self.remove_running_thread(current_thread))

    def clear_traceroute_results(self):
        """清除路由跟踪结果"""
        if self.is_tracing:
            messagebox.showinfo("提示", "请先取消正在进行的路由跟踪")
            return

        self.trace_tree.delete(*self.trace_tree.get_children())
        self.trace_data = []

        # 清除图表
        self.ax_trace.clear()
        self.ax_trace.set_title('路由跟踪可视化图')
        self.ax_trace.set_xlabel('延迟 (ms)')
        self.ax_trace.set_ylabel('网络跳数')
        self.ax_trace.grid(True, alpha=0.3)
        self.canvas_trace.draw()

        # 清除统计信息
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', 'end')
        self.stats_text.config(state='disabled')

        # 禁用生成地图按钮
        if TRACEMAP_AVAILABLE:
            self.generate_map_button.config(state='disabled')
            
        self.trace_status.config(text="结果已清除，就绪")

    def export_traceroute(self):
        """导出路由跟踪结果"""
        if not self.trace_data:
            messagebox.showinfo("提示", "没有路由跟踪结果可导出")
            return

        filename = filedialog.asksaveasfilename(
            title="保存路由跟踪结果",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    f.write(f"# 路由跟踪报告\n")
                    f.write(f"# 目标: {self.trace_host_entry.get()}\n")
                    f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# 生成工具: DNS解析分析工具 v2.0\n")
                    f.write(f"# 作者: 小韩 - www.xiaohan.ac.cn\n")
                    f.write(f"# 版权所有 © 2024\n\n")

                    writer = csv.writer(f)
                    writer.writerow(["跳数", "IP地址", "延迟(ms)", "地理位置", "运营商"])

                    for hop, ip, delay, location in self.trace_data:
                        isp = "未知"
                        if '(' in location and ')' in location:
                            isp_start = location.find('(') + 1
                            isp_end = location.find(')')
                            if isp_end > isp_start:
                                isp = location[isp_start:isp_end]

                        writer.writerow([
                            hop if hop > 0 else "超时",
                            ip,
                            f"{delay:.1f}" if delay > 0 else "超时",
                            location,
                            isp
                        ])

                messagebox.showinfo("成功", f"路由跟踪结果已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def generate_tracemap(self):
        """生成traceMap地图可视化"""
        if not self.trace_data:
            messagebox.showinfo("提示", "没有路由跟踪结果可用于生成地图")
            return
        
        hostname = self.trace_host_entry.get().strip()
        
        # 在新线程中生成地图，避免UI卡顿
        thread = threading.Thread(target=self.run_generate_tracemap, args=(hostname,))
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()
        
        # 显示生成中的提示
        self.trace_status.config(text="正在生成地图可视化...")
    
    def run_generate_tracemap(self, hostname):
        """在后台线程中执行地图生成"""
        try:
            # 检查是否有MapTrace URL（NextTrace生成的）
            if hasattr(self, 'maptrace_url') and self.maptrace_url:
                # 如果有MapTrace URL，直接在浏览器中打开
                import webbrowser
                webbrowser.open(self.maptrace_url)
                self.root.after(0, lambda: self.trace_status.config(text=f"已跳转到MapTrace可视化页面"))
                return
            
            # 检查是否是NextTrace生成的数据
            is_nexttrace_data = False
            for hop_data in self.trace_data:
                if len(hop_data) >= 6 and hop_data[5]:  # 如果数据中有经纬度信息
                    is_nexttrace_data = True
                    break
            
            if is_nexttrace_data:
                # 如果是NextTrace数据，直接使用
                html_path = generate_and_open_tracemap(self.trace_data, hostname)
            else:
                # 否则使用模拟方式生成地图
                html_path = generate_and_open_tracemap(self.trace_data, hostname)
            
            self.root.after(0, lambda: self.trace_status.config(text=f"地图可视化已生成: {os.path.basename(html_path)}"))
        except Exception as e:
            error_msg = f"生成地图可视化失败: {str(e)}"
            self.root.after(0, lambda: self.trace_status.config(text=error_msg))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            # 确保按钮状态正确恢复
            if hasattr(self, 'generate_map_button'):
                self.root.after(0, lambda: self.generate_map_button.config(state=tk.NORMAL))
            # 线程结束时从运行线程列表中移除
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def setup_quick_test_tab(self, notebook):
        """快速测试标签页"""
        quick_frame = ttk.Frame(notebook)
        notebook.add(quick_frame, text="快速测试")

        # 输入区域
        input_frame = ttk.LabelFrame(quick_frame, text="测试参数", padding=10)
        input_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(input_frame, text="域名:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.domain_entry = ttk.Entry(input_frame, width=30)
        self.domain_entry.insert(0, "google.com")
        self.domain_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="DNS服务器:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.dns_combo = ttk.Combobox(input_frame, width=25, values=[
            "8.8.8.8", "1.1.1.1", "208.67.222.222",
            "119.29.29.29", "114.114.114.114", "系统默认"
        ])
        self.dns_combo.set("8.8.8.8")
        self.dns_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="记录类型:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.record_combo = ttk.Combobox(input_frame, width=15, values=["A", "AAAA", "MX", "NS", "CNAME"])
        self.record_combo.set("A")
        self.record_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="测试次数:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.iterations_entry = ttk.Spinbox(input_frame, from_=1, to=100, width=10)
        self.iterations_entry.set("3")
        self.iterations_entry.grid(row=1, column=3, padx=5, pady=5)

        # 按钮区域
        button_frame = ttk.Frame(quick_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="开始测试", command=self.start_quick_test).pack(side='left', padx=5)
        ttk.Button(button_frame, text="清除结果", command=self.clear_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出结果", command=self.export_results).pack(side='left', padx=5)

        # 结果显示区域
        result_frame = ttk.LabelFrame(quick_frame, text="测试结果", padding=10)
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 创建树形视图显示结果
        columns = ("序号", "域名", "DNS服务器", "记录类型", "解析结果", "时间(ms)", "状态")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100)

        self.result_tree.pack(fill='both', expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        # 统计信息
        self.stats_label = ttk.Label(quick_frame, text="就绪")
        self.stats_label.pack(fill='x', padx=5, pady=5)

    def setup_batch_test_tab(self, notebook):
        """批量测试标签页"""
        batch_frame = ttk.Frame(notebook)
        notebook.add(batch_frame, text="批量测试")

        # 域名列表区域
        list_frame = ttk.LabelFrame(batch_frame, text="域名列表 (每行一个)", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.domains_text = tk.Text(list_frame, height=10, width=80)
        self.domains_text.pack(fill='both', expand=True, padx=5, pady=5)

        # 预填充一些测试域名
        default_domains = """google.com
github.com
baidu.com
taobao.com
qq.com
weibo.com
zhihu.com
bilibili.com
python.org
stackoverflow.com"""
        self.domains_text.insert('1.0', default_domains)

        # 按钮区域
        batch_button_frame = ttk.Frame(batch_frame)
        batch_button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(batch_button_frame, text="开始批量测试", command=self.start_batch_test).pack(side='left', padx=5)
        ttk.Button(batch_button_frame, text="导入域名列表", command=self.import_domains).pack(side='left', padx=5)
        ttk.Button(batch_button_frame, text="清空列表", command=self.clear_domains).pack(side='left', padx=5)

        # 批量测试结果
        batch_result_frame = ttk.LabelFrame(batch_frame, text="批量测试结果", padding=10)
        batch_result_frame.pack(fill='both', expand=True, padx=5, pady=5)

        batch_columns = ("域名", "DNS服务器", "平均时间(ms)", "最快(ms)", "最慢(ms)", "成功率")
        self.batch_tree = ttk.Treeview(batch_result_frame, columns=batch_columns, show='headings', height=10)

        for col in batch_columns:
            self.batch_tree.heading(col, text=col)
            self.batch_tree.column(col, width=120)

        self.batch_tree.pack(fill='both', expand=True)

    def setup_monitor_tab(self, notebook):
        """实时监控标签页"""
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="实时监控")

        # 监控参数
        monitor_input_frame = ttk.LabelFrame(monitor_frame, text="监控参数", padding=10)
        monitor_input_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(monitor_input_frame, text="监控域名:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.monitor_domain_entry = ttk.Entry(monitor_input_frame, width=25)
        self.monitor_domain_entry.insert(0, "google.com")
        self.monitor_domain_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(monitor_input_frame, text="间隔(秒):").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.interval_entry = ttk.Spinbox(monitor_input_frame, from_=1, to=3600, width=10)
        self.interval_entry.set("10")
        self.interval_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(monitor_input_frame, text="持续时间(分):").grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.duration_entry = ttk.Spinbox(monitor_input_frame, from_=1, to=1440, width=10)
        self.duration_entry.set("5")
        self.duration_entry.grid(row=0, column=5, padx=5, pady=5)

        # 监控按钮
        monitor_button_frame = ttk.Frame(monitor_frame)
        monitor_button_frame.pack(fill='x', padx=5, pady=5)

        self.monitor_button = ttk.Button(monitor_button_frame, text="开始监控", command=self.toggle_monitoring)
        self.monitor_button.pack(side='left', padx=5)

        ttk.Button(monitor_button_frame, text="清除图表", command=self.clear_chart).pack(side='left', padx=5)

        # 图表区域
        self.chart_frame = ttk.LabelFrame(monitor_frame, text="实时监控图表", padding=10)
        self.chart_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 初始化图表
        self.setup_chart()

        # 监控状态
        self.monitor_status = ttk.Label(monitor_frame, text="监控未启动")
        self.monitor_status.pack(fill='x', padx=5, pady=5)

    def setup_dns_compare_tab(self, notebook):
        """DNS 服务器比较标签页"""
        compare_frame = ttk.Frame(notebook)
        notebook.add(compare_frame, text="DNS 比较")

        # 比较参数设置
        compare_input_frame = ttk.LabelFrame(compare_frame, text="比较参数", padding=10)
        compare_input_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(compare_input_frame, text="测试域名:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.compare_domain_entry = ttk.Entry(compare_input_frame, width=30)
        self.compare_domain_entry.insert(0, "google.com")
        self.compare_domain_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(compare_input_frame, text="测试次数:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.compare_iterations = ttk.Spinbox(compare_input_frame, from_=1, to=20, width=10)
        self.compare_iterations.set("5")
        self.compare_iterations.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(compare_input_frame, text="记录类型:").grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.compare_record_type = ttk.Combobox(compare_input_frame, width=10, values=["A", "AAAA"])
        self.compare_record_type.set("A")
        self.compare_record_type.grid(row=0, column=5, padx=5, pady=5)

        # DNS 服务器选择
        dns_select_frame = ttk.LabelFrame(compare_frame, text="选择 DNS 服务器", padding=10)
        dns_select_frame.pack(fill='x', padx=5, pady=5)

        # 创建 DNS 服务器选择框架
        self.dns_vars = {}
        dns_servers = {
            "国内DNS": [
                ("114 DNS (114.114.114.114)", "114.114.114.114"),
                ("阿里 DNS (223.5.5.5)", "223.5.5.5"),
                ("百度 DNS (180.76.76.76)", "180.76.76.76"),
                ("腾讯 DNS (119.29.29.29)", "119.29.29.29"),
                ("CNNIC SDNS (1.2.4.8)", "1.2.4.8")
            ],
            "国际DNS": [
                ("Google DNS (8.8.8.8)", "8.8.8.8"),
                ("Cloudflare (1.1.1.1)", "1.1.1.1"),
                ("OpenDNS (208.67.222.222)", "208.67.222.222"),
                ("Quad9 (9.9.9.9)", "9.9.9.9"),
                ("IBM Quad9 (9.9.9.10)", "9.9.9.10")
            ],
            "运营商DNS": [
                ("中国电信", "219.141.136.10"),
                ("中国移动", "211.136.192.6"),
                ("中国联通", "221.179.38.7")
            ]
        }

        row = 0
        for category, servers in dns_servers.items():
            ttk.Label(dns_select_frame, text=f"{category}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
            col = 1
            for name, ip in servers:
                var = tk.BooleanVar(value=True)
                self.dns_vars[ip] = var
                cb = ttk.Checkbutton(dns_select_frame, text=name, variable=var)
                cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)
                col += 1
                if col > 4:  # 每行最多4个
                    col = 1
                    row += 1
            row += 1

        # 全选/全不选按钮
        select_frame = ttk.Frame(dns_select_frame)
        select_frame.grid(row=row, column=0, columnspan=5, pady=5)
        ttk.Button(select_frame, text="全选", command=self.select_all_dns).pack(side='left', padx=5)
        ttk.Button(select_frame, text="全不选", command=self.deselect_all_dns).pack(side='left', padx=5)

        # 控制按钮
        compare_button_frame = ttk.Frame(compare_frame)
        compare_button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(compare_button_frame, text="开始比较测试",
                   command=self.start_dns_comparison).pack(side='left', padx=5)
        ttk.Button(compare_button_frame, text="测试访问时延",
                   command=self.start_latency_test).pack(side='left', padx=5)
        ttk.Button(compare_button_frame, text="导出比较结果",
                   command=self.export_comparison_results).pack(side='left', padx=5)

        # 结果显示区域
        result_notebook = ttk.Notebook(compare_frame)
        result_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # 表格结果
        table_frame = ttk.Frame(result_notebook)
        result_notebook.add(table_frame, text="表格数据")

        columns = ("排名", "DNS服务器", "提供商", "平均解析(ms)", "最快(ms)", "最慢(ms)",
                   "访问时延(ms)", "成功率", "解析结果")
        self.compare_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        column_widths = {"排名": 60, "DNS服务器": 120, "提供商": 100, "平均解析(ms)": 100,
                         "最快(ms)": 80, "最慢(ms)": 80, "访问时延(ms)": 100, "成功率": 80, "解析结果": 150}

        for col in columns:
            self.compare_tree.heading(col, text=col)
            self.compare_tree.column(col, width=column_widths.get(col, 100))

        self.compare_tree.pack(fill='both', expand=True)

        # 图表结果
        self.chart_frame_compare = ttk.Frame(result_notebook)
        result_notebook.add(self.chart_frame_compare, text="性能图表")

        # 初始化比较图表
        self.setup_comparison_chart()

        # 状态显示
        self.compare_status = ttk.Label(compare_frame, text="就绪")
        self.compare_status.pack(fill='x', padx=5, pady=5)

    def setup_analysis_tab(self, notebook):
        """结果分析标签页"""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="结果分析")

        # 分析按钮
        analysis_button_frame = ttk.Frame(analysis_frame)
        analysis_button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(analysis_button_frame, text="生成统计报告", command=self.generate_report).pack(side='left', padx=5)
        ttk.Button(analysis_button_frame, text="比较DNS服务器", command=self.compare_dns_servers).pack(side='left',
                                                                                                       padx=5)
        ttk.Button(analysis_button_frame, text="清除报告", command=self.clear_report).pack(side='left', padx=5)

        # 报告显示区域
        report_frame = ttk.LabelFrame(analysis_frame, text="分析报告", padding=10)
        report_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.report_text = tk.Text(report_frame, height=20, width=80)
        self.report_text.pack(fill='both', expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.report_text.configure(yscrollcommand=scrollbar.set)

    def setup_chart(self):
        """设置监控图表"""
        self.fig, self.ax = plt.subplots(figsize=(8, 4))

        # 使用字体工具设置中文
        set_plot_chinese_font(self.ax,
                              title='RouteTracer Pro 路由追踪时间实时监控',
                              xlabel='时间',
                              ylabel='解析时间 (ms)')

        self.ax.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.monitor_times = []
        self.monitor_timestamps = []
        self.monitor_results = []  # 用于保存解析的IP结果

    def setup_comparison_chart(self):
        """设置比较图表"""
        self.fig_compare, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 使用字体工具设置中文
        set_plot_chinese_font(self.ax1,
                              title='RouteTracer Pro 路由追踪时间比较',
                              ylabel='解析时间 (ms)')

        set_plot_chinese_font(self.ax2,
                              title='访问时延比较',
                              ylabel='访问时延 (ms)')

        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)

        self.canvas_compare = FigureCanvasTkAgg(self.fig_compare, self.chart_frame_compare)
        self.canvas_compare.get_tk_widget().pack(fill='both', expand=True)

        self.comparison_data = []

    def test_dns_resolution(self, hostname, dns_server, record_type):
        """测试DNS解析"""
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5

        if dns_server != "系统默认":
            resolver.nameservers = [dns_server]

        try:
            start_time = time.time()
            answers = resolver.resolve(hostname, record_type)
            end_time = time.time()

            resolution_time = (end_time - start_time) * 1000
            results = [str(rdata) for rdata in answers]

            return {
                'success': True,
                'time_ms': resolution_time,
                'results': ', '.join(results[:3]),  # 只显示前3个结果
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'time_ms': None,
                'results': '',
                'error': str(e)
            }

    def start_quick_test(self):
        """开始快速测试"""
        domain = self.domain_entry.get().strip()
        dns_server = self.dns_combo.get()
        record_type = self.record_combo.get()

        if not domain:
            messagebox.showerror("错误", "请输入域名")
            return

        # 在新线程中执行测试
        thread = threading.Thread(target=self.run_quick_test, args=(domain, dns_server, record_type))
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()

    def run_quick_test(self, domain, dns_server, record_type):
        """执行快速测试"""
        try:
            iterations = int(self.iterations_entry.get())
            times = []

            for i in range(iterations):
                result = self.test_dns_resolution(domain, dns_server, record_type)

                # 在UI线程中更新结果
                self.root.after(0, self.update_result_tree, i + 1, domain, dns_server, record_type, result)

                if result['success']:
                    times.append(result['time_ms'])

                time.sleep(0.5)  # 短暂延迟

            # 更新统计信息
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                success_rate = len(times) / iterations

                stats_text = f"平均: {avg_time:.2f}ms, 最快: {min_time:.2f}ms, 最慢: {max_time:.2f}ms, 成功率: {success_rate:.1%}"
                self.root.after(0, lambda: self.stats_label.config(text=stats_text))
        except Exception as e:
            error_msg = f"快速测试失败: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            # 线程结束时移除自己
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def update_result_tree(self, index, domain, dns_server, record_type, result):
        """更新结果树形视图"""
        if result['success']:
            status = "成功"
            time_ms = f"{result['time_ms']:.2f}"
            results = result['results']

            # 获取IP位置信息
            ip_locations = []
            for ip in result['results'].split(', '):
                if ip and ip != 'N/A':
                    location_info = network_utils.get_ip_location(ip.strip())
                    location_str = network_utils.format_location_string(location_info)
                    ip_locations.append(f"{ip} [{location_str}]")

            if ip_locations:
                results = ', '.join(ip_locations)
            else:
                results = result['results']

        else:
            status = f"失败: {result['error']}"
            time_ms = "N/A"
            results = "N/A"

        self.result_tree.insert("", "end", values=(
            index, domain, dns_server, record_type, results, time_ms, status
        ))

    def start_batch_test(self):
        """开始批量测试"""
        domains_text = self.domains_text.get('1.0', 'end-1c').strip()
        if not domains_text:
            messagebox.showerror("错误", "请输入要测试的域名列表")
            return

        domains = [domain.strip() for domain in domains_text.split('\n') if domain.strip()]
        dns_server = self.dns_combo.get()

        # 在新线程中执行批量测试
        thread = threading.Thread(target=self.run_batch_test, args=(domains, dns_server))
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()

    def run_batch_test(self, domains, dns_server):
        """执行批量测试"""
        try:
            # 清空之前的结果
            self.root.after(0, lambda: self.batch_tree.delete(*self.batch_tree.get_children()))

            for domain in domains:
                times = []
                successes = 0
                iterations = 3  # 每个域名测试3次

                for i in range(iterations):
                    result = self.test_dns_resolution(domain, dns_server, 'A')
                    if result['success']:
                        times.append(result['time_ms'])
                        successes += 1
                    time.sleep(0.5)

                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    success_rate = successes / iterations
                else:
                    avg_time = min_time = max_time = 0
                    success_rate = 0

                # 更新UI
                self.root.after(0, self.update_batch_tree, domain, dns_server, avg_time, min_time, max_time, success_rate)
        except Exception as e:
            error_msg = f"批量测试失败: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            # 线程结束时移除自己
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def update_batch_tree(self, domain, dns_server, avg_time, min_time, max_time, success_rate):
        """更新批量测试结果树形视图"""
        self.batch_tree.insert("", "end", values=(
            domain, dns_server, f"{avg_time:.2f}", f"{min_time:.2f}", f"{max_time:.2f}", f"{success_rate:.1%}"
        ))

    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """开始监控"""
        domain = self.monitor_domain_entry.get().strip()
        interval = int(self.interval_entry.get())
        duration = int(self.duration_entry.get()) * 60  # 转换为秒

        if not domain:
            messagebox.showerror("错误", "请输入要监控的域名")
            return

        self.is_monitoring = True
        self.monitor_button.config(text="停止监控")
        self.monitor_status.config(text="监控进行中...")

        # 清空监控数据
        self.monitor_times.clear()
        self.monitor_timestamps.clear()
        self.monitor_results.clear()  # 清空解析结果

        # 在新线程中执行监控
        self.monitor_thread = threading.Thread(target=self.run_monitoring, args=(domain, interval, duration))
        self.monitor_thread.daemon = True
        self.add_running_thread(self.monitor_thread)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.monitor_button.config(text="开始监控")
        self.monitor_status.config(text="监控已停止")

    def run_monitoring(self, domain, interval, duration):
        """执行监控"""
        try:
            dns_server = self.dns_combo.get()
            start_time = time.time()
            end_time = start_time + duration

            while self.is_monitoring and time.time() < end_time:
                result = self.test_dns_resolution(domain, dns_server, 'A')

                current_time = time.time()
                if result['success']:
                    self.monitor_times.append(result['time_ms'])
                    self.monitor_timestamps.append(current_time)
                    self.monitor_results.append(result['results'])  # 保存解析结果

                    # 更新图表
                    self.root.after(0, self.update_chart)

                    status_text = f"最后解析: {result['time_ms']:.2f}ms - {time.strftime('%H:%M:%S')}"
                else:
                    status_text = f"解析失败 - {time.strftime('%H:%M:%S')}"

                self.root.after(0, lambda: self.monitor_status.config(text=status_text))

                # 等待间隔时间，但允许及时停止
                for i in range(interval * 10):
                    if not self.is_monitoring:
                        break
                    time.sleep(0.1)

            self.root.after(0, self.stop_monitoring)
        except Exception as e:
            error_msg = f"监控失败: {str(e)}"
            self.root.after(0, lambda: self.monitor_status.config(text=error_msg))
            self.root.after(0, self.stop_monitoring)
        finally:
            # 线程结束时移除自己
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def update_chart(self):
        """更新监控图表"""
        if not self.monitor_times:
            return

        self.ax.clear()

        # 转换为相对时间（分钟）
        if self.monitor_timestamps:
            start_time = self.monitor_timestamps[0]
            relative_times = [(t - start_time) / 60 for t in self.monitor_timestamps]

            # 绘制解析时间曲线
            self.ax.plot(relative_times, self.monitor_times, 'b-', marker='o', markersize=3)

            # 在图表左侧显示所有IP信息，每行一个
            if self.monitor_results:
                # 获取唯一的IP列表（去重）
                unique_ips = []
                seen = set()
                for result in reversed(self.monitor_results):
                    if result and result not in seen:
                        seen.add(result)
                        unique_ips.insert(0, result)
                        # 限制显示的IP数量，避免占用太多空间
                        if len(unique_ips) >= 5:
                            break
                
                # 将IP列表转换为多行文本
                if unique_ips:
                    ip_text = '\n'.join([f'IP: {ip}' for ip in unique_ips])
                    # 在图表左上角显示IP信息
                    self.ax.text(0.02, 0.98, ip_text, 
                                transform=self.ax.transAxes, ha='left', va='top',
                                fontsize=8, bbox=dict(facecolor='white', alpha=0.8))

            # 重新设置标题和标签（确保中文显示）
            set_plot_chinese_font(self.ax,
                                  title='RouteTracer Pro 路由追踪时间实时监控',
                                  xlabel='时间 (分钟)',
                                  ylabel='解析时间 (ms)')

            self.ax.grid(True, alpha=0.3)

            self.canvas.draw()

    def clear_chart(self):
        """清除图表"""
        self.ax.clear()
        self.ax.set_title('RouteTracer Pro 路由追踪时间实时监控')
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('解析时间 (ms)')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # 清空数据
        self.monitor_times.clear()
        self.monitor_timestamps.clear()
        self.monitor_results.clear()

    def select_all_dns(self):
        """全选 DNS 服务器"""
        for var in self.dns_vars.values():
            var.set(True)

    def deselect_all_dns(self):
        """全不选 DNS 服务器"""
        for var in self.dns_vars.values():
            var.set(False)

    def start_dns_comparison(self):
        """开始 DNS 服务器比较"""
        domain = self.compare_domain_entry.get().strip()
        if not domain:
            messagebox.showerror("错误", "请输入测试域名")
            return

        # 获取选中的 DNS 服务器
        selected_dns = [ip for ip, var in self.dns_vars.items() if var.get()]
        if not selected_dns:
            messagebox.showerror("错误", "请至少选择一个 DNS 服务器")
            return

        # 在新线程中执行比较测试
        thread = threading.Thread(
            target=self.run_dns_comparison,
            args=(domain, selected_dns, int(self.compare_iterations.get()))
        )
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()

    def run_dns_comparison(self, domain, dns_servers, iterations):
        """执行 DNS 服务器比较测试"""
        try:
            self.root.after(0, lambda: self.compare_status.config(text="测试进行中..."))
            self.root.after(0, lambda: self.compare_tree.delete(*self.compare_tree.get_children()))

            results = []

            for dns_ip in dns_servers:
                self.root.after(0, lambda ip=dns_ip: self.compare_status.config(text=f"正在测试 {ip}..."))

                # DNS 解析测试
                resolution_times = []
                resolved_ips = set()
                success_count = 0

                for i in range(iterations):
                    result = self.test_dns_resolution(domain, dns_ip, self.compare_record_type.get())
                    if result['success']:
                        resolution_times.append(result['time_ms'])
                        resolved_ips.update(result['results'].split(', '))
                        success_count += 1
                    time.sleep(0.5)  # 避免请求过快

                # 访问时延测试（如果解析成功）
                latency = None
                if resolved_ips:
                    latency = self.test_access_latency(list(resolved_ips)[0])

                # 计算统计信息
                if resolution_times:
                    avg_resolution = sum(resolution_times) / len(resolution_times)
                    min_resolution = min(resolution_times)
                    max_resolution = max(resolution_times)
                    success_rate = success_count / iterations
                else:
                    avg_resolution = min_resolution = max_resolution = 0
                    success_rate = 0

                # 获取 DNS 提供商名称
                provider = self.get_dns_provider_name(dns_ip)

                result_data = {
                    'dns_ip': dns_ip,
                    'provider': provider,
                    'avg_resolution': avg_resolution,
                    'min_resolution': min_resolution,
                    'max_resolution': max_resolution,
                    'latency': latency or 0,
                    'success_rate': success_rate,
                    'resolved_ips': ', '.join(list(resolved_ips)[:2])  # 只显示前2个IP
                }

                results.append(result_data)

            # 按平均解析时间排序
            results.sort(key=lambda x: x['avg_resolution'])

            # 更新UI
            self.root.after(0, self.update_comparison_results, results)
        except Exception as e:
            error_msg = f"DNS比较测试失败: {str(e)}"
            self.root.after(0, lambda: self.compare_status.config(text=error_msg))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            # 线程结束时移除自己
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def test_access_latency(self, ip_address):
        """测试访问时延 (TCP 连接时间)"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip_address, 80))  # 测试 HTTP 端口
            end_time = time.time()
            sock.close()

            return (end_time - start_time) * 1000  # 转换为毫秒
        except:
            return None

    def get_dns_provider_name(self, dns_ip):
        """获取 DNS 提供商名称"""
        provider_map = {
            "114.114.114.114": "114 DNS",
            "223.5.5.5": "阿里云",
            "180.76.76.76": "百度",
            "119.29.29.29": "腾讯",
            "1.2.4.8": "CNNIC",
            "8.8.8.8": "Google",
            "1.1.1.1": "Cloudflare",
            "208.67.222.222": "OpenDNS",
            "9.9.9.9": "Quad9",
            "9.9.9.10": "IBM Quad9",
            "219.141.136.10": "中国电信",
            "211.136.192.6": "中国移动",
            "221.179.38.7": "中国联通"
        }
        return provider_map.get(dns_ip, "未知")

    def update_comparison_results(self, results):
        """更新比较结果"""
        # 清空之前的结果
        self.compare_tree.delete(*self.compare_tree.get_children())
        self.comparison_data = results

        # 更新表格
        for i, result in enumerate(results, 1):
            self.compare_tree.insert("", "end", values=(
                i,
                result['dns_ip'],
                result['provider'],
                f"{result['avg_resolution']:.2f}",
                f"{result['min_resolution']:.2f}",
                f"{result['max_resolution']:.2f}",
                f"{result['latency']:.2f}" if result['latency'] else "超时",
                f"{result['success_rate']:.1%}",
                result['resolved_ips']
            ))

        # 更新图表
        self.update_comparison_chart(results)

        # 更新状态
        best_dns = results[0] if results else None
        if best_dns:
            status_text = f"测试完成！推荐 DNS: {best_dns['provider']} ({best_dns['dns_ip']}) - 平均 {best_dns['avg_resolution']:.2f}ms"
            self.compare_status.config(text=status_text)

    def update_comparison_chart(self, results):
        """更新比较图表"""
        if not results:
            return

        # 清空图表
        self.ax1.clear()
        self.ax2.clear()

        # 准备数据
        providers = [f"{r['provider']}\n({r['dns_ip']})" for r in results]
        resolution_times = [r['avg_resolution'] for r in results]
        latencies = [r['latency'] if r['latency'] else 0 for r in results]

        # 解析时间图表
        bars1 = self.ax1.bar(providers, resolution_times, color='skyblue', alpha=0.7)

        # 设置中文标题和标签
        set_plot_chinese_font(self.ax1,
                              title='RouteTracer Pro 路由追踪时间比较',
                              ylabel='解析时间 (ms)')

        self.ax1.tick_params(axis='x', rotation=45)
        self.ax1.grid(True, alpha=0.3)

        # 在柱状图上显示数值
        for bar, value in zip(bars1, resolution_times):
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                          f'{value:.1f}', ha='center', va='bottom', fontsize=8)

        # 访问时延图表
        bars2 = self.ax2.bar(providers, latencies, color='lightcoral', alpha=0.7)

        # 设置中文标题和标签
        set_plot_chinese_font(self.ax2,
                              title='访问时延比较',
                              ylabel='访问时延 (ms)')

        self.ax2.tick_params(axis='x', rotation=45)
        self.ax2.grid(True, alpha=0.3)

        # 在柱状图上显示数值
        for bar, value in zip(bars2, latencies):
            height = bar.get_height()
            self.ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                          f'{value:.1f}', ha='center', va='bottom', fontsize=8)

        # 调整布局
        self.fig_compare.tight_layout()
        self.canvas_compare.draw()

    def start_latency_test(self):
        """开始访问时延测试"""
        domain = self.compare_domain_entry.get().strip()
        if not domain:
            messagebox.showerror("错误", "请输入测试域名")
            return

        # 使用系统 DNS 解析域名获取 IP
        try:
            ip = socket.gethostbyname(domain)
        except:
            messagebox.showerror("错误", "无法解析域名")
            return

        # 在新线程中执行时延测试
        thread = threading.Thread(target=self.run_latency_test, args=(ip,))
        thread.daemon = True
        self.add_running_thread(thread)
        thread.start()

    def run_latency_test(self, ip):
        """执行访问时延测试"""
        try:
            self.root.after(0, lambda: self.compare_status.config(text="测试访问时延..."))

            latencies = []
            iterations = 10

            for i in range(iterations):
                latency = self.test_access_latency(ip)
                if latency is not None:
                    latencies.append(latency)
                    status = f"测试进度: {i + 1}/{iterations}, 当前时延: {latency:.2f}ms"
                    self.root.after(0, lambda s=status: self.compare_status.config(text=s))
                time.sleep(1)

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)

                result_text = (f"访问时延测试完成: 平均 {avg_latency:.2f}ms, "
                               f"最快 {min_latency:.2f}ms, 最慢 {max_latency:.2f}ms")
                self.root.after(0, lambda: self.compare_status.config(text=result_text))
            else:
                self.root.after(0, lambda: self.compare_status.config(text="访问时延测试失败"))
        finally:
            # 线程结束时从运行线程列表中移除
            current_thread = threading.current_thread()
            self.remove_running_thread(current_thread)

    def export_comparison_results(self):
        """导出比较结果"""
        if not self.comparison_data:
            messagebox.showinfo("提示", "没有比较结果可导出")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存比较结果",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.comparison_data)
                
                if filename.endswith('.xlsx'):
                    # 对于Excel，添加作者信息到单独的工作表
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        # 创建信息工作表
                        info_data = {
                            '项目': ['工具名称', '版本', '作者', '网站', '生成时间', '版权'],
                            '值': [
                                'DNS解析分析工具', 
                                'v2.0', 
                                '小韩', 
                                'www.xiaohan.ac.cn',
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                '版权所有 © 2024'
                            ]
                        }
                        info_df = pd.DataFrame(info_data)
                        info_df.to_excel(writer, sheet_name='工具信息', index=False)
                        
                        # 数据工作表
                        df.to_excel(writer, sheet_name='DNS比较结果', index=False)
                else:
                    # 对于CSV，添加注释头
                    with open(filename, 'w', encoding='utf-8-sig') as f:
                        f.write(f"# DNS服务器比较报告\n")
                        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# 测试域名: {self.compare_domain_entry.get()}\n")
                        f.write(f"# 生成工具: DNS解析分析工具 v2.0\n")
                        f.write(f"# 作者: 小韩 - www.xiaohan.ac.cn\n")
                        f.write(f"# 版权所有 © 2024\n\n")
                    
                    df.to_csv(filename, mode='a', index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("成功", f"结果已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def generate_report(self):
        """生成统计报告"""
        report = "DNS 测试分析报告\n"
        report += "=" * 50 + "\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"生成工具: DNS解析分析工具 v2.0\n"
        report += f"作者: 小韩 - www.xiaohan.ac.cn\n\n"
        
        # 原有的报告内容...
        # 收集所有测试结果
        total_tests = len(self.result_tree.get_children())
        successful_tests = 0
        total_time = 0
        dns_servers_used = set()
        
        for item in self.result_tree.get_children():
            values = self.result_tree.item(item)['values']
            if len(values) >= 7 and values[6] == "成功" and values[5] != "N/A":
                successful_tests += 1
                try:
                    total_time += float(values[5])
                except ValueError:
                    pass
            if len(values) >= 3:
                dns_servers_used.add(values[2])
        
        if total_tests > 0:
            success_rate = successful_tests / total_tests
            avg_time = total_time / successful_tests if successful_tests > 0 else 0
            
            report += f"总测试次数: {total_tests}\n"
            report += f"成功次数: {successful_tests}\n"
            report += f"成功率: {success_rate:.1%}\n"
            report += f"平均解析时间: {avg_time:.2f}ms\n"
            report += f"使用的DNS服务器: {', '.join(dns_servers_used)}\n\n"
        else:
            report += "没有测试数据\n\n"
        
        # 批量测试结果统计
        batch_results = []
        for item in self.batch_tree.get_children():
            values = self.batch_tree.item(item)['values']
            if len(values) >= 6:
                batch_results.append({
                    'domain': values[0],
                    'avg_time': float(values[2].replace('ms', '')),
                    'success_rate': float(values[5].replace('%', '')) / 100
                })
        
        if batch_results:
            report += "批量测试统计:\n"
            report += "-" * 30 + "\n"
            batch_results.sort(key=lambda x: x['avg_time'])
            
            fastest = batch_results[0]
            slowest = batch_results[-1]
            avg_batch_time = sum(r['avg_time'] for r in batch_results) / len(batch_results)
            
            report += f"最快解析: {fastest['domain']} - {fastest['avg_time']:.2f}ms\n"
            report += f"最慢解析: {slowest['domain']} - {slowest['avg_time']:.2f}ms\n"
            report += f"平均解析时间: {avg_batch_time:.2f}ms\n\n"
        
        # DNS比较结果
        if self.comparison_data:
            report += "DNS服务器推荐:\n"
            report += "-" * 30 + "\n"
            for i, dns in enumerate(self.comparison_data[:3], 1):  # 前3名
                report += (f"{i}. {dns['provider']} ({dns['dns_ip']}): "
                          f"{dns['avg_resolution']:.2f}ms, 成功率: {dns['success_rate']:.1%}\n")
        
        self.report_text.delete('1.0', 'end')
        self.report_text.insert('1.0', report)

    def compare_dns_servers(self):
        """比较DNS服务器性能"""
        # 收集所有测试结果
        all_dns_servers = set()
        dns_performance = {}

        for item in self.result_tree.get_children():
            values = self.result_tree.item(item)['values']
            if len(values) >= 7:
                dns_server = values[2]  # DNS服务器列
                time_str = values[5]  # 时间列
                status = values[6]  # 状态列

                if dns_server != "系统默认" and status == "成功" and time_str != "N/A":
                    try:
                        time_ms = float(time_str)
                        all_dns_servers.add(dns_server)

                        if dns_server not in dns_performance:
                            dns_performance[dns_server] = []
                        dns_performance[dns_server].append(time_ms)
                    except ValueError:
                        continue

        # 生成分析报告
        report = "DNS 服务器性能分析报告\n"
        report += "=" * 50 + "\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if dns_performance:
            # 计算每个DNS服务器的统计信息
            performance_stats = []
            for dns_server, times in dns_performance.items():
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)

                # 计算成功率
                total_attempts = len([item for item in self.result_tree.get_children()
                                      if self.result_tree.item(item)['values'][2] == dns_server])
                success_rate = len(times) / total_attempts if total_attempts > 0 else 0

                performance_stats.append({
                    'dns_server': dns_server,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'success_rate': success_rate,
                    'test_count': len(times)
                })

            # 按平均时间排序
            performance_stats.sort(key=lambda x: x['avg_time'])

            report += "性能排名:\n"
            report += "-" * 30 + "\n"
            for i, stats in enumerate(performance_stats, 1):
                report += (f"{i}. {stats['dns_server']}: {stats['avg_time']:.2f}ms "
                           f"(最快{stats['min_time']:.2f}ms, 最慢{stats['max_time']:.2f}ms, "
                           f"成功率{stats['success_rate']:.1%})\n")

            # 最佳推荐
            best = performance_stats[0]
            report += f"\n推荐使用: {best['dns_server']} (平均 {best['avg_time']:.2f}ms)\n"
        else:
            report += "没有足够的测试数据进行DNS服务器比较\n"

        self.report_text.delete('1.0', 'end')
        self.report_text.insert('1.0', report)

    def clear_report(self):
        """清除报告"""
        self.report_text.delete('1.0', 'end')

    def clear_results(self):
        """清除结果"""
        self.result_tree.delete(*self.result_tree.get_children())
        self.stats_label.config(text="就绪")

    def clear_domains(self):
        """清空域名列表"""
        self.domains_text.delete('1.0', 'end')

    def import_domains(self):
        """导入域名列表"""
        filename = filedialog.askopenfilename(
            title="选择域名列表文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    domains = f.read()
                self.domains_text.delete('1.0', 'end')
                self.domains_text.insert('1.0', domains)
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {e}")

    def export_results(self):
        """导出结果"""
        filename = filedialog.asksaveasfilename(
            title="保存测试结果",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                # 收集所有结果
                all_results = []
                for item in self.result_tree.get_children():
                    values = self.result_tree.item(item)['values']
                    all_results.append(values)

                if all_results:
                    df = pd.DataFrame(all_results,
                                      columns=["序号", "域名", "DNS服务器", "记录类型", "解析结果", "时间(ms)", "状态"])

                    # 添加作者信息作为注释
                    with open(filename, 'w', encoding='utf-8-sig') as f:
                        f.write(f"# DNS测试报告 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"# 生成工具: DNS解析分析工具 v2.0\n")
                        f.write(f"# 作者: 小韩 - www.xiaohan.ac.cn\n")
                        f.write(f"# 版权所有 © 2024\n")

                    # 追加数据
                    df.to_csv(filename, mode='a', index=False, encoding='utf-8-sig')
                    messagebox.showinfo("成功", f"结果已导出到: {filename}")
                else:
                    messagebox.showinfo("提示", "没有结果可导出")

            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
