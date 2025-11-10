#!/usr/bin/env python3
"""
调试位图数据
"""
import sys
import numpy as np

# 添加src到路径
sys.path.insert(0, '/home/listenai/Desktop/EPD/LVGL_Font/LVFontConv/src')

from core.glyph_renderer import GlyphRenderer

# 字体路径
font_path = '../fonts/SourceHanSansCN/SourceHanSansCN-Regular.otf'

# 创建渲染器
renderer = GlyphRenderer()
renderer.set_size(16)
renderer.set_bpp(4)  # 直接使用 4-bit

# 加载字体
from core.font_loader import FontLoader
font_loader = FontLoader()
font_info = font_loader.load_font(font_path)
face = font_loader._freetype_faces[font_path]
renderer.set_font_face(font_path, face)

print(f"字体: {font_info.family_name}, 字形数: {font_info.num_glyphs}")

# 渲染字符 '0' (U+0030)
rendered = renderer.render_glyph(
    font_path=font_path,
    char_code=0x30,
    mapped_code=0x30
)

print(f"渲染结果: {rendered}")

if rendered:
    print(f"字符 U+0030 '0':")
    print(f"尺寸: {rendered.width}x{rendered.height}")
    print(f"offset: ({rendered.offset_x}, {rendered.offset_y})")
    print(f"advance: {rendered.advance_width}")
    print(f"\nbitmap (4-bit):")
    
    # 打印位图 (十六进制)
    for y in range(min(5, rendered.height)):  # 前5行
        row_hex = ' '.join([f'{val:02x}' for val in rendered.bitmap[y, :]])
        print(f"  Row {y}: {row_hex}")
    
    # 第一行前10个像素的打包
    if rendered.height > 0 and rendered.width >= 10:
        first_10 = rendered.bitmap[0, :10]
        print(f"\n前10个像素: {[f'0x{val:x}' for val in first_10]}")
        
        # 手动打包前2个像素
        p0 = first_10[0]
        p1 = first_10[1]
        packed = (p0 << 4) | p1
        print(f"打包: (0x{p0:x} << 4) | 0x{p1:x} = 0x{packed:02x}")
else:
    print("渲染失败!")
