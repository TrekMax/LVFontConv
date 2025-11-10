#!/usr/bin/env python3
"""
生成对比测试文件

用 LVFontConv 生成字体文件,然后与原版 lv_font_conv 的输出对比
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.simple_converter import SimpleFontConverter


def main():
    """生成测试文件"""
    
    # 字体路径(请根据实际情况修改)
    font_path = "../fonts/SourceHanSansCN/SourceHanSansCN-Regular.otf"
    
    # 检查字体文件是否存在
    if not Path(font_path).exists():
        print(f"❌ 字体文件不存在: {font_path}")
        print("\n请修改脚本中的 font_path 变量为实际的字体路径")
        return 1
    
    print("=" * 70)
    print("🎨 LVFontConv 测试文件生成")
    print("=" * 70)
    print()
    
    # 配置参数(与原版工具保持一致)
    config = {
        'font_path': font_path,
        'ranges': ['0x30-0x39'],  # 数字 0-9
        'symbols': '',
        'size': 16,
        'bpp': 4,
        'output_path': '../test_lvfontconv',
        'compression': 'none',  # 先不压缩,方便对比
        'lvgl_version': 8
    }
    
    print("配置参数:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # 执行转换
    print("开始转换...")
    converter = SimpleFontConverter()
    converter.set_progress_callback(lambda msg, pct: print(f"[{pct:3d}%] {msg}"))
    
    success = converter.convert_font(**config)
    
    if success:
        output_file = config['output_path'] + '.c'
        print()
        print(f"✓ 转换成功: {output_file}")
        print()
        print("=" * 70)
        print("📋 下一步: 生成原版文件进行对比")
        print("=" * 70)
        print()
        print("请运行以下命令生成原版文件:")
        print()
        print(f"cd {Path(font_path).parent.parent}")
        print(f"lv_font_conv \\")
        print(f"  --font {font_path} \\")
        print(f"  --size {config['size']} \\")
        print(f"  --bpp {config['bpp']} \\")
        print(f"  --format lvgl \\")
        print(f"  --range {config['ranges'][0]} \\")
        print(f"  --no-compress \\")
        print(f"  -o test_original.c")
        print()
        print("然后运行对比:")
        print()
        print("cd LVFontConv")
        print("python compare_output.py ../test_original.c ../test_lvfontconv.c")
        print()
        return 0
    else:
        print()
        print("❌ 转换失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
