"""
Simple Font Converter - 简化的字体转换接口

直接使用 Phase 1 和 Phase 2 的现有 API,构建完整的 LVGLFont 结构。
"""

from pathlib import Path
from typing import List, Optional, Callable, Set, Dict
import re
import numpy as np

from core.font_loader import FontLoader
from core.glyph_renderer import GlyphRenderer
from writers.lvgl.structures import (
    LVGLFont, LVGLHead, LVGLCmap, LVGLGlyf, LVGLKern,
    CmapSubtable, GlyphData, KernPair,
    CompressionType, SubpixelMode, CmapFormat
)
from writers.lvgl.writer import LVGLWriter
from utils.logger import get_logger

logger = get_logger()


def parse_range(range_str: str) -> List[int]:
    """
    解析字符范围字符串
    
    支持格式:
    - "0x30-0x39" (十六进制范围)
    - "48-57" (十进制范围)
    - "0x41" (单个十六进制字符)
    - "65" (单个十进制字符)
    
    Args:
        range_str: 范围字符串
        
    Returns:
        字符码点列表
    """
    range_str = range_str.strip()
    
    # 匹配范围: 0x30-0x39 或 48-57
    match = re.match(r'(0x[0-9a-fA-F]+|[0-9]+)\s*-\s*(0x[0-9a-fA-F]+|[0-9]+)', range_str)
    if match:
        start_str, end_str = match.groups()
        start = int(start_str, 16 if start_str.startswith('0x') else 10)
        end = int(end_str, 16 if end_str.startswith('0x') else 10)
        return list(range(start, end + 1))
    
    # 单个字符: 0x41 或 65
    match = re.match(r'(0x[0-9a-fA-F]+|[0-9]+)$', range_str)
    if match:
        char_str = match.group(1)
        char_code = int(char_str, 16 if char_str.startswith('0x') else 10)
        return [char_code]
    
    logger.warning(f"无法解析范围字符串: {range_str}")
    return []


def collect_codepoints(ranges: List[str], symbols: str) -> Set[int]:
    """
    收集所有需要转换的字符码点
    
    Args:
        ranges: 范围字符串列表 ["0x30-0x39", "0x41-0x5A"]
        symbols: 符号字符串 "©®™"
        
    Returns:
        字符码点集合
    """
    codepoints = set()
    
    # 解析范围
    for range_str in ranges:
        codepoints.update(parse_range(range_str))
    
    # 添加单独符号
    for char in symbols:
        codepoints.add(ord(char))
    
    return codepoints


class SimpleFontConverter:
    """
    简化的字体转换器
    
    直接使用 Phase 1 和 Phase 2 的现有功能。
    """
    
    def __init__(self):
        """初始化转换器"""
        self.progress_callback: Optional[Callable[[str, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """设置进度回调 (message, percentage)"""
        self.progress_callback = callback
    
    def _report_progress(self, message: str, percentage: int):
        """报告进度"""
        logger.info(f"[{percentage}%] {message}")
        if self.progress_callback:
            self.progress_callback(message, percentage)
    
    def convert_font(
        self,
        font_path: str,
        ranges: List[str],
        symbols: str,
        size: int,
        bpp: int,
        output_path: str,
        compression: str = "rle",
        lvgl_version: int = 8,
        no_kerning: bool = False,
        lcd_mode: bool = False,
        lcd_v_mode: bool = False
    ) -> bool:
        """
        转换单个字体文件
        
        Args:
            font_path: 字体文件路径
            ranges: 字符范围列表 ["0x30-0x39"]
            symbols: 符号字符串 "©®™"
            size: 字体大小 (像素)
            bpp: 每像素位数 (1/2/4/8)
            output_path: 输出文件路径 (不含扩展名)
            compression: 压缩方式 "rle"/"none"
            lvgl_version: LVGL 版本 7/8/9
            no_kerning: 禁用字距调整
            lcd_mode: LCD 水平模式
            lcd_v_mode: LCD 垂直模式
            
        Returns:
            是否成功
        """
        font_loader = None
        
        try:
            self._report_progress(f"加载字体: {Path(font_path).name}", 10)
            
            # 1. 加载字体
            font_loader = FontLoader()
            font_info = font_loader.load_font(font_path)
            logger.info(f"字体加载成功: {font_info.family_name}")
            
            # 2. 收集字符码点
            self._report_progress("解析字符范围", 20)
            codepoints = collect_codepoints(ranges, symbols)
            
            if not codepoints:
                logger.error("没有有效的字符码点")
                return False
            
            logger.info(f"总共 {len(codepoints)} 个字符需要转换")
            
            # 3. 创建字形渲染器
            self._report_progress("初始化渲染器", 25)
            
            # 从 FontLoader 获取 FreeType Face
            if font_path not in font_loader._freetype_faces:
                raise ValueError(f"字体未正确加载: {font_path}")
            
            face = font_loader._freetype_faces[font_path]
            
            renderer = GlyphRenderer()
            renderer.set_font_face(font_path, face)  # 传递 FreeType Face
            renderer.set_size(size)
            
            # BPP 映射: 实际位深度 -> GlyphRenderer 的 bpp 参数
            # GlyphRenderer.bpp 是输出的位深度 (1, 2, 3, 4 对应 1-bit, 2-bit, 3-bit, 4-bit)
            # 注意: 原来的映射有误! 4-bit 应该用 bpp=4,而不是 3
            renderer.set_bpp(bpp)
            
            logger.info(f"渲染器配置: size={size}px, bpp={bpp}bit")
            
            # 4. 渲染所有字形
            self._report_progress("渲染字形", 30)
            
            # 创建 Glyf 容器
            compression_type = CompressionType.RLE if compression == "rle" else CompressionType.NONE
            glyf = LVGLGlyf(bpp=bpp, compression=compression_type)
            
            # 添加保留字形 (ID 0)
            reserved_glyph = GlyphData(
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
            glyf.add_glyph(reserved_glyph)
            
            # 渲染所有字符
            glyph_id = 1  # 从 1 开始 (0 是保留)
            bitmap_offset = 0
            
            # 用于构建 Cmap
            char_to_glyph_id = {}
            
            # 用于计算字体度量 (与原版 lv_font_conv 兼容)
            bbox_tops = []  # offset_y (bitmap_top)
            bbox_bottoms = []  # offset_y - height
            
            total_chars = len(codepoints)
            for i, codepoint in enumerate(sorted(codepoints)):
                # 渲染字形 (使用 Phase 1 的 GlyphRenderer)
                rendered_glyph = renderer.render_glyph(
                    font_path=font_path,
                    char_code=codepoint,
                    mapped_code=codepoint
                )
                
                if not rendered_glyph:
                    logger.warning(f"字符 U+{codepoint:04X} 渲染失败,跳过")
                    continue
                
                # 转换为 Phase 2 的 GlyphData 结构
                # 注意: ofs_y 需要是 bbox.y, 而不是 bitmap_top
                # 原版: bbox.y = ft_result.y - ft_result.height
                #       ofs_y = bbox.y
                # 我们的 offset_y 是 bitmap_top (对应 ft_result.y)
                ofs_y_value = rendered_glyph.offset_y - rendered_glyph.height
                
                lvgl_glyph = GlyphData(
                    glyph_id=glyph_id,
                    unicode=codepoint,
                    bitmap=rendered_glyph.bitmap,
                    bitmap_index=bitmap_offset,
                    advance_width=float(rendered_glyph.advance_width),
                    box_w=rendered_glyph.width,
                    box_h=rendered_glyph.height,
                    ofs_x=rendered_glyph.offset_x,
                    ofs_y=ofs_y_value
                )
                
                glyf.add_glyph(lvgl_glyph)
                char_to_glyph_id[codepoint] = glyph_id
                
                # 收集 bbox 用于度量计算 (与原版 lv_font_conv 相同的算法)
                # 原版: bbox.y = ft_result.y - ft_result.height
                #       ascent = max(bbox.y + bbox.height) = max(ft_result.y)
                #       descent = min(bbox.y) = min(ft_result.y - height)
                if rendered_glyph.height > 0:
                    bbox_tops.append(rendered_glyph.offset_y)
                    bbox_bottoms.append(rendered_glyph.offset_y - rendered_glyph.height)
                
                # 更新位图偏移
                bitmap_size = rendered_glyph.width * rendered_glyph.height
                if bpp == 1:
                    bitmap_offset += (bitmap_size + 7) // 8
                elif bpp == 2:
                    bitmap_offset += (bitmap_size + 3) // 4
                elif bpp == 4:
                    bitmap_offset += (bitmap_size + 1) // 2
                else:  # bpp == 8
                    bitmap_offset += bitmap_size
                
                glyph_id += 1
                
                # 更新进度
                if i % 10 == 0 or i == total_chars - 1:
                    progress = 30 + int((i / total_chars) * 40)
                    self._report_progress(
                        f"渲染字形 {i+1}/{total_chars}",
                        progress
                    )
            
            if len(glyf.glyphs) <= 1:  # 只有保留字形
                logger.error("没有成功渲染任何字形")
                return False
            
            logger.info(f"成功渲染 {len(glyf.glyphs) - 1} 个字形")
            
            # 5. 构建 Cmap
            self._report_progress("构建字符映射表", 75)
            cmap = LVGLCmap()
            
            # 简化: 为每个字符范围创建一个子表
            sorted_chars = sorted(char_to_glyph_id.keys())
            if sorted_chars:
                # 创建连续范围
                range_start = sorted_chars[0]
                range_chars = [range_start]
                
                for char in sorted_chars[1:]:
                    if char == range_chars[-1] + 1:
                        # 连续字符
                        range_chars.append(char)
                    else:
                        # 创建子表
                        subtable = CmapSubtable(
                            range_start=range_start,
                            range_length=len(range_chars),
                            glyph_id_start=char_to_glyph_id[range_start],
                            format=CmapFormat.FORMAT0_TINY
                        )
                        cmap.add_subtable(subtable)
                        
                        # 开始新范围
                        range_start = char
                        range_chars = [char]
                
                # 添加最后一个范围
                subtable = CmapSubtable(
                    range_start=range_start,
                    range_length=len(range_chars),
                    glyph_id_start=char_to_glyph_id[range_start],
                    format=CmapFormat.FORMAT0_TINY
                )
                cmap.add_subtable(subtable)
            
            # 6. 字距调整 (暂时跳过)
            self._report_progress("字距调整", 80)
            kern = LVGLKern()  # 空的字距表
            
            # 7. 构建 Head
            self._report_progress("构建字体头", 85)
            
            # 计算度量 (与原版 lv_font_conv 完全相同的算法)
            # 原版代码: collect_font_data.js line 163-164
            #   ascent:  Math.max(...glyphs.map(g => g.bbox.y + g.bbox.height)),
            #   descent: Math.min(...glyphs.map(g => g.bbox.y)),
            # 其中 bbox.y = ft_result.y - ft_result.height
            # 所以 ascent = max(ft_result.y), descent = min(ft_result.y - height)
            if bbox_tops:
                ascent = max(bbox_tops)
                descent = min(bbox_bottoms)
            else:
                # 如果没有字形,使用默认值
                ascent = size
                descent = 0
            
            line_height = ascent - descent
            
            logger.info(f"字体度量: ascent={ascent}, descent={descent}, line_height={line_height}")
            
            head = LVGLHead(
                font_size=size,
                ascent=ascent,
                descent=descent,
                typo_ascent=ascent,
                typo_descent=descent,
                typo_line_gap=0,
                min_y=descent,
                max_y=ascent,
                default_advance_width=size // 2,  # 估算
                kerning_scale=0.25,
                index_to_loc_format=0,
                glyph_id_format=0,
                advance_width_format=0,
                bpp=bpp,
                bbox_x_bits=4,
                bbox_y_bits=4,
                bbox_w_bits=4,
                bbox_h_bits=4,
                advance_width_bits=8,
                compression_id=compression_type,
                subpixel_mode=SubpixelMode.NONE,  # 暂不支持子像素
                underline_position=-1,
                underline_thickness=1
            )
            
            # 8. 构建 LVGLFont
            self._report_progress("组装字体结构", 90)
            
            font_name = Path(font_path).stem
            lvgl_font = LVGLFont(
                name=font_name,
                head=head,
                cmap=cmap,
                glyf=glyf,
                kern=kern
            )
            
            # 9. 写入文件
            self._report_progress("写入输出文件", 95)
            writer = LVGLWriter()
            
            output_file = f"{output_path}.c"
            writer.write(lvgl_font, output_file)
            
            logger.info(f"字体转换成功: {output_file}")
            self._report_progress("转换完成", 100)
            
            return True
            
        except Exception as e:
            logger.error(f"字体转换失败: {e}")
            import traceback
            traceback.print_exc()
            return False
