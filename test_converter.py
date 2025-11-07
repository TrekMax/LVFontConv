#!/usr/bin/env python3
"""
测试 SimpleFontConverter 的端到端转换功能
"""

import sys
import os
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.simple_converter import SimpleFontConverter

def test_conversion():
    """测试基本的字体转换"""
    
    # 查找系统字体
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if not font_path:
        print("❌ 未找到系统字体,请指定字体路径")
        return False
    
    print(f"✓ 使用字体: {font_path}")
    
    # 创建转换器
    converter = SimpleFontConverter()
    
    # 设置进度回调
    def progress_callback(message, progress):
        print(f"  [{progress:3d}%] {message}")
    
    converter.set_progress_callback(progress_callback)
    
    # 执行转换
    print("\n开始转换...")
    success = converter.convert_font(
        font_path=font_path,
        size=16,
        bpp=4,
        ranges=["0x30-0x39", "0x41-0x5A"],  # 数字和大写字母
        symbols="!@#",
        output_path="/tmp/test_font",
        compression="none",
        lcd_mode=False,
        lcd_v_mode=False,
        lvgl_version="9.2.0"
    )
    
    if success:
        output_file = "/tmp/test_font.c"
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"\n✅ 转换成功!")
            print(f"   输出文件: {output_file}")
            print(f"   文件大小: {size} 字节")
            
            # 显示文件前几行
            with open(output_file, 'r') as f:
                lines = f.readlines()[:20]
                print("\n   文件内容预览:")
                for line in lines:
                    print(f"   {line.rstrip()}")
            
            return True
        else:
            print(f"❌ 输出文件不存在: {output_file}")
            return False
    else:
        print("❌ 转换失败")
        return False

if __name__ == "__main__":
    try:
        success = test_conversion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
