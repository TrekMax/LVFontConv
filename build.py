#!/usr/bin/env python3
"""
LVFontConv 打包脚本

使用 PyInstaller 将应用打包为可执行文件。
"""

import PyInstaller.__main__
import sys
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# 应用信息
APP_NAME = "LVFontConv"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = str(SRC_DIR / "main.py")

# PyInstaller 选项
pyinstaller_args = [
    MAIN_SCRIPT,
    f"--name={APP_NAME}",
    f"--distpath={DIST_DIR}",
    f"--workpath={BUILD_DIR}",
    f"--specpath={ROOT_DIR}",
    
    # 单文件模式 (可选,注释掉使用目录模式)
    # "--onefile",
    
    # 窗口模式 (不显示控制台)
    "--windowed",
    
    # 清理构建缓存
    "--clean",
    
    # 日志级别
    "--log-level=INFO",
    
    # 添加数据文件 (如果有的话)
    # f"--add-data={SRC_DIR}/resources:resources",
    
    # 隐藏导入 (PyInstaller 可能检测不到的模块)
    "--hidden-import=numpy",
    "--hidden-import=freetype",
    "--hidden-import=PIL",
    
    # 排除不需要的模块以减小体积
    "--exclude-module=matplotlib",
    "--exclude-module=pandas",
    "--exclude-module=scipy",
    "--exclude-module=IPython",
    "--exclude-module=jupyter",
    
    # 优化选项
    "--strip",  # Linux: 去除符号表
    "--noupx",  # 不使用 UPX 压缩 (可能导致问题)
]

# macOS 特定选项
if sys.platform == "darwin":
    pyinstaller_args.extend([
        # "--icon=resources/icon.icns",
        "--osx-bundle-identifier=com.lvgl.fontconv",
    ])

# Windows 特定选项
elif sys.platform == "win32":
    pyinstaller_args.extend([
        # "--icon=resources/icon.ico",
        "--version-file=version_info.txt",  # 需要创建版本信息文件
    ])

# Linux 特定选项
elif sys.platform == "linux":
    pyinstaller_args.extend([
        # "--icon=resources/icon.png",
    ])

def main():
    """主函数"""
    print(f"=" * 60)
    print(f"开始打包 {APP_NAME} v{APP_VERSION}")
    print(f"平台: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"=" * 60)
    print()
    
    # 确保目录存在
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    
    # 运行 PyInstaller
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print()
        print(f"=" * 60)
        print(f"打包完成!")
        print(f"输出目录: {DIST_DIR}")
        print(f"=" * 60)
        return 0
    except Exception as e:
        print(f"\n错误: 打包失败")
        print(f"原因: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
