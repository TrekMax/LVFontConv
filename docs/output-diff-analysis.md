# LVFontConv 与原版 lv_font_conv 输出差异分析

## 问题描述

LVFontConv 转换的字体与原版 lv_font_conv 输出不完全一致。

## 测试配置

- 字体: SourceHanSansCN-Regular.otf
- 范围: 0x30-0x39 (数字 0-9)
- 大小: 16px
- BPP: 4
- 压缩: 无 (--no-compress)

## 已发现的差异

###  1. ✅ 位图打包逻辑 (已修复)
**问题**: 之前没有实现位打包,直接返回原始字节  
**修复**: 实现了 1/2/4/8-bit 的正确打包逻辑  
**状态**: 基本修复,但位序仍需调整

### 2. ⚠️ 位图数据差异 (部分修复)
**现状**: 
- 原版: `[0, 76, 251, 32, 0, 63, 147, 174...]`
- 新版: `[0, 98, 87, 1, 0, 114, 36, 117...]`

**分析**:  
- 数值接近但不完全一致
- 可能的原因:
  1. 4-bit 打包的高低位顺序
  2. 像素值的量化方式不同
  3. FreeType 渲染参数差异

### 3. ❌ ofs_y 偏移错误
**问题**:
- 原版: `ofs_y = 0`
- 新版: `ofs_y = 12`

**分析**:
LVGL 的 `ofs_y` 是相对于 baseline 的偏移。原版值为 0 说明:
- 字形的顶部与 baseline 对齐,或
- 使用了不同的坐标系

需要检查:
1. GlyphRenderer 返回的 `offset_y` 含义
2. LVGL 期望的坐标系定义

### 4. ❌ baseline 计算错误
**问题**:
- 原版: `base_line = 0`
- 新版: `base_line = -5`

**关联**: 与 `ofs_y` 和 `line_height` 错误相关

### 5. ❌ line_height 差异
**问题**:
- 原版: `line_height = 12`
- 新版: `line_height = 13`

**计算公式** (simple_converter.py:312):
```python
baseline = font_info.ascent * size // font_info.units_per_em
line_height = (font_info.ascent - font_info.descent) * size // font_info.units_per_em
```

可能需要参考原版的计算方式。

### 6. ✅ 其他指标正确
- `bpp`: 4 ✓
- `glyph_dsc_count`: 11 ✓  
- `adv_w`: 142 vs 144 (接近)
- `box_w`, `box_h`: 基本相同

## 下一步行动

### 优先级 P0 - 严重影响显示

1. **修复 ofs_y 偏移**
   - 研究 LVGL 的坐标系定义
   - 检查 FreeType bearing_y 到 LVGL ofs_y 的转换
   - 参考: lv_font_conv/lib/font/table_glyf.js

2. **修复 baseline 和 line_height**
   - 对比原版计算公式
   - 参考: lv_font_conv/lib/font/font.js

### 优先级 P1 - 影响准确性

3. **调试位图打包顺序**
   - 生成 dump 格式输出对比像素值
   - 确认 4-bit 高低位顺序
   - 测试不同 BPP (1/2/8) 是否正确

## 测试方法

```bash
# 1. 生成测试文件
cd LVFontConv
python test_comparison.py

# 2. 生成原版文件
cd ..
lv_font_conv --font fonts/SourceHanSansCN/SourceHanSansCN-Regular.otf \
  --size 16 --bpp 4 --format lvgl --range 0x30-0x39 \
  --no-compress -o test_original.c

# 3. 对比
cd LVFontConv
python compare_output.py ../test_original.c ../test_lvfontconv.c
```

## 参考资料

- [lv_font_conv GitHub](https://github.com/lvgl/lv_font_conv)
- [LVGL 字体格式文档](https://docs.lvgl.io/master/details/main-components/font.html)
- lv_font_conv/lib/font/table_glyf.js - 字形位图处理
- lv_font_conv/lib/font/font.js - 字体度量计算

## 更新记录

- 2025-11-10: 初始分析,修复位图打包基础逻辑
