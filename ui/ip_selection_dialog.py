#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP选择对话框组件
用于在NextTrace遇到多个IP时让用户选择要追踪的IP地址
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class IPSelectionDialog:
    """IP选择对话框"""
    
    def __init__(self, parent, title="选择IP地址", message="请选择要追踪的IP地址"):
        self.parent = parent
        self.title = title
        self.message = message
        self.selected_ip = None
        self.selected_index = None
        self.ip_list = []
        self.result = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        
        # 设置模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 创建界面
        self._create_widgets()
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 消息标签
        message_label = ttk.Label(main_frame, text=self.message, font=("Arial", 12, "bold"))
        message_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # IP列表框架
        list_frame = ttk.LabelFrame(main_frame, text="可用的IP地址", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示IP列表
        columns = ("index", "ip", "type", "location")
        self.ip_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        self.ip_tree.heading("index", text="序号")
        self.ip_tree.heading("ip", text="IP地址")
        self.ip_tree.heading("type", text="类型")
        self.ip_tree.heading("location", text="位置")
        
        # 设置列宽
        self.ip_tree.column("index", width=60, minwidth=50)
        self.ip_tree.column("ip", width=150, minwidth=120)
        self.ip_tree.column("type", width=80, minwidth=60)
        self.ip_tree.column("location", width=180, minwidth=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ip_tree.yview)
        self.ip_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.ip_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.ip_tree.bind("<Double-1>", self._on_double_click)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 选择按钮
        self.select_button = ttk.Button(
            button_frame, 
            text="选择", 
            command=self._on_select,
            state=tk.DISABLED
        )
        self.select_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=self._on_cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="请等待IP列表加载...", foreground="gray")
        self.status_label.grid(row=3, column=0, sticky=tk.W)
        
    def add_ip(self, index, ip, ip_type="IPv4", location="未知"):
        """添加IP到列表"""
        self.ip_list.append({
            "index": index,
            "ip": ip,
            "type": ip_type,
            "location": location
        })
        
        # 在GUI线程中更新界面
        self.dialog.after(0, self._update_ip_list)
        
    def _update_ip_list(self):
        """更新IP列表显示"""
        # 清空现有项目
        for item in self.ip_tree.get_children():
            self.ip_tree.delete(item)
            
        # 添加IP列表
        for ip_info in self.ip_list:
            self.ip_tree.insert(
                "", 
                tk.END, 
                values=(
                    ip_info["index"],
                    ip_info["ip"],
                    ip_info["type"],
                    ip_info["location"]
                )
            )
        
        # 更新状态
        if self.ip_list:
            self.status_label.config(text=f"找到 {len(self.ip_list)} 个IP地址，请选择一个")
            self.select_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="未找到IP地址")
            self.select_button.config(state=tk.DISABLED)
            
    def _on_double_click(self, event):
        """双击事件处理"""
        self._on_select()
        
    def _on_select(self):
        """选择按钮事件处理"""
        selection = self.ip_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个IP地址")
            return
            
        # 获取选中的IP信息
        item = self.ip_tree.item(selection[0])
        values = item["values"]
        
        self.selected_index = values[0]
        self.selected_ip = values[1]
        
        # 关闭对话框
        self.dialog.destroy()
        
    def _on_cancel(self):
        """取消按钮事件处理"""
        self.selected_ip = None
        self.selected_index = None
        self.dialog.destroy()
        
    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.selected_ip, self.selected_index
        
    def set_loading_complete(self):
        """设置加载完成"""
        if not self.ip_list:
            self.status_label.config(text="未找到可用的IP地址", foreground="red")
        else:
            self.status_label.config(text=f"找到 {len(self.ip_list)} 个IP地址，请选择一个", foreground="green")


class IPSelectionManager:
    """IP选择管理器"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.current_dialog = None
        self.selection_result = None
        self.selection_event = threading.Event()
        
    def show_ip_selection(self, ip_options, title="选择IP地址", message="请选择要追踪的IP地址"):
        """显示IP选择对话框
        
        :param ip_options: IP选项列表，格式: [{"index": 0, "ip": "1.1.1.1", "type": "IPv4", "location": "美国"}, ...]
        :param title: 对话框标题
        :param message: 对话框消息
        :return: (selected_ip, selected_index) 或 (None, None)
        """
        # 重置事件和结果
        self.selection_event.clear()
        self.selection_result = None
        
        # 在主线程中创建对话框
        def create_dialog():
            self.current_dialog = IPSelectionDialog(self.parent_window, title, message)
            
            # 添加IP选项
            for ip_option in ip_options:
                self.current_dialog.add_ip(
                    ip_option["index"],
                    ip_option["ip"],
                    ip_option.get("type", "IPv4"),
                    ip_option.get("location", "未知")
                )
            
            # 设置加载完成
            self.current_dialog.set_loading_complete()
            
            # 显示对话框并获取结果
            selected_ip, selected_index = self.current_dialog.show()
            
            # 保存结果并设置事件
            self.selection_result = (selected_ip, selected_index)
            self.selection_event.set()
            
        # 在主线程中执行
        self.parent_window.after(0, create_dialog)
        
        # 等待用户选择
        self.selection_event.wait()
        
        return self.selection_result


# 测试函数
def test_ip_selection():
    """测试IP选择对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 创建管理器
    manager = IPSelectionManager(root)
    
    # 模拟IP选项
    ip_options = [
        {"index": 0, "ip": "180.101.49.11", "type": "IPv4", "location": "中国江苏南京"},
        {"index": 1, "ip": "180.101.49.12", "type": "IPv4", "location": "中国江苏南京"},
        {"index": 2, "ip": "2400:da00::2", "type": "IPv6", "location": "中国江苏南京"},
        {"index": 3, "ip": "2400:da00::3", "type": "IPv6", "location": "中国江苏南京"}
    ]
    
    # 显示选择对话框
    selected_ip, selected_index = manager.show_ip_selection(
        ip_options,
        "选择百度IP地址",
        "www.baidu.com解析到多个IP地址，请选择要追踪的IP"
    )
    
    if selected_ip:
        print(f"用户选择了IP: {selected_ip} (索引: {selected_index})")
    else:
        print("用户取消了选择")
    
    root.destroy()


if __name__ == "__main__":
    test_ip_selection()