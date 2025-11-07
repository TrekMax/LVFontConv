"""
Simple Font Converter - 简化的字体转换接口

直接使用 Phase 1 和 Phase 2 的现有 API,不引入复杂抽象。
"""

from pathlib import Path
from typing import List, Optional, Callable, Set, Dict
import re

from core.font_loader import FontLoader
from core.glyph_renderer import GlyphRenderer
from writers.lvgl.structures import FontData, GlyphData, CmapEntry, CompressionType, SubpixelMode
from writers.lvgl.compress import compress_bitmap
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
            
            renderer = GlyphRenderer()
            renderer.set_font_face(font_path, font_loader._font)  # 传递 FreeType Face
            renderer.set_size(size)
            
            # BPP 映射: 实际位深度 -> GlyphRenderer 的 bpp 参数
            # 1bit->1, 2bit->2, 4bit->3, 8bit->4
            bpp_map = {1: 1, 2: 2, 4: 3, 8: 4}
            renderer_bpp = bpp_map.get(bpp, 3)
            renderer.set_bpp(renderer_bpp)
            
            logger.info(f"渲染器配置: size={size}px, bpp={bpp}bit (renderer_bpp={renderer_bpp})")
            
            # 4. 渲染所有字形
            self._report_progress("渲染字形", 30)
            glyphs: Dict[int, GlyphData] = {}
            cmap_entries: List[CmapEntry] = []
            
            total_chars = len(codepoints)
            for i, codepoint in enumerate(sorted(codepoints)):
                # 渲染字形
                glyph_data = renderer.render_glyph(
                    font_path=font_path,
                    char_code=codepoint,
                    mapped_code=codepoint
                )
                
                if glyph_data:
                    glyphs[codepoint] = glyph_data
                    cmap_entries.append(CmapEntry(
                        unicode=codepoint,
                        glyph_index=len(glyphs) - 1  # 简单的索引分配
                    ))
                else:
                    logger.warning(f"字符 U+{codepoint:04X} 渲染失败,跳过")
                
                # 更新进度
                if i % 10 == 0 or i == total_chars - 1:
                    progress = 30 + int((i / total_chars) * 40)
                    self._report_progress(
                        f"渲染字形 {i+1}/{total_chars}",
                        progress
                    )
            
            if not glyphs:
                logger.error("没有成功渲染任何字形")
                return False
            
            logger.info(f"成功渲染 {len(glyphs)} 个字形")
            
            # 5. 字距调整 (暂时跳过,Phase 1 API 不完整)
            self._report_progress("字距调整", 70)
            kern_pairs = []  # TODO: 实现字距调整
            
            # 6. 应用压缩
            self._report_progress("压缩字形数据", 75)
            compression_type = CompressionType.RLE if compression == "rle" else CompressionType.NONE
            
            if compression_type == CompressionType.RLE:
                for glyph_data in glyphs.values():
                    if glyph_data.bitmap:
                        compressed = compress_bitmap(glyph_data.bitmap, bpp)
                        glyph_data.bitmap = compressed
                logger.info("字形数据已压缩")
            
            # 7. 确定子像素模式
            if lcd_mode:
                subpixel_mode = SubpixelMode.LCD
            elif lcd_v_mode:
                subpixel_mode = SubpixelMode.LCD_V
            else:
                subpixel_mode = SubpixelMode.NONE
            
            # 8. 构建 FontData
            self._report_progress("构建字体数据结构", 85)
            
            # 计算基准线和行高
            baseline = font_info.ascent * size // font_info.units_per_em
            line_height = (font_info.ascent - font_info.descent) * size // font_info.units_per_em
            
            font_data = FontData(
                base_line=baseline,
                line_height=line_height,
                bpp=bpp,
                compression=compression_type,
                subpixel_mode=subpixel_mode,
                glyphs=glyphs,
                cmap=cmap_entries,
                kerning=kern_pairs
            )
            
            # 9. 写入文件
            self._report_progress("写入输出文件", 90)
            writer = LVGLWriter(lvgl_version=lvgl_version)
            
            output_file = f"{output_path}.c"
            font_name = Path(font_path).stem
            writer.write(font_data, output_file, font_name)
            
            logger.info(f"字体转换成功: {output_file}")
            self._report_progress("转换完成", 100)
            
            return True
            
        except Exception as e:
            logger.error(f"字体转换失败: {e}", exc_info=True)
            return False
        
        finally:
            # 清理资源
            if font_loader:
                try:
                    font_loader.close()
                except:
                    pass
