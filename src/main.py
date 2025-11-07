#!/usr/bin/env python3
"""
LVFontConv - Main Entry Point
A PyQt6-based font converter for LVGL with preview capabilities
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from utils.logger import get_logger

logger = get_logger()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("LVFontConv")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("LVGL")
    app.setOrganizationDomain("lvgl.io")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    logger.info("=" * 70)
    logger.info("LVFontConv 启动 v0.1.0")
    logger.info("=" * 70)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
