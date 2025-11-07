"""
Font Converter - 字体转换核心

本模块提供字体转换的核心功能,整合所有转换流程:
1. 加载字体文件 (TrueType/OpenType)
2. 渲染指定的字符范围
3. 构建 LVGL 数据结构
4. 生成输出文件 (C 代码/二进制/JSON)

主要类:
- FontConverter: 字体转换器核心类
- ConversionParams: 转换参数配置

使用示例:
    converter = FontConverter()
    converter.add_font("Arial.ttf", ["0x30-0x39", "0x41-0x5A"])  # 0-9, A-Z
    converter.set_params(size=24, bpp=4, compression="rle")
    converter.convert("output/font_24", format="lvgl")
"""

from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
import numpy as np

from loaders.font_loader import FontLoader, FontFace
from renderers.glyph_renderer import GlyphRenderer, RenderOptions, GlyphMetrics
from writers.lvgl.structures import (
    LVGLFont, LVGLHead, LVGLCmap, LVGLGlyf, LVGLKern,
    CmapSubtable, GlyphData, KernPair,
    CompressionType, SubpixelMode, CmapFormat
)
from writers.lvgl.compress import compress_bitmap
from writers.lvgl.writer import LVGLWriter


@dataclass
class FontSource:
    """单个字体源配置"""
    path: str                                    # 字体文件路径
    ranges: List[str] = field(default_factory=list)  # 字符范围列表 (如 "0x30-0x39")
    symbols: str = ""                           # 单独的符号字符串
    
    
@dataclass
class ConversionParams:
    """转换参数配置"""
    size: int = 24                              # 字体大小 (像素)
    bpp: int = 4                                # 每像素位数 (1, 2, 4, 8)
    compression: str = "none"                   # 压缩模式 ("none", "rle")
    format: str = "lvgl"                        # 输出格式 ("lvgl", "bin", "dump")
    lcd_mode: bool = False                      # 子像素渲染 (水平)
    lcd_v_mode: bool = False                    # 子像素渲染 (垂直)
    no_kerning: bool = False                    # 禁用字距调整
    no_compress: bool = False                   # 禁用压缩 (废弃,用 compression)
    lvgl_version: int = 9                       # LVGL 版本 (7, 8, 9)
    
    def __post_init__(self):
        """参数验证"""
        if self.bpp not in [1, 2, 4, 8]:
            raise ValueError(f"Invalid bpp: {self.bpp}. Must be 1, 2, 4, or 8")
        
        if self.compression not in ["none", "rle"]:
            raise ValueError(f"Invalid compression: {self.compression}")
        
        if self.format not in ["lvgl", "bin", "dump"]:
            raise ValueError(f"Invalid format: {self.format}")
        
        if self.lvgl_version not in [7, 8, 9]:
            raise ValueError(f"Invalid LVGL version: {self.lvgl_version}")


class FontConverter:
    """
    字体转换器核心类
    
    负责协调整个字体转换流程：
    1. 加载字体
    2. 收集字符范围
    3. 渲染字形
    4. 构建数据结构
    5. 生成输出
    """
    
    def __init__(self):
        """初始化转换器"""
        self.font_sources: List[FontSource] = []
        self.params = ConversionParams()
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
        
        # 内部状态
        self._font_loader: Optional[FontLoader] = None
        self._glyph_renderer: Optional[GlyphRenderer] = None
        self._loaded_fonts: Dict[str, FontFace] = {}
    
    def add_font(self, font_path: str, ranges: Optional[List[str]] = None, 
                 symbols: str = "") -> None:
        """
        添加字体源
        
        Args:
            font_path: 字体文件路径
            ranges: 字符范围列表,如 ["0x30-0x39", "0x41-0x5A"]
            symbols: 单独的符号字符串,如 "©®™"
        """
        source = FontSource(
            path=font_path,
            ranges=ranges or [],
            symbols=symbols
        )
        self.font_sources.append(source)
    
    def set_params(self, **kwargs) -> None:
        """
        设置转换参数
        
        支持的参数:
            size: 字体大小
            bpp: 每像素位数
            compression: 压缩模式
            format: 输出格式
            lcd_mode, lcd_v_mode: 子像素渲染
            no_kerning: 禁用字距
            lvgl_version: LVGL 版本
        """
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
            else:
                raise ValueError(f"Unknown parameter: {key}")
        
        # 重新验证参数
        self.params.__post_init__()
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数 (message: str, current: int, total: int) -> None
        """
        self.progress_callback = callback
    
    def convert(self, output_path: str) -> None:
        """
        执行字体转换
        
        Args:
            output_path: 输出文件路径 (不含扩展名)
        
        Raises:
            ValueError: 参数错误
            RuntimeError: 转换失败
        """
        if not self.font_sources:
            raise ValueError("No fonts added. Use add_font() first.")
        
        try:
            # 1. 加载字体
            self._report_progress("Loading fonts", 0, 5)
            self._load_fonts()
            
            # 2. 收集字符
            self._report_progress("Collecting characters", 1, 5)
            char_map = self._collect_characters()
            
            # 3. 渲染字形
            self._report_progress("Rendering glyphs", 2, 5)
            glyphs = self._render_glyphs(char_map)
            
            # 4. 构建数据结构
            self._report_progress("Building font data", 3, 5)
            font_data = self._build_font_data(glyphs)
            
            # 5. 生成输出
            self._report_progress("Writing output", 4, 5)
            self._write_output(font_data, output_path)
            
            self._report_progress("Conversion complete", 5, 5)
            
        finally:
            # 清理资源
            self._cleanup()
    
    def _load_fonts(self) -> None:
        """加载所有字体文件"""
        self._font_loader = FontLoader()
        
        for source in self.font_sources:
            if source.path not in self._loaded_fonts:
                font_face = self._font_loader.load(source.path, self.params.size)
                self._loaded_fonts[source.path] = font_face
    
    def _collect_characters(self) -> Dict[int, str]:
        """
        收集所有需要渲染的字符
        
        Returns:
            字典: {unicode码点: 字体路径}
        """
        char_map = {}
        
        for source in self.font_sources:
            # 从范围添加
            for range_str in source.ranges:
                chars = self._parse_range(range_str)
                for char_code in chars:
                    if char_code not in char_map:
                        char_map[char_code] = source.path
            
            # 从符号字符串添加
            for char in source.symbols:
                char_code = ord(char)
                if char_code not in char_map:
                    char_map[char_code] = source.path
        
        if not char_map:
            raise ValueError("No characters to render. Specify ranges or symbols.")
        
        return char_map
    
    def _parse_range(self, range_str: str) -> List[int]:
        """
        解析字符范围字符串
        
        Args:
            range_str: 范围字符串,如 "0x30-0x39" 或 "48-57"
        
        Returns:
            字符码点列表
        """
        if '-' not in range_str:
            # 单个字符
            return [int(range_str, 0)]
        
        start_str, end_str = range_str.split('-', 1)
        start = int(start_str, 0)
        end = int(end_str, 0)
        
        if start > end:
            raise ValueError(f"Invalid range: {range_str} (start > end)")
        
        return list(range(start, end + 1))
    
    def _render_glyphs(self, char_map: Dict[int, str]) -> List[GlyphData]:
        """
        渲染所有字形
        
        Args:
            char_map: 字符到字体的映射
        
        Returns:
            渲染后的字形数据列表
        """
        # 创建渲染器
        render_options = RenderOptions(
            lcd=self.params.lcd_mode,
            lcd_v=self.params.lcd_v_mode,
            mono=(self.params.bpp == 1 and not self.params.lcd_mode and not self.params.lcd_v_mode)
        )
        self._glyph_renderer = GlyphRenderer(render_options)
        
        glyphs = []
        total = len(char_map)
        
        for idx, (char_code, font_path) in enumerate(sorted(char_map.items())):
            self._report_progress(f"Rendering glyph {idx + 1}/{total}", idx, total)
            
            font_face = self._loaded_fonts[font_path]
            metrics = self._glyph_renderer.render(font_face, char_code)
            
            if metrics is None:
                continue  # 字形不存在,跳过
            
            # 转换为 GlyphData
            glyph_data = GlyphData(
                glyph_id=len(glyphs),  # 临时 ID,后面会重新编号
                unicode=char_code,
                bitmap=metrics.pixels,
                bitmap_index=0,  # 后面在打包时设置
                advance_width=metrics.advance_x,
                box_w=metrics.width,
                box_h=metrics.height,
                ofs_x=metrics.bearing_x,
                ofs_y=metrics.bearing_y
            )
            
            glyphs.append(glyph_data)
        
        return glyphs
    
    def _build_font_data(self, glyphs: List[GlyphData]) -> LVGLFont:
        """
        构建 LVGL 字体数据结构
        
        Args:
            glyphs: 渲染后的字形列表
        
        Returns:
            完整的 LVGL 字体对象
        """
        if not glyphs:
            raise ValueError("No glyphs rendered")
        
        # 1. 构建字形表 (GLYF)
        glyf = self._build_glyf_table(glyphs)
        
        # 2. 构建字符映射表 (CMAP)
        cmaps = self._build_cmap_tables(glyphs)
        
        # 3. 构建字距表 (KERN) - 如果启用
        kern = None
        if not self.params.no_kerning:
            kern = self._build_kern_table(glyphs)
        
        # 4. 构建头部 (HEAD)
        head = self._build_head(glyf, cmaps, kern)
        
        # 5. 组装完整字体
        font = LVGLFont(
            head=head,
            cmaps=cmaps,
            glyf=glyf,
            kern=kern
        )
        
        # 验证
        font.validate()
        
        return font
    
    def _build_glyf_table(self, glyphs: List[GlyphData]) -> LVGLGlyf:
        """构建字形表"""
        # 打包所有位图
        all_bitmaps = []
        bitmap_index = 0
        
        for glyph in glyphs:
            glyph.bitmap_index = bitmap_index
            
            # 打包位图到字节
            if glyph.bitmap.size > 0:
                packed = self._pack_bitmap(glyph.bitmap)
                all_bitmaps.append(packed)
                bitmap_index += len(packed)
        
        # 合并所有位图数据
        bitmap_data = np.concatenate(all_bitmaps) if all_bitmaps else np.array([], dtype=np.uint8)
        
        # 压缩 (如果启用)
        compression = CompressionType.NONE
        if self.params.compression == "rle":
            bitmap_data = compress_bitmap(bitmap_data, self.params.bpp)
            compression = CompressionType.RLE
        
        return LVGLGlyf(
            glyphs=glyphs,
            bitmap_data=bitmap_data,
            compression=compression
        )
    
    def _pack_bitmap(self, pixels: np.ndarray) -> np.ndarray:
        """
        将像素数组打包为字节数组
        
        Args:
            pixels: 2D 像素数组
        
        Returns:
            打包后的字节数组
        """
        if pixels.size == 0:
            return np.array([], dtype=np.uint8)
        
        # 展平为 1D
        flat = pixels.flatten()
        
        # 打包到字节
        pixels_per_byte = 8 // self.params.bpp
        num_bytes = (len(flat) + pixels_per_byte - 1) // pixels_per_byte
        
        packed = np.zeros(num_bytes, dtype=np.uint8)
        
        for i, pixel in enumerate(flat):
            byte_idx = i // pixels_per_byte
            bit_offset = (i % pixels_per_byte) * self.params.bpp
            packed[byte_idx] |= (pixel << (8 - bit_offset - self.params.bpp))
        
        return packed
    
    def _build_cmap_tables(self, glyphs: List[GlyphData]) -> List[CmapSubtable]:
        """构建字符映射表"""
        if not glyphs:
            return []
        
        # 按 Unicode 排序
        sorted_glyphs = sorted(glyphs, key=lambda g: g.unicode)
        
        # 分组为连续范围
        cmaps = []
        range_start = sorted_glyphs[0].unicode
        range_glyphs = [sorted_glyphs[0]]
        
        for glyph in sorted_glyphs[1:]:
            if glyph.unicode == range_glyphs[-1].unicode + 1:
                # 连续
                range_glyphs.append(glyph)
            else:
                # 断开,创建新范围
                cmaps.append(self._create_cmap_subtable(range_start, range_glyphs))
                range_start = glyph.unicode
                range_glyphs = [glyph]
        
        # 最后一个范围
        if range_glyphs:
            cmaps.append(self._create_cmap_subtable(range_start, range_glyphs))
        
        return cmaps
    
    def _create_cmap_subtable(self, range_start: int, glyphs: List[GlyphData]) -> CmapSubtable:
        """创建单个 cmap 子表"""
        # 使用简单的 FORMAT0_FULL 格式
        return CmapSubtable(
            range_start=range_start,
            range_length=len(glyphs),
            glyph_id_start=glyphs[0].glyph_id,
            format=CmapFormat.FORMAT0_FULL,
            unicode_list=None,
            glyph_id_ofs_list=None
        )
    
    def _build_kern_table(self, glyphs: List[GlyphData]) -> Optional[LVGLKern]:
        """构建字距调整表 (简化版,不实现完整 kerning)"""
        # TODO: 实现完整的 kerning 支持
        # 需要从字体文件读取 kerning pairs
        return None
    
    def _build_head(self, glyf: LVGLGlyf, cmaps: List[CmapSubtable], 
                    kern: Optional[LVGLKern]) -> LVGLHead:
        """构建字体头"""
        # 计算字体度量
        if not glyf.glyphs:
            raise ValueError("No glyphs in font")
        
        # 找最大/最小 Y 坐标
        max_y = max((g.ofs_y + g.box_h) for g in glyf.glyphs if g.box_h > 0)
        min_y = min(g.ofs_y for g in glyf.glyphs if g.box_h > 0)
        
        # 典型的上升/下降值
        ascent = max(max_y, self.params.size * 3 // 4)
        descent = min(min_y, -self.params.size // 4)
        
        return LVGLHead(
            font_size=self.params.size,
            bpp=self.params.bpp,
            ascent=ascent,
            descent=descent,
            typo_ascent=ascent,
            typo_descent=descent,
            typo_line_gap=0,
            min_y=min_y,
            max_y=max_y,
            default_advance_width=self.params.size,
            kerning_scale=1.0,
            index_to_loc_format=0,
            glyph_id_format=0,
            advance_width_format=0,
            compression_id=glyf.compression.value,
            subpixel_mode=SubpixelMode.NONE
        )
    
    def _write_output(self, font: LVGLFont, output_path: str) -> None:
        """写入输出文件"""
        if self.params.format == "lvgl":
            # LVGL C 代码
            writer = LVGLWriter(font, lvgl_version=self.params.lvgl_version)
            output_file = Path(output_path).with_suffix('.c')
            writer.write(str(output_file))
            
        elif self.params.format == "bin":
            # 二进制格式 (TODO: 实现 BinWriter)
            raise NotImplementedError("Binary format not yet implemented")
            
        elif self.params.format == "dump":
            # JSON + PNG 调试格式 (TODO: 实现 DumpWriter)
            raise NotImplementedError("Dump format not yet implemented")
    
    def _report_progress(self, message: str, current: int, total: int) -> None:
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def _cleanup(self) -> None:
        """清理资源"""
        if self._font_loader:
            self._font_loader.cleanup()
        
        self._loaded_fonts.clear()
        self._font_loader = None
        self._glyph_renderer = None
