import PyInstaller.__main__
import os
import sys


def build_exe():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # PyInstaller 配置 - 使用验证成功的参数
    params = [
        'main.py',
        '--name=RouteTracerPro_v2',
        '--onefile',
        '--windowed',
        f'--icon={os.path.join(current_dir, "favicon_logosc", "favicon.ico")}',
        f'--add-data={os.path.join(current_dir, "ui")};ui',
        f'--add-data={os.path.join(current_dir, "tools")};tools',
        f'--add-data={os.path.join(current_dir, "favicon_logosc")};favicon_logosc',
        '--hidden-import=ui.nexttrace_integration',
        '--hidden-import=ui.tracemap_integration',
        '--clean',
        '--noconfirm'
    ]

    print("开始打包 RouteTracer Pro...")
    print("构建参数:", ' '.join(params))
    PyInstaller.__main__.run(params)
    print("打包完成！")
    print(f"可执行文件位置: {os.path.join(current_dir, 'dist', 'RouteTracerPro_v2.exe')}")


if __name__ == "__main__":
    build_exe()