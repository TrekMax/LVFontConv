"""
LVGL 字体格式写入器

将 LVGLFont 数据结构转换为 LVGL C 源代码。
"""

from typing import Optional, List
from pathlib import Path
import numpy as np

from .structures import (
    LVGLFont,
    LVGLCmap,
    LVGLGlyf,
    LVGLKern,
    CmapFormat,
    CompressionType,
    SubpixelMode
)
from .compress import compress_rle, compress_rle_with_xor


class LVGLWriter:
    """
    LVGL 字体格式写入器
    
    负责将 LVGLFont 数据结构转换为 LVGL C 代码格式。
    生成的代码可以直接在 LVGL 项目中使用。
    """
    
    def __init__(
        self,
        lv_include: str = "lvgl.h",
        version_major: int = 9
    ):
        """
        初始化写入器
        
        Args:
            lv_include: LVGL 头文件包含路径
            version_major: LVGL 主版本号 (7, 8, 9)
        """
        self.lv_include = lv_include
        self.version_major = version_major
    
    def write(self, font: LVGLFont, output_path: str) -> None:
        """
        写入字体数据到 C 文件
        
        Args:
            font: LVGL 字体数据
            output_path: 输出文件路径 (.c)
        """
        # 验证字体数据
        errors = font.validate()
        if errors:
            raise ValueError(f"字体数据验证失败:\n" + "\n".join(f"  - {e}" for e in errors))
        
        # 生成 C 代码
        c_code = self.generate_c_code(font)
        
        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(c_code, encoding='utf-8')
    
    def generate_c_code(self, font: LVGLFont) -> str:
        """
        生成完整的 C 代码
        
        Args:
            font: LVGL 字体数据
            
        Returns:
            C 源代码字符串
        """
        guard_name = font.name.upper()
        
        # 生成各部分
        header = self._generate_header(font)
        glyf_section = self._generate_glyf_section(font)
        cmap_section = self._generate_cmap_section(font)
        kern_section = self._generate_kern_section(font)
        font_dsc = self._generate_font_descriptor(font)
        public_font = self._generate_public_font(font)
        
        # 组装完整代码
        code = f"""{header}

#ifndef {guard_name}
#define {guard_name} 1
#endif

#if {guard_name}

{glyf_section}

{cmap_section}

{kern_section}

{font_dsc}

{public_font}

#endif /*#if {guard_name}*/
"""
        return code
    
    def _generate_header(self, font: LVGLFont) -> str:
        """生成文件头部"""
        return f"""/*******************************************************************************
 * Size: {font.head.font_size} px
 * Bpp: {font.head.bpp}
 * Opts: --no-compress --no-prefilter --bpp {font.head.bpp} --size {font.head.font_size}
 ******************************************************************************/

#ifdef __has_include
    #if __has_include("lvgl.h")
        #ifndef LV_LVGL_H_INCLUDE_SIMPLE
            #define LV_LVGL_H_INCLUDE_SIMPLE
        #endif
    #endif
#endif

#ifdef LV_LVGL_H_INCLUDE_SIMPLE
    #include "lvgl.h"
#else
    #include "{self.lv_include}"
#endif"""
    
    def _generate_glyf_section(self, font: LVGLFont) -> str:
        """生成字形表 C 代码"""
        glyf = font.glyf
        
        # 生成位图数据
        bitmap_arrays = []
        for glyph in glyf.glyphs:
            if glyph.glyph_id == 0:
                continue  # 跳过保留字形
            
            code_hex = f"{glyph.unicode:04X}"
            char_str = chr(glyph.unicode) if 0x20 <= glyph.unicode < 0x7F else "?"
            
            # 压缩位图
            if font.head.compression_id == CompressionType.NONE:
                bitmap_data = self._flatten_bitmap(glyph.bitmap, font.head.bpp)
            elif font.head.compression_id == CompressionType.RLE:
                bitmap_data = compress_rle_with_xor(
                    glyph.bitmap,
                    bpp=font.head.bpp,
                    width=glyph.box_w,
                    height=glyph.box_h
                )
            else:  # RLE_NO_PREFILTER
                flat = glyph.bitmap.flatten()
                bitmap_data = compress_rle(flat, bpp=font.head.bpp)
            
            if len(bitmap_data) > 0:
                hex_data = self._format_hex_array(bitmap_data)
                comment = f"    /* U+{code_hex} \"{char_str}\" */\n"
                bitmap_arrays.append(comment + hex_data)
        
        bitmaps = ",\n\n".join(bitmap_arrays) if bitmap_arrays else ""
        
        # 生成字形描述符
        glyph_descs = ['    {.bitmap_index = 0, .adv_w = 0, .box_w = 0, .box_h = 0, .ofs_x = 0, .ofs_y = 0} /* id = 0 reserved */']
        
        for glyph in glyf.glyphs:
            if glyph.glyph_id == 0:
                continue
            
            adv_w = glyph.adv_w_fp
            desc = f"    {{.bitmap_index = {glyph.bitmap_index}, .adv_w = {adv_w}, .box_w = {glyph.box_w}, .box_h = {glyph.box_h}, .ofs_x = {glyph.ofs_x}, .ofs_y = {glyph.ofs_y}}}"
            glyph_descs.append(desc)
        
        return f"""/*-----------------
 *    BITMAPS
 *----------------*/

/*Store the image of the glyphs*/
static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {{
{bitmaps}
}};


/*---------------------
 *  GLYPH DESCRIPTION
 *--------------------*/

static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {{
{','.join(chr(10).join([glyph_descs[0]] + glyph_descs[1:]).split(chr(10)))}
}};"""
    
    def _generate_cmap_section(self, font: LVGLFont) -> str:
        """生成字符映射表 C 代码"""
        cmap = font.cmap
        
        subtable_defs = []
        subtable_headers = []
        
        for idx, subtable in enumerate(cmap.subtables):
            # 生成数据数组
            defs = []
            
            if subtable.format in (CmapFormat.SPARSE_TINY, CmapFormat.SPARSE_FULL):
                if subtable.unicode_list:
                    unicode_hex = [f"0x{u:x}" for u in subtable.unicode_list]
                    defs.append(f"static const uint16_t unicode_list_{idx}[] = {{\n    {', '.join(unicode_hex)}\n}};")
            
            if subtable.format in (CmapFormat.FORMAT0_FULL, CmapFormat.SPARSE_FULL):
                if subtable.glyph_id_ofs_list:
                    defs.append(f"static const uint16_t glyph_id_ofs_list_{idx}[] = {{\n    {', '.join(map(str, subtable.glyph_id_ofs_list))}\n}};")
            
            if defs:
                subtable_defs.append("\n".join(defs))
            
            # 生成头部
            format_enum = self._cmap_format_to_enum(subtable.format)
            u_list = f"unicode_list_{idx}" if subtable.unicode_list else "NULL"
            id_list = f"glyph_id_ofs_list_{idx}" if subtable.glyph_id_ofs_list else "NULL"
            
            header = f"""    {{
        .range_start = {subtable.range_start}, .range_length = {subtable.range_length}, .glyph_id_start = {subtable.glyph_id_start},
        .unicode_list = {u_list}, .glyph_id_ofs_list = {id_list}, .list_length = {subtable.entries_count}, .type = {format_enum}
    }}"""
            subtable_headers.append(header)
        
        defs_str = "\n\n".join(subtable_defs) if subtable_defs else ""
        
        return f"""/*---------------------
 *  CHARACTER MAPPING
 *--------------------*/

{defs_str}

/*Collect the unicode lists and glyph_id offsets*/
static const lv_font_fmt_txt_cmap_t cmaps[] =
{{
{',\n'.join(subtable_headers)}
}};"""
    
    def _generate_kern_section(self, font: LVGLFont) -> str:
        """生成字距调整表 C 代码"""
        if not font.has_kerning:
            return ""
        
        kern = font.kern
        
        if kern.use_classes:
            # Format 3: 基于类
            left_mapping = ', '.join(map(str, kern.left_mapping))
            right_mapping = ', '.join(map(str, kern.right_mapping))
            
            # 转换为 FP4.4
            scale = font.head.kerning_scale
            values = [self._kern_to_fp(v, scale) for v in kern.class_values]
            values_str = ', '.join(map(str, values))
            
            return f"""/*-----------------
 *    KERNING
 *----------------*/

/*Map glyph_ids to kern left classes*/
static const uint8_t kern_left_class_mapping[] =
{{
    {left_mapping}
}};

/*Map glyph_ids to kern right classes*/
static const uint8_t kern_right_class_mapping[] =
{{
    {right_mapping}
}};

/*Kern values between classes*/
static const int8_t kern_class_values[] =
{{
    {values_str}
}};

/*Collect the kern class' data in one place*/
static const lv_font_fmt_txt_kern_classes_t kern_classes =
{{
    .class_pair_values   = kern_class_values,
    .left_class_mapping  = kern_left_class_mapping,
    .right_class_mapping = kern_right_class_mapping,
    .left_class_cnt      = {kern.left_classes},
    .right_class_cnt     = {kern.right_classes},
}};"""
        else:
            # Format 0: 字形对
            gid_size = "uint16_t" if font.head.glyph_id_format else "uint8_t"
            scale = font.head.kerning_scale
            
            pairs_gids = []
            pairs_values = []
            
            for pair in kern.pairs:
                pairs_gids.append(f"    {pair.left_glyph_id}, {pair.right_glyph_id}")
                pairs_values.append(str(pair.to_fp(scale)))
            
            return f"""/*-----------------
 *    KERNING
 *----------------*/

/*Pair left and right glyphs for kerning*/
static const {gid_size} kern_pair_glyph_ids[] =
{{
{',\n'.join(pairs_gids)}
}};

/* Kerning between the respective left and right glyphs
 * 4.4 format which needs to scaled with `kern_scale`*/
static const int8_t kern_pair_values[] =
{{
    {', '.join(pairs_values)}
}};

/*Collect the kern pair's data in one place*/
static const lv_font_fmt_txt_kern_pair_t kern_pairs =
{{
    .glyph_ids = kern_pair_glyph_ids,
    .values = kern_pair_values,
    .pair_cnt = {len(kern.pairs)},
    .glyph_ids_size = {font.head.glyph_id_format}
}};"""
    
    def _generate_font_descriptor(self, font: LVGLFont) -> str:
        """生成字体描述符"""
        kern_dsc = "NULL"
        kern_scale = "0"
        kern_classes = "0"
        
        if font.has_kerning:
            if font.kern.use_classes:
                kern_dsc = "&kern_classes"
                kern_classes = "1"
            else:
                kern_dsc = "&kern_pairs"
            kern_scale = str(font.head.kerning_scale_fp)
        
        compression_code = int(font.head.compression_id)
        
        fallback_decl = ""
        if font.fallback:
            fallback_decl = f"extern const lv_font_t {font.fallback};\n"
        
        return f"""{fallback_decl}/*--------------------
 *  ALL CUSTOM DATA
 *--------------------*/

#if LVGL_VERSION_MAJOR == 8
/*Store all the custom data of the font*/
static  lv_font_fmt_txt_glyph_cache_t cache;
#endif

#if LVGL_VERSION_MAJOR >= 8
static const lv_font_fmt_txt_dsc_t font_dsc = {{
#else
static lv_font_fmt_txt_dsc_t font_dsc = {{
#endif
    .glyph_bitmap = glyph_bitmap,
    .glyph_dsc = glyph_dsc,
    .cmaps = cmaps,
    .kern_dsc = {kern_dsc},
    .kern_scale = {kern_scale},
    .cmap_num = {len(font.cmap.subtables)},
    .bpp = {font.head.bpp},
    .kern_classes = {kern_classes},
    .bitmap_format = {compression_code},
#if LVGL_VERSION_MAJOR == 8
    .cache = &cache
#endif
}};"""
    
    def _generate_public_font(self, font: LVGLFont) -> str:
        """生成公共字体声明"""
        subpx_enum = {
            SubpixelMode.NONE: "LV_FONT_SUBPX_NONE",
            SubpixelMode.HORIZONTAL: "LV_FONT_SUBPX_HOR",
            SubpixelMode.VERTICAL: "LV_FONT_SUBPX_VER"
        }[font.head.subpixel_mode]
        
        fallback = f"&{font.fallback}" if font.fallback else "NULL"
        
        return f"""/*-----------------
 *  PUBLIC FONT
 *----------------*/

/*Initialize a public general font descriptor*/
#if LVGL_VERSION_MAJOR >= 8
const lv_font_t {font.name} = {{
#else
lv_font_t {font.name} = {{
#endif
    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,    /*Function pointer to get glyph's data*/
    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,    /*Function pointer to get glyph's bitmap*/
    .line_height = {font.head.line_height},          /*The maximum line height required by the font*/
    .base_line = {font.head.base_line},             /*Baseline measured from the bottom of the line*/
#if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
    .subpx = {subpx_enum},
#endif
#if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
    .underline_position = {font.head.underline_position},
    .underline_thickness = {font.head.underline_thickness},
#endif
    .dsc = &font_dsc,          /*The custom font data. Will be accessed by `get_glyph_bitmap/dsc` */
#if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
    .fallback = {fallback},
#endif
    .user_data = NULL,
}};"""
    
    def _flatten_bitmap(self, bitmap: np.ndarray, bpp: int) -> bytes:
        """
        将位图扁平化为字节数组（无压缩）
        
        根据 BPP 打包像素:
        - 1 bpp: 8 像素/字节
        - 2 bpp: 4 像素/字节
        - 4 bpp: 2 像素/字节
        - 8 bpp: 1 像素/字节
        """
        flat = bitmap.flatten()
        
        if bpp == 8:
            # 8-bit: 1 像素/字节,直接返回
            return flat.tobytes()
        elif bpp == 4:
            # 4-bit: 2 像素/字节
            # 注意: 原版使用 BitStream 大端序(MSB first),所以第一个像素在高nibble
            packed = []
            for i in range(0, len(flat), 2):
                high = (flat[i] & 0x0F) << 4  # 高4位(第一个像素)
                low = flat[i+1] & 0x0F if i+1 < len(flat) else 0  # 低4位(第二个像素)
                packed.append(high | low)
            return bytes(packed)
        elif bpp == 2:
            # 2-bit: 4 像素/字节
            packed = []
            for i in range(0, len(flat), 4):
                byte = 0
                for j in range(4):
                    if i+j < len(flat):
                        byte |= (flat[i+j] & 0x03) << (6 - j*2)
                packed.append(byte)
            return bytes(packed)
        elif bpp == 1:
            # 1-bit: 8 像素/字节
            packed = []
            for i in range(0, len(flat), 8):
                byte = 0
                for j in range(8):
                    if i+j < len(flat):
                        byte |= (flat[i+j] & 0x01) << (7 - j)
                packed.append(byte)
            return bytes(packed)
        else:
            raise ValueError(f"不支持的 BPP: {bpp}")
    
    def _format_hex_array(self, data: bytes, cols: int = 12) -> str:
        """格式化字节数组为十六进制 C 数组"""
        hex_values = [f"0x{b:02x}" for b in data]
        lines = []
        
        for i in range(0, len(hex_values), cols):
            line = ", ".join(hex_values[i:i+cols])
            lines.append(f"    {line}")
        
        return ",\n".join(lines)
    
    def _cmap_format_to_enum(self, fmt: CmapFormat) -> str:
        """转换 CmapFormat 到 C 枚举"""
        mapping = {
            CmapFormat.FORMAT0_TINY: "LV_FONT_FMT_TXT_CMAP_FORMAT0_TINY",
            CmapFormat.FORMAT0_FULL: "LV_FONT_FMT_TXT_CMAP_FORMAT0_FULL",
            CmapFormat.SPARSE_TINY: "LV_FONT_FMT_TXT_CMAP_SPARSE_TINY",
            CmapFormat.SPARSE_FULL: "LV_FONT_FMT_TXT_CMAP_SPARSE_FULL"
        }
        return mapping[fmt]
    
    def _kern_to_fp(self, value: int, scale: float) -> int:
        """将字距值转换为 FP4.4 格式"""
        return round(value / scale)
