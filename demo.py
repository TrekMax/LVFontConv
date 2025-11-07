#!/usr/bin/env python3
"""
LVFontConv - 临时命令行演示工具
演示当前已实现的核心功能
"""

import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.font_loader import FontLoader
from core.glyph_renderer import GlyphRenderer
from core.range_parser import RangeParser, get_preset_ranges
import freetype


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_font_info(font_path):
    """演示字体信息获取"""
    print_header("字体信息")
    
    loader = FontLoader()
    info = loader.load_font(font_path)
    
    print(f"📁 文件: {info.file_path}")
    print(f"👨‍👩‍👧‍👦 字体家族: {info.family_name}")
    print(f"🎨 样式: {info.style_name}")
    print(f"📝 完整名称: {info.full_name}")
    print(f"🔢 字形数量: {info.glyph_count}")
    print(f"✅ 支持字符数: {len(info.supported_chars)}")
    print(f"📏 Units per EM: {info.units_per_em}")
    print(f"⬆️  Ascent: {info.ascent}")
    print(f"⬇️  Descent: {info.descent}")
    print(f"🔤 字距调整: {'是' if info.has_kerning else '否'}")
    print(f"📐 等宽字体: {'是' if info.is_fixed_pitch else '否'}")
    
    # 测试一些字符
    print("\n字符支持测试:")
    test_chars = [
        (0x41, 'A'),
        (0x61, 'a'),
        (0x30, '0'),
        (0x4E2D, '中'),
        (0x6587, '文'),
    ]
    
    for code, char in test_chars:
        exists = loader.char_exists(font_path, code)
        status = "✅" if exists else "❌"
        print(f"  {status} U+{code:04X} ({char}): {exists}")
    
    return loader


def demo_glyph_rendering(font_path):
    """演示字形渲染"""
    print_header("字形渲染")
    
    renderer = GlyphRenderer()
    face = freetype.Face(font_path)
    renderer.set_font_face(font_path, face)
    
    # 测试不同的参数
    test_configs = [
        (16, 4, "小字号, 4-bit"),
        (24, 2, "中字号, 2-bit"),
        (32, 1, "大字号, 1-bit"),
    ]
    
    test_char = 0x41  # 'A'
    
    for size, bpp, desc in test_configs:
        renderer.set_size(size)
        renderer.set_bpp(bpp)
        
        glyph = renderer.render_glyph(font_path, test_char)
        if glyph:
            print(f"\n📐 {desc}:")
            print(f"   尺寸: {glyph.width}x{glyph.height} 像素")
            print(f"   偏移: ({glyph.offset_x}, {glyph.offset_y})")
            print(f"   前进宽度: {glyph.advance_width} 像素")
            if glyph.bitmap.size > 0:
                print(f"   值范围: {glyph.bitmap.min()}-{glyph.bitmap.max()}")
    
    # 测试字距调整
    print("\n字距调整测试:")
    renderer.set_size(24)
    
    kerning_pairs = [
        (0x41, 0x56, "AV"),
        (0x54, 0x6F, "To"),
        (0x57, 0x41, "WA"),
    ]
    
    for left, right, desc in kerning_pairs:
        kern = renderer.get_kerning(font_path, left, right)
        print(f"  {desc}: ({kern[0]}, {kern[1]})")
    
    # 测试文本测量
    print("\n文本测量:")
    test_texts = ["Hello", "World", "LVFontConv"]
    
    for text in test_texts:
        width, height = renderer.measure_text(font_path, text)
        print(f"  '{text}': {width}x{height} 像素")


def demo_range_parser():
    """演示范围解析"""
    print_header("Unicode 范围解析")
    
    parser = RangeParser()
    
    print("\n支持的格式:")
    test_ranges = [
        ("0x41", "单个字符"),
        ("0x41-0x5A", "字符范围"),
        ("0x41=>0x100", "字符映射"),
        ("0x41-0x5A=>0x100", "范围映射"),
        ("0x20-0x7F,0x41", "多个范围"),
    ]
    
    for range_str, desc in test_ranges:
        try:
            ranges = parser.parse_range(range_str)
            char_count = len(parser.get_character_set(ranges))
            print(f"\n  📝 {desc}")
            print(f"     输入: {range_str}")
            print(f"     解析: {ranges}")
            print(f"     字符数: {char_count}")
        except Exception as e:
            print(f"     错误: {e}")
    
    # 符号列表
    print("\n符号列表:")
    symbols = "ABC123"
    ranges = parser.parse_symbols(symbols)
    print(f"  输入: {symbols}")
    print(f"  字符数: {len(ranges)}")
    
    # 预设范围
    print("\n预设范围:")
    presets = get_preset_ranges()
    for name in list(presets.keys())[:5]:  # 只显示前5个
        print(f"  • {name}: {presets[name]}")
    print(f"  ... 共 {len(presets)} 个预设")


def main():
    """主函数"""
    print("\n" + "🎨" * 30)
    print("  LVFontConv - 核心功能演示")
    print("  Version: 0.1.0 (Phase 1 完成)")
    print("🎨" * 30)
    
    # 查找系统字体
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    
    font_path = None
    for path in possible_fonts:
        if Path(path).exists():
            font_path = path
            break
    
    if not font_path:
        print("\n❌ 错误: 未找到系统字体")
        print("请提供字体文件路径:")
        print("  python demo.py <font_file>")
        return 1
    
    # 如果命令行提供了字体路径
    if len(sys.argv) > 1:
        font_path = sys.argv[1]
        if not Path(font_path).exists():
            print(f"\n❌ 错误: 字体文件不存在: {font_path}")
            return 1
    
    print(f"\n🔤 使用字体: {font_path}")
    
    try:
        # 运行各个演示
        demo_font_info(font_path)
        demo_glyph_rendering(font_path)
        demo_range_parser()
        
        print_header("演示完成")
        print("\n✅ 所有核心功能运行正常！")
        print("\n📝 下一步:")
        print("   • Phase 2: LVGL 格式输出实现")
        print("   • Phase 3: GUI 界面开发")
        print("   • Phase 4: 字体预览功能")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
