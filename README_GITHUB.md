# RouteTracer Pro v2.0 - 专业路由追踪工具

[![Python](https://img.shields.io/badge/Python-3.7%2B-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

一个功能强大、界面美观的专业网络路由追踪分析工具，集成了多种先进的路由追踪技术和可视化功能。

## ✨ 主要特性

- 🔍 **多引擎支持**: 集成 nexttrace、traceroute 等多种追踪引擎
- 🗺️ **地图可视化**: 基于 traceMap 的交互式地图展示路由路径
- 📊 **实时监控**: 实时延迟监控和数据分析图表
- 💾 **多格式导出**: 支持 HTML、JSON、CSV 等格式导出
- 🎨 **现代化界面**: 基于 Tkinter 的美观图形界面

## 🚀 快速开始

### 环境要求
- Windows 10/11
- Python 3.7+

### 安装运行
```bash
git clone https://github.com/hangezhu-xiaohan/RouteTracer-Pro.git
cd RouteTracer-Pro
pip install -r requirements.txt
python main.py
```

## 📖 使用说明

1. 启动程序后，在目标输入框中输入域名或IP地址
2. 选择追踪模式（快速/详细/连续）
3. 点击"开始追踪"按钮
4. 查看实时追踪结果和地图可视化

## 🖼️ 界面展示

- **主界面**: 现代化的GUI界面，操作简单直观
- **地图视图**: 交互式地图显示路由跳转路径
- **数据分析**: 实时监控图表和统计分析

## 🏗️ 技术架构

- **GUI**: Tkinter + 自定义组件
- **路由追踪**: nexttrace + 传统traceroute
- **可视化**: traceMap + SVG图形渲染
- **数据处理**: JSON + 多线程处理

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [nexttrace](https://github.com/xgadget-lab/nexttrace) - 高性能路由追踪工具
- [traceMap](https://github.com/lei-zhiyu/traceMap) - 路由可视化地图框架

## 📞 联系方式

- **作者**: 小韩
- **网站**: [www.xiaohan.ac.cn](http://www.xiaohan.ac.cn)
- **GitHub**: [@hangezhu-xiaohan](https://github.com/hangezhu-xiaohan)

如果这个项目对您有帮助，请给我们一个 ⭐ Star！