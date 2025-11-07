#!/usr/bin/env python3
"""
FontConverter 端到端演示

展示完整的字体转换流程：
1. 加载 TrueType 字体
2. 指定字符范围
3. 配置转换参数
4. 生成 LVGL C 代码
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.font_converter import FontConverter, ConversionParams


def progress_callback(message: str, current: int, total: int):
    """进度回调函数"""
    percentage = (current / total * 100) if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r{message}: [{bar}] {percentage:.1f}%", end="", flush=True)
    if current >= total:
        print()  # 换行


def main():
    """主函数"""
    print("=" * 70)
    print("🎨 FontConverter 端到端演示")
    print("=" * 70)
    print()
    
    # 查找系统字体
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",              # macOS
        "C:\\Windows\\Fonts\\arial.ttf",                    # Windows
    ]
    
    font_path = None
    for path in font_paths:
        if Path(path).exists():
            font_path = path
            break
    
    if not font_path:
        print("❌ 未找到系统字体，请手动指定字体路径")
        print("   可用的字体路径示例：")
        for p in font_paths:
            print(f"   - {p}")
        return 1
    
    print(f"✅ 使用字体: {font_path}")
    print()
    
    # 1. 创建转换器
    print("📝 步骤 1: 创建 FontConverter")
    converter = FontConverter()
    converter.set_progress_callback(progress_callback)
    print("   ✓ 转换器已创建")
    print()
    
    # 2. 添加字体和字符范围
    print("📝 步骤 2: 添加字体和字符范围")
    
    # 数字 0-9 (0x30-0x39)
    converter.add_font(font_path, ranges=["0x30-0x39"])
    print("   ✓ 添加数字 0-9")
    
    # 大写字母 A-Z (0x41-0x5A)
    converter.add_font(font_path, ranges=["0x41-0x5A"])
    print("   ✓ 添加大写字母 A-Z")
    
    # 小写字母 a-z (0x61-0x7A)
    converter.add_font(font_path, ranges=["0x61-0x7A"])
    print("   ✓ 添加小写字母 a-z")
    
    # 常用符号
    converter.add_font(font_path, symbols=".,!?:;-+*/=()[]{}@#$%&")
    print("   ✓ 添加常用符号")
    
    total_chars = (10 + 26 + 26 + 24)  # 数字 + 大写 + 小写 + 符号
    print(f"   ℹ️  总共 {total_chars} 个字符")
    print()
    
    # 3. 设置转换参数
    print("📝 步骤 3: 配置转换参数")
    converter.set_params(
        size=24,              # 字体大小 24px
        bpp=4,                # 4-bit 灰度
        compression="rle",    # RLE 压缩
        format="lvgl",        # LVGL C 代码
        lvgl_version=9,       # LVGL 9.x
        no_kerning=True       # 暂时禁用 kerning (简化演示)
    )
    print("   ✓ 字体大小: 24px")
    print("   ✓ 位深度: 4-bit (16 级灰度)")
    print("   ✓ 压缩: RLE")
    print("   ✓ 输出格式: LVGL C 代码")
    print("   ✓ LVGL 版本: 9.x")
    print()
    
    # 4. 执行转换
    print("📝 步骤 4: 执行转换")
    output_path = "output/demo_converted_font_24"
    
    try:
        converter.convert(output_path)
        print()
        print("   ✓ 转换完成!")
        print()
        
        # 5. 检查输出文件
        print("📝 步骤 5: 检查输出文件")
        output_file = Path(output_path).with_suffix('.c')
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"   ✓ 文件已生成: {output_file}")
            print(f"   ✓ 文件大小: {file_size:,} 字节 ({file_size / 1024:.1f} KB)")
            
            # 读取并显示前几行
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"   ✓ 代码行数: {len(lines)}")
            print()
            print("   📄 文件预览 (前 20 行):")
            print("   " + "-" * 66)
            for i, line in enumerate(lines[:20], 1):
                print(f"   {i:3d} | {line.rstrip()}")
            if len(lines) > 20:
                print(f"   ... (省略剩余 {len(lines) - 20} 行)")
            print("   " + "-" * 66)
        else:
            print("   ⚠️  输出文件未找到")
        
    except Exception as e:
        print()
        print(f"   ❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("=" * 70)
    print("✅ 演示完成!")
    print("=" * 70)
    print()
    print("💡 使用提示:")
    print("   1. 生成的 C 文件可直接用于 LVGL 项目")
    print("   2. 在 LVGL 代码中引用:")
    print(f"      LV_FONT_DECLARE(demo_converted_font_24);")
    print(f"      lv_obj_set_style_text_font(label, &demo_converted_font_24, 0);")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
