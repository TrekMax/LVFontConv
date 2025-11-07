"""
测试 LVGL Writer
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, 'src')

from writers.lvgl.writer import LVGLWriter
from writers.lvgl.structures import (
    LVGLFont,
    LVGLHead,
    LVGLCmap,
    LVGLGlyf,
    LVGLKern,
    CmapSubtable,
    GlyphData,
    KernPair,
    CompressionType,
    SubpixelMode,
    CmapFormat
)


class TestLVGLWriter:
    """测试 LVGL Writer"""
    
    def create_test_font(self) -> LVGLFont:
        """创建测试字体"""
        # Head
        head = LVGLHead(
            font_size=16,
            ascent=14,
            descent=-2,
            typo_ascent=14,
            typo_descent=-2,
            typo_line_gap=0,
            min_y=-3,
            max_y=15,
            default_advance_width=8,
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
            underline_position=-1,
            underline_thickness=1
        )
        
        # Cmap
        cmap = LVGLCmap()
        
        # ASCII 范围 (简化：只包含 A-B)
        subtable = CmapSubtable(
            range_start=0x41,  # 'A'
            range_length=2,    # A, B
            glyph_id_start=1,
            format=CmapFormat.FORMAT0_TINY
        )
        cmap.add_subtable(subtable)
        
        # Glyf
        glyf = LVGLGlyf(bpp=4, compression=CompressionType.NONE)
        
        # 保留字形 (ID 0)
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
        
        # 添加字形 A
        bitmap_a = np.array([
            [0, 15, 15, 0],
            [15, 0, 0, 15],
            [15, 15, 15, 15],
            [15, 0, 0, 15]
        ], dtype=np.uint8)
        
        glyph_a = GlyphData(
            glyph_id=1,
            unicode=0x41,
            bitmap=bitmap_a,
            bitmap_index=0,
            advance_width=8.0,
            box_w=4,
            box_h=4,
            ofs_x=0,
            ofs_y=0
        )
        glyf.add_glyph(glyph_a)
        
        # 添加字形 B
        bitmap_b = np.array([
            [15, 15, 15, 0],
            [15, 0, 0, 15],
            [15, 15, 15, 0],
            [15, 0, 0, 15],
            [15, 15, 15, 0]
        ], dtype=np.uint8)
        
        glyph_b = GlyphData(
            glyph_id=2,
            unicode=0x42,
            bitmap=bitmap_b,
            bitmap_index=16,
            advance_width=8.0,
            box_w=4,
            box_h=5,
            ofs_x=0,
            ofs_y=0
        )
        glyf.add_glyph(glyph_b)
        
        # Font
        font = LVGLFont(
            name="test_font",
            head=head,
            cmap=cmap,
            glyf=glyf
        )
        
        return font
    
    def test_create_writer(self):
        """测试创建写入器"""
        writer = LVGLWriter()
        
        assert writer.lv_include == "lvgl.h"
        assert writer.version_major == 9
    
    def test_write_to_file(self):
        """测试写入文件"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_font.c"
            writer.write(font, str(output_path))
            
            # 验证文件存在
            assert output_path.exists()
            
            # 读取并验证内容
            content = output_path.read_text()
            
            # 检查关键部分
            assert "test_font" in content
            assert "glyph_bitmap" in content
            assert "glyph_dsc" in content
            assert "cmaps" in content
            assert "lv_font_t" in content
    
    def test_generate_c_code(self):
        """测试生成 C 代码"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        code = writer.generate_c_code(font)
        
        # 验证代码结构
        assert "/*******************************************************************************" in code
        assert "Size: 16 px" in code
        assert "Bpp: 4" in code
        assert "#ifndef TEST_FONT" in code
        assert "#define TEST_FONT 1" in code
        assert "glyph_bitmap" in code
        assert "glyph_dsc" in code
        assert "const lv_font_t test_font" in code
    
    def test_generate_header(self):
        """测试生成文件头"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        header = writer._generate_header(font)
        
        assert "Size: 16 px" in header
        assert "Bpp: 4" in header
        assert "lvgl.h" in header
        assert "#ifdef __has_include" in header
    
    def test_generate_glyf_section(self):
        """测试生成字形表"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        glyf_section = writer._generate_glyf_section(font)
        
        # 检查位图数组
        assert "glyph_bitmap" in glyf_section
        assert "U+0041" in glyf_section  # 'A'
        assert "U+0042" in glyf_section  # 'B'
        
        # 检查字形描述符
        assert "glyph_dsc" in glyf_section
        assert "bitmap_index" in glyf_section
        assert "adv_w" in glyf_section
        assert "box_w" in glyf_section
    
    def test_generate_cmap_section(self):
        """测试生成字符映射表"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        cmap_section = writer._generate_cmap_section(font)
        
        assert "cmaps" in cmap_section
        assert "range_start" in cmap_section
        assert "range_length" in cmap_section
        assert "glyph_id_start" in cmap_section
        assert "LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY" in cmap_section
    
    def test_generate_kern_section_empty(self):
        """测试生成空字距表"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        kern_section = writer._generate_kern_section(font)
        
        # 没有字距调整，应该返回空
        assert kern_section == ""
    
    def test_generate_kern_section_with_pairs(self):
        """测试生成字距对"""
        font = self.create_test_font()
        
        # 添加字距调整
        kern = LVGLKern()
        pair = KernPair(left_glyph_id=1, right_glyph_id=2, value=-2)
        kern.add_pair(pair)
        font.kern = kern
        
        writer = LVGLWriter()
        kern_section = writer._generate_kern_section(font)
        
        assert "KERNING" in kern_section
        assert "kern_pair_glyph_ids" in kern_section
        assert "kern_pair_values" in kern_section
        assert "kern_pairs" in kern_section
    
    def test_generate_font_descriptor(self):
        """测试生成字体描述符"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        font_dsc = writer._generate_font_descriptor(font)
        
        assert "font_dsc" in font_dsc
        assert "glyph_bitmap" in font_dsc
        assert "glyph_dsc" in font_dsc
        assert "cmaps" in font_dsc
        assert "kern_dsc = NULL" in font_dsc
        assert f"bpp = {font.head.bpp}" in font_dsc
    
    def test_generate_public_font(self):
        """测试生成公共字体声明"""
        font = self.create_test_font()
        writer = LVGLWriter()
        
        public_font = writer._generate_public_font(font)
        
        assert "const lv_font_t test_font" in public_font
        assert "get_glyph_dsc" in public_font
        assert "get_glyph_bitmap" in public_font
        assert "line_height" in public_font
        assert "base_line" in public_font
        assert f"line_height = {font.head.line_height}" in public_font
    
    def test_format_hex_array(self):
        """测试格式化十六进制数组"""
        writer = LVGLWriter()
        
        data = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55])
        result = writer._format_hex_array(data, cols=3)
        
        assert "0x00" in result
        assert "0x11" in result
        assert "0x55" in result
        assert result.count("\n") >= 1  # 至少有一个换行
    
    def test_cmap_format_to_enum(self):
        """测试 CmapFormat 转换"""
        writer = LVGLWriter()
        
        assert writer._cmap_format_to_enum(CmapFormat.FORMAT0_TINY) == "LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY"
        assert writer._cmap_format_to_enum(CmapFormat.FORMAT0_FULL) == "LV_FONT_FMT_TXT_CMAP_FORMAT0_FULL"
        assert writer._cmap_format_to_enum(CmapFormat.SPARSE_TINY) == "LV_FONT_FMT_TXT_CMAP_SPARSE_TINY"
        assert writer._cmap_format_to_enum(CmapFormat.SPARSE_FULL) == "LV_FONT_FMT_TXT_CMAP_SPARSE_FULL"
    
    def test_kern_to_fp(self):
        """测试字距值转换"""
        writer = LVGLWriter()
        
        # scale = 0.25, value = -4
        result = writer._kern_to_fp(-4, 0.25)
        assert result == -16  # -4 / 0.25 = -16
        
        # scale = 0.5, value = -2
        result = writer._kern_to_fp(-2, 0.5)
        assert result == -4  # -2 / 0.5 = -4
    
    def test_validate_font_before_write(self):
        """测试写入前验证字体"""
        # 创建无效字体（空名称）
        font = self.create_test_font()
        font.name = ""
        
        writer = LVGLWriter()
        
        with pytest.raises(ValueError, match="字体数据验证失败"):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test.c"
                writer.write(font, str(output_path))
    
    def test_custom_lv_include(self):
        """测试自定义 LVGL 头文件路径"""
        writer = LVGLWriter(lv_include="custom/lvgl.h")
        
        assert writer.lv_include == "custom/lvgl.h"
        
        font = self.create_test_font()
        header = writer._generate_header(font)
        
        assert "custom/lvgl.h" in header


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
