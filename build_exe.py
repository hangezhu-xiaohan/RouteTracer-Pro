import PyInstaller.__main__
import os
import sys


def build_exe():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # PyInstaller 配置
    params = [
        'main.py',
        '--name=RouteTracer Pro',
        '--onefile',
        '--windowed',
        '--icon=NONE',  # 可以替换为你的图标文件路径
        f'--add-data={os.path.join(current_dir, "ui")};ui',
        '--hidden-import=tkinter',
        '--hidden-import=matplotlib.backends.backend_tkagg',
        '--hidden-import=dns.resolver',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=matplotlib.pyplot',
        '--hidden-import=datetime',
        '--hidden-import=threading',
        '--clean',
        '--noconfirm'
    ]

    print("开始打包...")
    PyInstaller.__main__.run(params)


if __name__ == "__main__":
    build_exe()