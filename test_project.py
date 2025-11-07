#!/usr/bin/env python3
"""
测试项目管理功能
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_project_save_load():
    """测试项目保存和加载"""
    from core.project import Project, FontSource
    
    print("=" * 60)
    print("测试项目保存/加载功能")
    print("=" * 60)
    
    # 1. 创建项目
    print("\n1. 创建新项目")
    project = Project()
    print(f"   ✓ 项目创建成功")
    print(f"   显示名称: {project.display_name}")
    
    # 2. 添加字体
    print("\n2. 添加字体")
    fonts = [
        FontSource(
            path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ranges=["0x30-0x39", "0x41-0x5A"],
            symbols="!@#",
            display_name="DejaVu Sans - Numbers & Letters"
        ),
        FontSource(
            path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ranges=["0x61-0x7A"],
            symbols="$%^",
            display_name="DejaVu Sans Bold"
        )
    ]
    
    for font in fonts:
        project.fonts.append(font)
        print(f"   ✓ 添加: {font.display_name}")
    
    # 3. 修改配置
    print("\n3. 修改配置")
    project.config.font_size = 24
    project.config.bpp = 4
    project.config.compression = "rle"
    project.config.output_name = "my_awesome_font"
    project.mark_modified()
    print(f"   ✓ 字体大小: {project.config.font_size}px")
    print(f"   ✓ BPP: {project.config.bpp}")
    print(f"   ✓ 压缩: {project.config.compression}")
    print(f"   ✓ 已修改: {project.is_modified}")
    
    # 4. 保存项目
    print("\n4. 保存项目")
    test_file = "/tmp/test_lvfontconv_project.lvproj"
    success = project.save(test_file)
    if success:
        size = os.path.getsize(test_file)
        print(f"   ✓ 保存成功: {test_file}")
        print(f"   文件大小: {size} 字节")
        print(f"   已修改: {project.is_modified}")
    else:
        print(f"   ✗ 保存失败")
        return False
    
    # 5. 加载项目
    print("\n5. 加载项目")
    project2 = Project()
    success = project2.load(test_file)
    if success:
        print(f"   ✓ 加载成功")
        print(f"   字体数量: {len(project2.fonts)}")
        print(f"   配置:")
        print(f"     - 字体大小: {project2.config.font_size}px")
        print(f"     - BPP: {project2.config.bpp}")
        print(f"     - 输出名称: {project2.config.output_name}")
    else:
        print(f"   ✗ 加载失败")
        return False
    
    # 6. 验证数据
    print("\n6. 验证数据")
    assert len(project2.fonts) == 2, "字体数量不匹配"
    assert project2.fonts[0].display_name == "DejaVu Sans - Numbers & Letters", "字体1名称不匹配"
    assert project2.fonts[1].display_name == "DejaVu Sans Bold", "字体2名称不匹配"
    assert project2.config.font_size == 24, "字体大小不匹配"
    assert project2.config.bpp == 4, "BPP不匹配"
    assert project2.config.output_name == "my_awesome_font", "输出名称不匹配"
    print("   ✓ 所有数据验证通过")
    
    # 7. 测试新建项目
    print("\n7. 测试新建项目")
    project2.new()
    assert len(project2.fonts) == 0, "新建项目应该清空字体列表"
    assert project2.file_path is None, "新建项目不应该有文件路径"
    assert not project2.is_modified, "新建项目不应该标记为已修改"
    print("   ✓ 新建项目功能正常")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_project_save_load()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
