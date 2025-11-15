import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform


def setup_chinese_font():
    """设置中文字体支持"""
    system = platform.system()

    # 常见的中文字体列表，按优先级排序
    chinese_fonts = []

    if system == 'Windows':
        chinese_fonts = [
            'Microsoft YaHei',  # 微软雅黑
            'SimHei',  # 黑体
            'KaiTi',  # 楷体
            'SimSun',  # 宋体
            'FangSong',  # 仿宋
            'NSimSun',  # 新宋体
        ]
    elif system == 'Darwin':  # macOS
        chinese_fonts = [
            'PingFang SC',  # 苹方
            'Hiragino Sans GB',  # 冬青黑体
            'STHeiti',  # 华文黑体
            'STKaiti',  # 华文楷体
            'STSong',  # 华文宋体
        ]
    else:  # Linux
        chinese_fonts = [
            'WenQuanYi Micro Hei',  # 文泉驿微米黑
            'WenQuanYi Zen Hei',  # 文泉驿正黑
            'Noto Sans CJK SC',  # 思源黑体
            'DejaVu Sans',  # 备用字体
        ]

    # 添加备用英文字体
    chinese_fonts.extend(['DejaVu Sans', 'Arial', 'sans-serif'])

    # 设置字体
    plt.rcParams['font.sans-serif'] = chinese_fonts
    plt.rcParams['axes.unicode_minus'] = False

    # 验证字体是否可用
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = None

    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break

    if selected_font:
        print(f"使用字体: {selected_font}")
        return selected_font
    else:
        print("警告: 未找到合适的中文字体，图表可能显示方块")
        return None


def set_plot_chinese_font(ax, title=None, xlabel=None, ylabel=None):
    """为图表设置中文字体"""
    font_prop = fm.FontProperties()
    system = platform.system()

    if system == 'Windows':
        font_prop.set_family('Microsoft YaHei')
    elif system == 'Darwin':
        font_prop.set_family('PingFang SC')
    else:
        font_prop.set_family('WenQuanYi Micro Hei')

    if title:
        ax.set_title(title, fontproperties=font_prop)
    if xlabel:
        ax.set_xlabel(xlabel, fontproperties=font_prop)
    if ylabel:
        ax.set_ylabel(ylabel, fontproperties=font_prop)

    # 设置刻度标签字体
    for label in ax.get_xticklabels():
        label.set_fontproperties(font_prop)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_prop)