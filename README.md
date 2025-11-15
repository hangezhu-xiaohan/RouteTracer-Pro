# RouteTracer Pro v2.0 - 专业路由追踪工具

<div align="center">

![RouteTracer Pro Logo](https://img.shields.io/badge/RouteTracer-Pro%20v2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.7%2B-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)

**一个功能强大、界面美观的专业路由追踪分析工具**

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用说明](#使用说明) • [截图展示](#截图展示) • [技术架构](#技术架构) • [贡献指南](#贡献指南)

</div>

## 📖 项目简介

RouteTracer Pro 是一款专业的网络路由追踪分析工具，集成了多种先进的路由追踪技术和可视化功能。该工具提供了直观的图形界面，支持实时路由监控、地理信息显示、数据分析和导出等功能。

### 🎯 设计目标

- **专业性**: 提供企业级的路由追踪分析能力
- **易用性**: 现代化的GUI界面，操作简单直观
- **可视化**: 集成地图展示，直观呈现路由路径
- **高性能**: 支持多种追踪引擎，快速准确
- **扩展性**: 模块化设计，易于功能扩展

## ✨ 功能特性

### 🔍 核心追踪功能
- **多引擎支持**: 集成 `nexttrace`、`traceroute` 等多种追踪引擎
- **实时监控**: 实时显示路由追踪进度和结果
- **智能分析**: 自动分析路由质量、延迟、丢包率等指标
- **历史记录**: 保存和管理历史追踪数据

### 🗺️ 可视化展示
- **地图集成**: 基于 traceMap 的交互式地图展示
- **路径可视化**: 在地图上直观显示路由跳转路径
- **地理信息**: 显示各跳节点的地理位置信息
- **统计图表**: 实时延迟监控图表和数据分析

### 📊 数据分析
- **延迟分析**: RTT（往返时间）统计和趋势分析
- **节点分析**: 路由节点信息详细展示
- **质量评估**: 网络质量评估和问题诊断
- **报告生成**: 自动生成详细的分析报告

### 💾 数据管理
- **多格式导出**: 支持 HTML、JSON、CSV 等格式导出
- **数据缓存**: 智能缓存地理信息，提高响应速度
- **配置管理**: 灵活的配置选项和用户偏好设置

## 🚀 快速开始

### 环境要求

- **操作系统**: Windows 10/11 (推荐)
- **Python版本**: Python 3.7 或更高版本
- **内存**: 至少 4GB RAM
- **网络**: 需要互联网连接进行地理信息查询

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/hangezhu-xiaohan/RouteTracer-Pro.git
cd RouteTracer-Pro
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python main.py
```

### 依赖包说明

主要依赖包包括：
- `tkinter`: GUI界面框架
- `requests`: HTTP请求处理
- `matplotlib`: 数据可视化
- `threading`: 多线程支持
- `json`: JSON数据处理
- `subprocess`: 外部程序调用

## 📖 使用说明

### 基本操作

1. **启动应用**: 运行 `main.py` 启动程序
2. **输入目标**: 在目标输入框中输入要追踪的域名或IP地址
3. **选择模式**: 选择追踪模式（快速/详细/连续）
4. **开始追踪**: 点击"开始追踪"按钮
5. **查看结果**: 在结果区域查看追踪详情和地图展示

### 高级功能

- **批量追踪**: 支持同时追踪多个目标
- **定时追踪**: 设置定时任务进行周期性追踪
- **结果对比**: 对比不同时间的追踪结果
- **自定义配置**: 调整追踪参数和显示选项

## 🖼️ 截图展示

### 主界面
*（应用主界面展示，包含目标输入、控制面板、结果展示等区域）*

### 地图可视化
*（traceMap集成的交互式地图，显示路由路径和节点信息）*

### 数据分析
*（实时监控图表和统计分析界面）*

## 🏗️ 技术架构

### 项目结构
```
RouteTracer-Pro/
├── main.py                 # 主程序入口
├── ui/                     # 用户界面模块
│   ├── main_window.py      # 主窗口界面
│   ├── network_utils.py    # 网络工具函数
│   ├── nexttrace_integration.py  # nexttrace集成
│   └── tracemap_integration.py   # 地图集成
├── tracemap/              # 地图可视化模块
│   ├── geo_converter.py   # 地理信息转换
│   ├── svg_generator.py   # SVG图形生成
│   └── utils.py           # 工具函数
├── tools/                 # 外部工具
│   └── nexttrace.exe      # nexttrace可执行文件
└── html/                  # 导出文件存储
```

### 核心技术

- **GUI框架**: Tkinter + 自定义组件
- **路由追踪**: nexttrace + 传统traceroute
- **地理信息**: IP地理位置数据库集成
- **可视化**: traceMap + SVG图形渲染
- **数据处理**: JSON + 多线程处理

## 🔧 配置说明

### 追踪参数配置
- **超时设置**: 设置每个跳点的超时时间
- **最大跳数**: 设置追踪的最大跳数限制
- **并发数**: 设置并发追踪的线程数

### 地图配置
- **地图样式**: 选择不同的地图显示样式
- **节点标记**: 自定义节点标记样式
- **路径样式**: 设置路径线条样式和颜色

## 🤝 贡献指南

我们欢迎所有形式的贡献！请阅读以下指南：

### 贡献方式

1. **报告问题**: 在 Issues 中提交bug报告或功能建议
2. **代码贡献**: Fork 项目，创建分支，提交 Pull Request
3. **文档改进**: 改进文档、添加使用示例
4. **测试反馈**: 测试新功能，提供反馈意见

### 开发规范

- 遵循 PEP 8 Python 代码规范
- 添加适当的注释和文档字符串
- 确保代码通过所有测试
- 提交前请运行代码格式化工具

### 提交流程

1. Fork 项目到您的GitHub账户
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和贡献者：

- [nexttrace](https://github.com/xgadget-lab/nexttrace) - 高性能路由追踪工具
- [traceMap](https://github.com/lei-zhiyu/traceMap) - 路由可视化地图框架
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI框架

## 📞 联系方式

- **作者**: 小韩
- **网站**: [www.xiaohan.ac.cn](http://www.xiaohan.ac.cn)
- **GitHub**: [@hangezhu-xiaohan](https://github.com/hangezhu-xiaohan)

## ⭐ 支持项目

如果这个项目对您有帮助，请给我们一个 ⭐ Star！

---

<div align="center">

**[⬆ 回到顶部](#routetracer-pro-v20---专业路由追踪工具)**

Made with ❤️ by 小韩

</div>