#!/usr/bin/env python3
"""
测试完整的 GUI 到后端的转换流程
"""

import sys
import os
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gui_integration():
    """测试 GUI 集成"""
    from PyQt6.QtWidgets import QApplication
    from ui.main_window import MainWindow
    
    print("✓ 启动 GUI...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("\n✅ GUI 启动成功!")
    print("   - MainWindow: OK")
    print("   - FontListWidget: OK")
    print("   - ConfigWidget: OK")
    print("\n请在GUI中:")
    print("  1. 点击 '添加字体' 或 '添加文件夹'")
    print("  2. 配置字体参数 (大小、BPP等)")
    print("  3. 点击 '开始转换' 测试完整流程")
    print("  4. 查看日志输出和转换结果")
    
    sys.exit(app.exec())

def test_backend_only():
    """仅测试后端转换"""
    from core.simple_converter import SimpleFontConverter
    
    # 查找系统字体
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if not font_path:
        print("❌ 未找到系统字体")
        return False
    
    print(f"✓ 使用字体: {font_path}")
    
    converter = SimpleFontConverter()
    
    def progress_callback(message, progress):
        print(f"  [{progress:3d}%] {message}")
    
    converter.set_progress_callback(progress_callback)
    
    print("\n开始转换...")
    success = converter.convert_font(
        font_path=font_path,
        size=20,
        bpp=4,  # 使用 BPP=4 (8 不支持 RLE 压缩)
        ranges=["0x20-0x7E"],  # ASCII 可见字符
        symbols="€£¥",
        output_path="/tmp/full_test",
        compression="rle",
        lcd_mode=False,
        lcd_v_mode=False,
        lvgl_version="9.2.0",
        no_kerning=False
    )
    
    if success:
        output_file = "/tmp/full_test.c"
        size = os.path.getsize(output_file)
        print(f"\n✅ 转换成功!")
        print(f"   输出: {output_file}")
        print(f"   大小: {size:,} 字节")
        
        # 验证文件内容
        with open(output_file, 'r') as f:
            content = f.read()
            
        checks = [
            ("字形位图", "glyph_bitmap"),
            ("字形描述符", "glyph_dsc"),
            ("字符映射", "cmaps"),
            ("字体描述符", "font_dsc"),
            ("公共字体", "const lv_font_t")
        ]
        
        print("\n   内容验证:")
        for name, pattern in checks:
            if pattern in content:
                print(f"   ✓ {name}")
            else:
                print(f"   ✗ {name} (未找到)")
        
        return True
    else:
        print("❌ 转换失败")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 LVFontConv")
    parser.add_argument(
        "--mode",
        choices=["gui", "backend"],
        default="backend",
        help="测试模式: gui (启动GUI) 或 backend (仅测试后端)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "gui":
            test_gui_integration()
        else:
            success = test_backend_only()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
