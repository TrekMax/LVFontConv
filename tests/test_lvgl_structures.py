"""
测试 LVGL 数据结构
"""

import pytest
import numpy as np
import sys
sys.path.insert(0, 'src')

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


class TestCmapSubtable:
    """测试 CmapSubtable 数据类"""
    
    def test_create_format0_tiny(self):
        """测试创建 FORMAT0_TINY 子表"""
        subtable = CmapSubtable(
            range_start=0x20,
            range_length=96,
            glyph_id_start=1,
            format=CmapFormat.FORMAT0_TINY
        )
        
        assert subtable.range_start == 0x20
        assert subtable.range_end == 0x7F
        assert subtable.entries_count == 0
    
    def test_create_sparse_full(self):
        """测试创建 SPARSE_FULL 子表"""
        subtable = CmapSubtable(
            range_start=0x4E00,
            range_length=100,
            glyph_id_start=100,
            format=CmapFormat.SPARSE_FULL,
            unicode_list=[0x4E00, 0x4E01, 0x4E03],
            glyph_id_ofs_list=[0, 1, 2]
        )
        
        assert subtable.range_start == 0x4E00
        assert subtable.entries_count == 3
        assert len(subtable.unicode_list) == 3


class TestGlyphData:
    """测试 GlyphData 数据类"""
    
    def test_create_glyph(self):
        """测试创建字形数据"""
        bitmap = np.array([[15, 15], [15, 0]], dtype=np.uint8)
        glyph = GlyphData(
            glyph_id=1,
            unicode=0x41,  # 'A'
            bitmap=bitmap,
            bitmap_index=0,
            advance_width=12.5,
            box_w=2,
            box_h=2,
            ofs_x=1,
            ofs_y=-1
        )
        
        assert glyph.glyph_id == 1
        assert glyph.unicode == 0x41
        assert glyph.adv_w_fp == 200  # 12.5 * 16
        assert glyph.bitmap.shape == (2, 2)
    
    def test_advance_width_fp(self):
        """测试前进宽度 FP12.4 转换"""
        glyph = GlyphData(
            glyph_id=1,
            unicode=0x41,
            bitmap=np.zeros((1, 1), dtype=np.uint8),
            bitmap_index=0,
            advance_width=10.0,
            box_w=1,
            box_h=1,
            ofs_x=0,
            ofs_y=0
        )
        
        assert glyph.adv_w_fp == 160  # 10.0 * 16


class TestKernPair:
    """测试 KernPair 数据类"""
    
    def test_create_kern_pair(self):
        """测试创建字距对"""
        pair = KernPair(
            left_glyph_id=1,
            right_glyph_id=2,
            value=-2
        )
        
        assert pair.left_glyph_id == 1
        assert pair.right_glyph_id == 2
        assert pair.value == -2
    
    def test_to_fp(self):
        """测试转换为定点数"""
        pair = KernPair(left_glyph_id=1, right_glyph_id=2, value=-4)
        fp_value = pair.to_fp(scale=0.25)  # scale = 0.25
        
        assert fp_value == -16  # -4 / 0.25


class TestLVGLHead:
    """测试 LVGLHead 数据类"""
    
    def test_create_head(self):
        """测试创建字体头部"""
        head = LVGLHead(
            font_size=24,
            ascent=20,
            descent=-4,
            typo_ascent=20,
            typo_descent=-4,
            typo_line_gap=0,
            min_y=-5,
            max_y=20,
            default_advance_width=12,
            kerning_scale=0.25,
            index_to_loc_format=0,
            glyph_id_format=0,
            advance_width_format=1,
            bpp=4,
            bbox_x_bits=4,
            bbox_y_bits=4,
            bbox_w_bits=4,
            bbox_h_bits=4,
            advance_width_bits=8,
            compression_id=CompressionType.RLE,
            subpixel_mode=SubpixelMode.NONE,
            underline_position=-2,
            underline_thickness=1
        )
        
        assert head.font_size == 24
        assert head.line_height == 24
        assert head.base_line == 4
        assert head.kerning_scale_fp == 4  # 0.25 * 16


class TestLVGLCmap:
    """测试 LVGLCmap 数据类"""
    
    def test_create_empty_cmap(self):
        """测试创建空字符映射表"""
        cmap = LVGLCmap()
        assert len(cmap.subtables) == 0
        assert cmap.total_glyphs == 0
    
    def test_add_subtable(self):
        """测试添加子表"""
        cmap = LVGLCmap()
        subtable = CmapSubtable(
            range_start=0x20,
            range_length=96,
            glyph_id_start=1,
            format=CmapFormat.FORMAT0_TINY
        )
        cmap.add_subtable(subtable)
        
        assert len(cmap.subtables) == 1
        assert cmap.total_glyphs == 97  # 1 + 96
    
    def test_find_glyph_id_format0(self):
        """测试查找字形 ID (FORMAT0)"""
        cmap = LVGLCmap()
        subtable = CmapSubtable(
            range_start=0x41,  # 'A'
            range_length=26,   # A-Z
            glyph_id_start=10,
            format=CmapFormat.FORMAT0_TINY
        )
        cmap.add_subtable(subtable)
        
        # 查找 'A'
        glyph_id = cmap.find_glyph_id(0x41)
        assert glyph_id == 10
        
        # 查找 'Z'
        glyph_id = cmap.find_glyph_id(0x5A)
        assert glyph_id == 35  # 10 + 25
        
        # 查找不存在的字符
        glyph_id = cmap.find_glyph_id(0x61)  # 'a'
        assert glyph_id is None
    
    def test_find_glyph_id_sparse(self):
        """测试查找字形 ID (SPARSE)"""
        cmap = LVGLCmap()
        subtable = CmapSubtable(
            range_start=0x4E00,
            range_length=100,
            glyph_id_start=100,
            format=CmapFormat.SPARSE_TINY,
            unicode_list=[0x4E00, 0x4E01, 0x4E03]
        )
        cmap.add_subtable(subtable)
        
        # 查找存在的字符
        glyph_id = cmap.find_glyph_id(0x4E00)
        assert glyph_id == 100
        
        glyph_id = cmap.find_glyph_id(0x4E03)
        assert glyph_id == 102
        
        # 查找不存在的字符
        glyph_id = cmap.find_glyph_id(0x4E02)
        assert glyph_id is None


class TestLVGLGlyf:
    """测试 LVGLGlyf 数据类"""
    
    def test_create_empty_glyf(self):
        """测试创建空字形表"""
        glyf = LVGLGlyf(bpp=4, compression=CompressionType.RLE)
        
        assert len(glyf.glyphs) == 0
        assert glyf.bpp == 4
        assert glyf.total_bitmap_size == 0
    
    def test_add_glyph(self):
        """测试添加字形"""
        glyf = LVGLGlyf()
        bitmap = np.array([[15, 15]], dtype=np.uint8)
        glyph = GlyphData(
            glyph_id=1,
            unicode=0x41,
            bitmap=bitmap,
            bitmap_index=0,
            advance_width=10.0,
            box_w=2,
            box_h=1,
            ofs_x=0,
            ofs_y=0
        )
        
        glyf.add_glyph(glyph)
        assert len(glyf.glyphs) == 1
        assert glyf.total_bitmap_size == 2  # 2 像素
    
    def test_get_glyph(self):
        """测试获取字形"""
        glyf = LVGLGlyf()
        bitmap = np.array([[15]], dtype=np.uint8)
        glyph1 = GlyphData(
            glyph_id=1, unicode=0x41, bitmap=bitmap,
            bitmap_index=0, advance_width=10.0,
            box_w=1, box_h=1, ofs_x=0, ofs_y=0
        )
        glyph2 = GlyphData(
            glyph_id=2, unicode=0x42, bitmap=bitmap,
            bitmap_index=1, advance_width=10.0,
            box_w=1, box_h=1, ofs_x=0, ofs_y=0
        )
        
        glyf.add_glyph(glyph1)
        glyf.add_glyph(glyph2)
        
        found = glyf.get_glyph(1)
        assert found is not None
        assert found.unicode == 0x41
        
        not_found = glyf.get_glyph(999)
        assert not_found is None


class TestLVGLKern:
    """测试 LVGLKern 数据类"""
    
    def test_create_empty_kern(self):
        """测试创建空字距表"""
        kern = LVGLKern()
        
        assert len(kern.pairs) == 0
        assert not kern.has_kerning
        assert kern.pair_count == 0
    
    def test_add_pair(self):
        """测试添加字距对"""
        kern = LVGLKern()
        pair = KernPair(left_glyph_id=1, right_glyph_id=2, value=-2)
        
        kern.add_pair(pair)
        assert kern.pair_count == 1
        assert kern.has_kerning
    
    def test_format3_data(self):
        """测试 Format 3 数据"""
        kern = LVGLKern(use_classes=True)
        kern.left_classes = 5
        kern.right_classes = 5
        kern.class_values = [0, -1, -2, 0, 0]
        
        assert kern.use_classes
        assert kern.has_kerning


class TestLVGLFont:
    """测试 LVGLFont 数据类"""
    
    def create_minimal_font(self) -> LVGLFont:
        """创建最小化的测试字体"""
        head = LVGLHead(
            font_size=16, ascent=14, descent=-2,
            typo_ascent=14, typo_descent=-2, typo_line_gap=0,
            min_y=-3, max_y=15, default_advance_width=8,
            kerning_scale=0.25, index_to_loc_format=0,
            glyph_id_format=0, advance_width_format=0, bpp=4,
            bbox_x_bits=4, bbox_y_bits=4, bbox_w_bits=4, bbox_h_bits=4,
            advance_width_bits=8, compression_id=CompressionType.RLE,
            subpixel_mode=SubpixelMode.NONE,
            underline_position=-1, underline_thickness=1
        )
        
        cmap = LVGLCmap()
        subtable = CmapSubtable(
            range_start=0x41, range_length=1,
            glyph_id_start=1, format=CmapFormat.FORMAT0_TINY
        )
        cmap.add_subtable(subtable)
        
        glyf = LVGLGlyf(bpp=4, compression=CompressionType.RLE)
        bitmap = np.array([[15]], dtype=np.uint8)
        glyph = GlyphData(
            glyph_id=1, unicode=0x41, bitmap=bitmap,
            bitmap_index=0, advance_width=8.0,
            box_w=1, box_h=1, ofs_x=0, ofs_y=0
        )
        glyf.add_glyph(glyph)
        
        return LVGLFont(
            name="test_font",
            head=head,
            cmap=cmap,
            glyf=glyf
        )
    
    def test_create_font(self):
        """测试创建字体"""
        font = self.create_minimal_font()
        
        assert font.name == "test_font"
        assert font.glyph_count == 1
        assert not font.has_kerning
    
    def test_font_with_kerning(self):
        """测试带字距调整的字体"""
        font = self.create_minimal_font()
        kern = LVGLKern()
        pair = KernPair(left_glyph_id=1, right_glyph_id=2, value=-1)
        kern.add_pair(pair)
        font.kern = kern
        
        assert font.has_kerning
    
    def test_validate_success(self):
        """测试验证成功"""
        font = self.create_minimal_font()
        errors = font.validate()
        
        assert len(errors) == 0
    
    def test_validate_empty_name(self):
        """测试验证失败 - 空名称"""
        font = self.create_minimal_font()
        font.name = ""
        errors = font.validate()
        
        assert len(errors) > 0
        assert any("名称" in err for err in errors)
    
    def test_validate_bpp_mismatch(self):
        """测试验证失败 - BPP 不一致"""
        font = self.create_minimal_font()
        font.head.bpp = 2
        font.glyf.bpp = 4
        errors = font.validate()
        
        assert len(errors) > 0
        assert any("BPP" in err for err in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
