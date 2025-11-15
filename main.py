import tkinter as tk
from ui.main_window import DNSAnalyzerApp


def main():
    # 创建主窗口
    root = tk.Tk()

    # 设置应用程序
    app = DNSAnalyzerApp(root)

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()