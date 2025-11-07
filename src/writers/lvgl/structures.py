"""
LVGL 字体格式数据结构定义

本模块定义了 LVGL 字体格式的所有数据结构，参考 lv_font_conv 的实现。

参考文档：
- https://docs.lvgl.io/master/overview/font.html
- lv_font_conv/doc/font_spec.md
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import IntEnum
import numpy as np


class CompressionType(IntEnum):
    """压缩算法类型"""
    NONE = 0           # 无压缩
    RLE = 1            # RLE + XOR 预过滤
    RLE_NO_PREFILTER = 2  # 仅 RLE，无 XOR 预过滤


class SubpixelMode(IntEnum):
    """亚像素渲染模式"""
    NONE = 0      # 无亚像素渲染
    HORIZONTAL = 1  # 水平 3x 分辨率
    VERTICAL = 2    # 垂直 3x 分辨率


class CmapFormat(IntEnum):
    """字符映射表格式"""
    FORMAT0_TINY = 0    # 紧凑型连续格式
    FORMAT0_FULL = 1    # 完整连续格式
    SPARSE_TINY = 2     # 紧凑型稀疏格式
    SPARSE_FULL = 3     # 完整稀疏格式


@dataclass
class CmapSubtable:
    """
    字符映射子表
    
    将 Unicode 码点映射到字形 ID。
    """
    range_start: int              # 范围起始码点
    range_length: int             # 范围长度
    glyph_id_start: int          # 起始字形 ID
    format: CmapFormat           # 子表格式
    unicode_list: Optional[List[int]] = None    # 稀疏格式的 Unicode 列表
    glyph_id_ofs_list: Optional[List[int]] = None  # 字形 ID 偏移列表
    
    @property
    def range_end(self) -> int:
        """范围结束码点"""
        return self.range_start + self.range_length - 1
    
    @property
    def entries_count(self) -> int:
        """条目数量"""
        if self.unicode_list:
            return len(self.unicode_list)
        if self.glyph_id_ofs_list:
            return len(self.glyph_id_ofs_list)
        return 0


@dataclass
class GlyphData:
    """
    字形数据
    
    包含单个字形的位图和度量信息。
    """
    glyph_id: int                # 字形 ID
    unicode: int                 # Unicode 码点
    bitmap: np.ndarray          # 位图数据 (numpy 数组)
    bitmap_index: int           # 位图在总位图中的索引/偏移
    advance_width: float        # 前进宽度 (像素)
    box_w: int                  # 边界框宽度
    box_h: int                  # 边界框高度
    ofs_x: int                  # X 偏移
    ofs_y: int                  # Y 偏移
    
    @property
    def adv_w_fp(self) -> int:
        """前进宽度 (FP12.4 定点数格式)"""
        return round(self.advance_width * 16)


@dataclass
class KernPair:
    """
    字距调整对
    
    记录两个字形之间的间距调整。
    """
    left_glyph_id: int          # 左字形 ID
    right_glyph_id: int         # 右字形 ID
    value: int                  # 调整值 (像素)
    
    def to_fp(self, scale: float) -> int:
        """转换为 FP4.4 定点数"""
        return round(self.value / scale)


@dataclass
class LVGLHead:
    """
    LVGL 字体头部信息 (head 表)
    
    包含字体的全局信息和度量数据。
    """
    font_size: int              # 字体大小 (像素)
    ascent: int                 # 上升高度
    descent: int                # 下降高度 (负数)
    typo_ascent: int           # 排版上升高度
    typo_descent: int          # 排版下降高度
    typo_line_gap: int         # 排版行间距
    min_y: int                 # 最小 Y 坐标
    max_y: int                 # 最大 Y 坐标
    default_advance_width: int # 默认前进宽度
    kerning_scale: float       # 字距缩放 (FP12.4)
    index_to_loc_format: int   # loca 表格式 (0=Offset16, 1=Offset32)
    glyph_id_format: int       # 字形 ID 格式 (0=1字节, 1=2字节)
    advance_width_format: int  # 前进宽度格式 (0=整数, 1=FP4)
    bpp: int                   # 每像素位数 (1-4)
    bbox_x_bits: int           # 边界框 X 坐标位数
    bbox_y_bits: int           # 边界框 Y 坐标位数
    bbox_w_bits: int           # 边界框宽度位数
    bbox_h_bits: int           # 边界框高度位数
    advance_width_bits: int    # 前进宽度位数
    compression_id: CompressionType  # 压缩算法 ID
    subpixel_mode: SubpixelMode      # 亚像素模式
    underline_position: int    # 下划线位置
    underline_thickness: int   # 下划线粗细
    
    @property
    def line_height(self) -> int:
        """行高"""
        return self.ascent - self.descent
    
    @property
    def base_line(self) -> int:
        """基线 (从底部测量)"""
        return -self.descent
    
    @property
    def kerning_scale_fp(self) -> int:
        """字距缩放 FP12.4 格式"""
        return round(self.kerning_scale * 16)


@dataclass
class LVGLCmap:
    """
    LVGL 字符映射表 (cmap 表)
    
    将 Unicode 码点映射到字形 ID。
    """
    subtables: List[CmapSubtable] = field(default_factory=list)
    
    def add_subtable(self, subtable: CmapSubtable) -> None:
        """添加子表"""
        self.subtables.append(subtable)
    
    def find_glyph_id(self, unicode: int) -> Optional[int]:
        """
        查找 Unicode 对应的字形 ID
        
        Args:
            unicode: Unicode 码点
            
        Returns:
            字形 ID，如果未找到返回 None
        """
        for subtable in self.subtables:
            if subtable.range_start <= unicode <= subtable.range_end:
                offset = unicode - subtable.range_start
                
                if subtable.format in (CmapFormat.FORMAT0_TINY, CmapFormat.FORMAT0_FULL):
                    # 连续格式
                    if subtable.glyph_id_ofs_list:
                        return subtable.glyph_id_start + subtable.glyph_id_ofs_list[offset]
                    return subtable.glyph_id_start + offset
                    
                elif subtable.format in (CmapFormat.SPARSE_TINY, CmapFormat.SPARSE_FULL):
                    # 稀疏格式
                    if subtable.unicode_list:
                        try:
                            idx = subtable.unicode_list.index(unicode)
                            if subtable.glyph_id_ofs_list:
                                return subtable.glyph_id_start + subtable.glyph_id_ofs_list[idx]
                            return subtable.glyph_id_start + idx
                        except ValueError:
                            continue
        
        return None
    
    @property
    def total_glyphs(self) -> int:
        """总字形数"""
        max_id = 0
        for subtable in self.subtables:
            if subtable.format in (CmapFormat.FORMAT0_TINY, CmapFormat.FORMAT0_FULL):
                max_id = max(max_id, subtable.glyph_id_start + subtable.range_length)
            else:
                if subtable.glyph_id_ofs_list:
                    max_id = max(max_id, subtable.glyph_id_start + max(subtable.glyph_id_ofs_list))
                else:
                    max_id = max(max_id, subtable.glyph_id_start + subtable.entries_count)
        return max_id


@dataclass
class LVGLGlyf:
    """
    LVGL 字形表 (glyf 表)
    
    包含所有字形的位图数据和描述符。
    """
    glyphs: List[GlyphData] = field(default_factory=list)
    bpp: int = 4                    # 每像素位数
    compression: CompressionType = CompressionType.RLE
    
    def add_glyph(self, glyph: GlyphData) -> None:
        """添加字形"""
        self.glyphs.append(glyph)
    
    def get_glyph(self, glyph_id: int) -> Optional[GlyphData]:
        """获取字形"""
        for glyph in self.glyphs:
            if glyph.glyph_id == glyph_id:
                return glyph
        return None
    
    @property
    def total_bitmap_size(self) -> int:
        """总位图大小 (字节)"""
        if not self.glyphs:
            return 0
        return sum(glyph.bitmap.nbytes for glyph in self.glyphs)


@dataclass
class LVGLKern:
    """
    LVGL 字距调整表 (kern 表)
    
    存储字形对之间的间距调整信息。
    支持两种格式：
    - Format 0: 字形对列表
    - Format 3: 基于类的字距调整
    """
    pairs: List[KernPair] = field(default_factory=list)
    use_classes: bool = False       # 是否使用类格式
    
    # Format 3 数据
    left_classes: int = 0
    right_classes: int = 0
    left_mapping: List[int] = field(default_factory=list)
    right_mapping: List[int] = field(default_factory=list)
    class_values: List[int] = field(default_factory=list)
    
    def add_pair(self, pair: KernPair) -> None:
        """添加字距对"""
        self.pairs.append(pair)
    
    @property
    def has_kerning(self) -> bool:
        """是否有字距调整"""
        return len(self.pairs) > 0 or len(self.class_values) > 0
    
    @property
    def pair_count(self) -> int:
        """字距对数量"""
        return len(self.pairs)


@dataclass
class LVGLFont:
    """
    LVGL 字体完整数据结构
    
    包含字体的所有表和元信息。
    """
    name: str                       # 字体名称
    head: LVGLHead                  # 头部表
    cmap: LVGLCmap                  # 字符映射表
    glyf: LVGLGlyf                  # 字形表
    kern: Optional[LVGLKern] = None # 字距调整表
    fallback: Optional[str] = None  # 回退字体名称
    
    @property
    def has_kerning(self) -> bool:
        """是否有字距调整"""
        return self.kern is not None and self.kern.has_kerning
    
    @property
    def glyph_count(self) -> int:
        """字形数量"""
        return len(self.glyf.glyphs)
    
    def validate(self) -> List[str]:
        """
        验证字体数据完整性
        
        Returns:
            错误列表，如果为空则验证通过
        """
        errors = []
        
        # 检查必需字段
        if not self.name:
            errors.append("字体名称不能为空")
        
        if self.glyph_count == 0:
            errors.append("字形数量不能为 0")
        
        # 检查 BPP 一致性
        if self.head.bpp != self.glyf.bpp:
            errors.append(f"BPP 不一致: head={self.head.bpp}, glyf={self.glyf.bpp}")
        
        # 检查压缩类型
        if self.head.compression_id != self.glyf.compression:
            errors.append(f"压缩类型不一致: head={self.head.compression_id}, glyf={self.glyf.compression}")
        
        # 检查字形 ID 连续性
        glyph_ids = [g.glyph_id for g in self.glyf.glyphs]
        if glyph_ids != sorted(glyph_ids):
            errors.append("字形 ID 未排序")
        
        # 检查 cmap 和 glyf 一致性
        max_glyph_id = max(glyph_ids) if glyph_ids else 0
        cmap_max_id = self.cmap.total_glyphs
        if cmap_max_id > max_glyph_id + 1:
            errors.append(f"cmap 引用了不存在的字形 ID: {cmap_max_id} > {max_glyph_id}")
        
        return errors
