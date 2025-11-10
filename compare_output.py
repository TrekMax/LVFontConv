#!/usr/bin/env python3
"""
对比 LVFontConv 和原版 lv_font_conv 的输出差异

使用方法:
    python compare_output.py <original_file.c> <new_file.c>
"""

import sys
import re
from pathlib import Path


def parse_c_font_file(filepath):
    """解析 C 字体文件,提取关键数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {}
    
    # 提取字体大小
    match = re.search(r'\.line_height\s*=\s*(\d+)', content)
    if match:
        data['line_height'] = int(match.group(1))
    
    # 提取 base_line
    match = re.search(r'\.base_line\s*=\s*(-?\d+)', content)
    if match:
        data['base_line'] = int(match.group(1))
    
    # 提取 BPP
    match = re.search(r'\.bpp\s*=\s*(\d+)', content)
    if match:
        data['bpp'] = int(match.group(1))
    
    # 提取压缩方式
    if 'LV_FONT_FMT_TXT_COMPRESS_RLE' in content:
        data['compression'] = 'RLE'
    elif 'LV_FONT_FMT_TXT_COMPRESS_NONE' in content:
        data['compression'] = 'NONE'
    
    # 提取字形数量
    match = re.search(r'glyph_cnt\s*=\s*(\d+)', content)
    if match:
        data['glyph_count'] = int(match.group(1))
    
    # 提取 cmap 范围
    cmap_ranges = re.findall(r'0x([0-9a-f]+),\s*0x([0-9a-f]+)', content, re.IGNORECASE)
    if cmap_ranges:
        data['cmap_ranges'] = [(int(start, 16), int(end, 16)) for start, end in cmap_ranges[:5]]  # 前5个
    
    # 提取字形位图数据 (前几个字节)
    match = re.search(r'glyph_bitmap\[\]\s*=\s*\{([\s\S]+?)\};', content)
    if match:
        bitmap_str = match.group(1)
        # 提取前20个字节
        bytes_data = re.findall(r'0x([0-9a-f]+)', bitmap_str, re.IGNORECASE)[:20]
        data['bitmap_preview'] = [int(b, 16) for b in bytes_data]
    
    # 提取字形描述数据
    match = re.search(r'glyph_dsc\[\]\s*=\s*\{([\s\S]+?)\};', content)
    if match:
        dsc_str = match.group(1)
        # 计算字形描述的数量
        dsc_entries = re.findall(r'\{[^}]+\}', dsc_str)
        data['glyph_dsc_count'] = len(dsc_entries)
        # 提取前3个字形描述
        data['glyph_dsc_preview'] = dsc_entries[:3]
    
    return data


def compare_fonts(original_data, new_data):
    """对比两个字体数据"""
    print("\n" + "=" * 80)
    print("字体数据对比")
    print("=" * 80)
    
    keys = set(original_data.keys()) | set(new_data.keys())
    
    for key in sorted(keys):
        orig_val = original_data.get(key, 'N/A')
        new_val = new_data.get(key, 'N/A')
        
        if orig_val == new_val:
            status = "✓"
        else:
            status = "✗"
        
        print(f"\n{status} {key}:")
        print(f"  原版: {orig_val}")
        print(f"  新版: {new_val}")
        
        if orig_val != new_val and key == 'bitmap_preview':
            print("  差异分析:")
            if isinstance(orig_val, list) and isinstance(new_val, list):
                for i, (o, n) in enumerate(zip(orig_val, new_val)):
                    if o != n:
                        print(f"    字节{i}: 0x{o:02X} -> 0x{n:02X} (差值: {n-o:+d})")


def main():
    if len(sys.argv) != 3:
        print("使用方法: python compare_output.py <original_file.c> <new_file.c>")
        print("\n示例:")
        print("  # 先用原版工具生成:")
        print("  lv_font_conv --font font.ttf --size 16 --bpp 4 --range 0x20-0x7E -o original.c")
        print("\n  # 再用 LVFontConv 生成 new.c")
        print("\n  # 然后对比:")
        print("  python compare_output.py original.c new.c")
        return 1
    
    original_file = Path(sys.argv[1])
    new_file = Path(sys.argv[2])
    
    if not original_file.exists():
        print(f"错误: 文件不存在: {original_file}")
        return 1
    
    if not new_file.exists():
        print(f"错误: 文件不存在: {new_file}")
        return 1
    
    print(f"\n解析原版文件: {original_file}")
    original_data = parse_c_font_file(original_file)
    
    print(f"解析新版文件: {new_file}")
    new_data = parse_c_font_file(new_file)
    
    compare_fonts(original_data, new_data)
    
    print("\n" + "=" * 80)
    print("对比完成")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
