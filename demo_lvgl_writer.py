#!/usr/bin/env python3
"""
LVFontConv Phase 2 综合演示

演示从字体加载到 LVGL C 代码生成的完整流程。
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from pathlib import Path

from core.font_loader import FontLoader
from core.glyph_renderer import GlyphRenderer
from writers.lvgl.structures import (
    LVGLFont,
    LVGLHead,
    LVGLCmap,
    LVGLGlyf,
    LVGLKern,
    CmapSubtable,
    GlyphData,
    CompressionType,
    SubpixelMode,
    CmapFormat
)
from writers.lvgl.writer import LVGLWriter


def demo_lvgl_writer():
    """演示 LVGL Writer 功能"""
    print("=" * 70)
    print("🎨 LVFontConv - LVGL Writer 演示")
    print("=" * 70)
    print()
    
    # 1. 准备测试字体数据
    print("📦 步骤 1: 创建测试字体数据")
    print("-" * 70)
    
    # 创建 Head
    head = LVGLHead(
        font_size=24,
        ascent=20,
        descent=-4,
        typo_ascent=20,
        typo_descent=-4,
        typo_line_gap=0,
        min_y=-5,
        max_y=22,
        default_advance_width=12,
        kerning_scale=0.25,
        index_to_loc_format=0,
        glyph_id_format=0,
        advance_width_format=0,
        bpp=4,
        bbox_x_bits=4,
        bbox_y_bits=4,
        bbox_w_bits=4,
        bbox_h_bits=4,
        advance_width_bits=8,
        compression_id=CompressionType.NONE,
        subpixel_mode=SubpixelMode.NONE,
        underline_position=-2,
        underline_thickness=1
    )
    print(f"  ✅ 字体头部: {head.font_size}px, {head.bpp}-bit")
    
    # 创建 Cmap
    cmap = LVGLCmap()
    
    # 数字范围 (0-9)
    subtable_digits = CmapSubtable(
        range_start=0x30,  # '0'
        range_length=10,   # 0-9
        glyph_id_start=1,
        format=CmapFormat.FORMAT0_TINY
    )
    cmap.add_subtable(subtable_digits)
    
    # 大写字母范围 (A-E, 简化演示)
    subtable_upper = CmapSubtable(
        range_start=0x41,  # 'A'
        range_length=5,    # A-E
        glyph_id_start=11,
        format=CmapFormat.FORMAT0_TINY
    )
    cmap.add_subtable(subtable_upper)
    
    print(f"  ✅ 字符映射表: {len(cmap.subtables)} 个子表")
    print(f"     - 数字: 0-9 (10 chars)")
    print(f"     - 大写: A-E (5 chars)")
    
    # 创建 Glyf
    glyf = LVGLGlyf(bpp=4, compression=CompressionType.NONE)
    
    # 添加保留字形
    reserved = GlyphData(
        glyph_id=0,
        unicode=0,
        bitmap=np.zeros((1, 1), dtype=np.uint8),
        bitmap_index=0,
        advance_width=0.0,
        box_w=0,
        box_h=0,
        ofs_x=0,
        ofs_y=0
    )
    glyf.add_glyph(reserved)
    
    # 添加数字 0-9 的简化字形
    bitmap_offset = 0
    for i in range(10):
        # 创建简单的位图 (6x8)
        bitmap = np.random.randint(0, 16, (8, 6), dtype=np.uint8)
        
        glyph = GlyphData(
            glyph_id=i + 1,
            unicode=0x30 + i,  # '0' + i
            bitmap=bitmap,
            bitmap_index=bitmap_offset,
            advance_width=10.0,
            box_w=6,
            box_h=8,
            ofs_x=1,
            ofs_y=-1
        )
        glyf.add_glyph(glyph)
        bitmap_offset += 48  # 6 * 8 = 48 pixels
    
    # 添加字母 A-E
    for i in range(5):
        bitmap = np.random.randint(0, 16, (10, 8), dtype=np.uint8)
        
        glyph = GlyphData(
            glyph_id=i + 11,
            unicode=0x41 + i,  # 'A' + i
            bitmap=bitmap,
            bitmap_index=bitmap_offset,
            advance_width=12.0,
            box_w=8,
            box_h=10,
            ofs_x=0,
            ofs_y=0
        )
        glyf.add_glyph(glyph)
        bitmap_offset += 80  # 8 * 10 = 80 pixels
    
    print(f"  ✅ 字形表: {len(glyf.glyphs)} 个字形")
    print(f"     - 位图总大小: {glyf.total_bitmap_size} 字节")
    
    # 创建 Font
    font = LVGLFont(
        name="demo_font_24",
        head=head,
        cmap=cmap,
        glyf=glyf
    )
    
    print(f"  ✅ 字体创建完成: {font.name}")
    print()
    
    # 2. 验证字体
    print("🔍 步骤 2: 验证字体数据")
    print("-" * 70)
    
    errors = font.validate()
    if errors:
        print("  ❌ 验证失败:")
        for err in errors:
            print(f"     - {err}")
        return
    
    print("  ✅ 字体数据验证通过")
    print(f"     - 字形数量: {font.glyph_count}")
    print(f"     - 行高: {font.head.line_height}px")
    print(f"     - 基线: {font.head.base_line}px")
    print()
    
    # 3. 生成 C 代码
    print("⚙️  步骤 3: 生成 LVGL C 代码")
    print("-" * 70)
    
    writer = LVGLWriter(lv_include="lvgl.h", version_major=9)
    c_code = writer.generate_c_code(font)
    
    print(f"  ✅ C 代码生成完成")
    print(f"     - 代码长度: {len(c_code)} 字节 ({len(c_code) // 1024} KB)")
    print(f"     - 行数: {c_code.count(chr(10))}")
    print()
    
    # 4. 显示代码片段
    print("📄 步骤 4: C 代码预览")
    print("-" * 70)
    
    lines = c_code.split('\n')
    
    # 显示头部
    print("  头部 (前 15 行):")
    for i, line in enumerate(lines[:15], 1):
        print(f"    {i:3d} | {line}")
    
    print("\n  ...")
    
    # 查找关键部分
    for keyword in ["glyph_bitmap", "cmaps", "const lv_font_t"]:
        for i, line in enumerate(lines):
            if keyword in line:
                print(f"\n  关键行 (第 {i+1} 行): {line[:60]}...")
                break
    
    print()
    
    # 5. 写入文件
    print("💾 步骤 5: 写入文件")
    print("-" * 70)
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"{font.name}.c"
    writer.write(font, str(output_file))
    
    print(f"  ✅ 文件已保存: {output_file}")
    print(f"     - 文件大小: {output_file.stat().st_size} 字节")
    print()
    
    # 6. 检查生成的代码结构
    print("🔎 步骤 6: 代码结构分析")
    print("-" * 70)
    
    keywords = {
        "glyph_bitmap": "字形位图数组",
        "glyph_dsc": "字形描述符数组",
        "cmaps": "字符映射表数组",
        "font_dsc": "字体描述符结构",
        f"const lv_font_t {font.name}": "公共字体声明"
    }
    
    for keyword, description in keywords.items():
        count = c_code.count(keyword)
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {description}: {count} 处")
    
    print()
    
    # 7. 统计信息
    print("📊 步骤 7: 统计信息")
    print("-" * 70)
    
    stats = {
        "字体名称": font.name,
        "字体大小": f"{font.head.font_size}px",
        "位深度": f"{font.head.bpp}-bit",
        "字形数量": font.glyph_count,
        "字符范围": "0-9, A-E",
        "压缩类型": "无压缩 (NONE)",
        "C 代码大小": f"{len(c_code) // 1024} KB",
        "输出文件": str(output_file)
    }
    
    for key, value in stats.items():
        print(f"  📌 {key}: {value}")
    
    print()
    print("=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)
    print()
    print("💡 提示:")
    print("  - 生成的 C 文件可以直接在 LVGL 项目中使用")
    print("  - 在代码中使用: lv_font_declare(demo_font_24);")
    print("  - 设置字体: lv_obj_set_style_text_font(obj, &demo_font_24, 0);")
    print()


if __name__ == '__main__':
    demo_lvgl_writer()
