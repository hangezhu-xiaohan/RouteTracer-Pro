import tkinter as tk
import sys
import os
from ui.main_window import DNSAnalyzerApp


def main():
    try:
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口图标
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "favicon_logosc", "favicon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        
        # 设置应用程序
        app = DNSAnalyzerApp(root)

        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 确保程序完全退出
        try:
            sys.exit(0)
        except:
            os._exit(0)


if __name__ == "__main__":
    main()