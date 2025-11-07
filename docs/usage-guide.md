# LVFontConv 使用指南

## 当前版本: 0.1.0 (Phase 1)

**状态**: ✅ Phase 1 完成 | 🚧 Phase 2-4 开发中

---

## 📦 安装

### 1. 克隆或下载项目

```bash
cd /home/listenai/Desktop/EPD/LVGL_Font/LVFontConv
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖包**:
- PyQt6 >= 6.4.0
- fontTools >= 4.38.0
- freetype-py >= 2.3.0
- Pillow >= 9.3.0
- numpy >= 1.24.0
- pytest >= 7.2.0 (开发依赖)

---

## 🚀 快速开始

### 方法 1: 运行演示工具（推荐）

这是最简单的方式来体验当前功能：

```bash
python demo.py
```

使用自定义字体：
```bash
python demo.py /path/to/your/font.ttf
```

**演示内容**:
- ✅ 字体信息获取
- ✅ 字符支持检测
- ✅ 字形渲染（多种尺寸和位深度）
- ✅ 字距调整信息
- ✅ 文本尺寸测量
- ✅ Unicode 范围解析

---

### 方法 2: 运行主程序

```bash
python src/main.py
```

> **注意**: GUI 界面尚未实现，当前仅显示版本信息。GUI 将在 Phase 3 开发。

---

### 方法 3: 运行测试套件

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_font_loader.py -v
python -m pytest tests/test_glyph_renderer.py -v

# 显示测试覆盖率
python -m pytest tests/ --cov=src --cov-report=html
```

**测试统计**:
- ✅ 30 个测试
- ✅ 100% 通过率
- ✅ 覆盖核心功能

---

## 📖 模块使用示例

### 1. 字体加载器 (FontLoader)

```python
import sys
sys.path.insert(0, 'src')

from core.font_loader import FontLoader

# 创建加载器
loader = FontLoader()

# 加载字体
info = loader.load_font("/path/to/font.ttf")

# 获取字体信息
print(f"字体家族: {info.family_name}")
print(f"样式: {info.style_name}")
print(f"字形数: {info.glyph_count}")
print(f"字符数: {len(info.supported_chars)}")
print(f"字距调整: {info.has_kerning}")

# 检查字符是否存在
has_char = loader.char_exists("/path/to/font.ttf", 0x41)  # 'A'
print(f"包含 'A': {has_char}")

# 卸载字体
loader.unload_font("/path/to/font.ttf")
```

**支持的格式**:
- ✅ TTF (TrueType Font)
- ✅ OTF (OpenType Font)
- ✅ WOFF (Web Open Font Format)
- ✅ WOFF2 (Web Open Font Format 2)

---

### 2. 字形渲染器 (GlyphRenderer)

```python
import sys
sys.path.insert(0, 'src')

from core.glyph_renderer import GlyphRenderer
import freetype

# 创建渲染器
renderer = GlyphRenderer()

# 加载字体
face = freetype.Face("/path/to/font.ttf")
renderer.set_font_face("my_font", face)

# 设置参数
renderer.set_size(24)  # 24 像素
renderer.set_bpp(4)    # 4-bit (16 级灰度)

# 渲染字形
glyph = renderer.render_glyph("my_font", 0x41)  # 'A'

if glyph:
    print(f"尺寸: {glyph.width}x{glyph.height}")
    print(f"偏移: ({glyph.offset_x}, {glyph.offset_y})")
    print(f"前进宽度: {glyph.advance_width}")
    print(f"位图形状: {glyph.bitmap.shape}")
    print(f"值范围: {glyph.bitmap.min()}-{glyph.bitmap.max()}")

# 获取字距调整
kern_x, kern_y = renderer.get_kerning("my_font", 0x41, 0x56)  # 'AV'
print(f"AV 字距: ({kern_x}, {kern_y})")

# 测量文本
width, height = renderer.measure_text("my_font", "Hello World")
print(f"文本尺寸: {width}x{height}")
```

**支持的功能**:
- ✅ 字体大小: 8-200 像素
- ✅ 位深度: 1, 2, 3, 4 bit
- ✅ 字距调整 (Kerning)
- ✅ 文本测量
- ✅ 自动微调 (Autohinting)

---

### 3. Unicode 范围解析器 (RangeParser)

```python
import sys
sys.path.insert(0, 'src')

from core.range_parser import RangeParser, get_preset_ranges

parser = RangeParser()

# 解析单个字符
ranges = parser.parse_range("0x41")
print(ranges)  # [(65, 65, 65)]

# 解析字符范围
ranges = parser.parse_range("0x41-0x5A")  # A-Z
print(ranges)  # [(65, 90, 65)]

# 解析带映射的范围
ranges = parser.parse_range("0x41-0x5A=>0x100")
print(ranges)  # [(65, 90, 256)]

# 解析多个范围
ranges = parser.parse_range("0x20-0x7F,0x410-0x44F")
char_set = parser.get_character_set(ranges)
print(f"字符数: {len(char_set)}")

# 解析符号列表
ranges = parser.parse_symbols("ABC123!@#")
print(f"符号数: {len(ranges)}")

# 展开范围为字符列表
expanded = parser.expand_ranges(ranges)
print(expanded)  # [(源码, 映射码), ...]

# 使用预设范围
presets = get_preset_ranges()
print(f"ASCII: {presets['ASCII']}")
print(f"数字: {presets['DIGITS']}")
```

**支持的格式**:
- ✅ 单个字符: `0x41` 或 `65`
- ✅ 范围: `0x20-0x7F`
- ✅ 映射: `0x41=>0x100`
- ✅ 范围映射: `0x20-0x7F=>0x100`
- ✅ 符号列表: `ABC123`
- ✅ 混合: `0x20-0x7F,0x41,0x100-0x110`

**预设范围**:
- ASCII
- ASCII_PRINTABLE
- DIGITS
- UPPERCASE
- LOWERCASE
- NUMBERS_PUNCTUATION
- LATIN_EXTENDED_A/B
- CYRILLIC
- GREEK
- CJK_UNIFIED_COMMON

---

## 🎨 实用示例

### 示例 1: 将字形渲染为图片

```python
import sys
sys.path.insert(0, 'src')

from core.glyph_renderer import GlyphRenderer
from PIL import Image
import freetype
import numpy as np

# 初始化
renderer = GlyphRenderer()
face = freetype.Face("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
renderer.set_font_face("font", face)
renderer.set_size(48)
renderer.set_bpp(4)

# 渲染字符
glyph = renderer.render_glyph("font", 0x41)  # 'A'

if glyph and glyph.bitmap.size > 0:
    # 转换为 8-bit 图像
    bitmap = (glyph.bitmap * 17).astype(np.uint8)  # 0-15 -> 0-255
    
    # 创建 PIL 图像
    img = Image.fromarray(bitmap, mode='L')
    
    # 放大 4 倍以便查看
    img = img.resize(
        (bitmap.shape[1] * 4, bitmap.shape[0] * 4),
        Image.NEAREST
    )
    
    # 保存
    img.save("glyph_A.png")
    print("已保存为 glyph_A.png")
```

---

### 示例 2: 批量检查字符支持

```python
import sys
sys.path.insert(0, 'src')

from core.font_loader import FontLoader

loader = FontLoader()
info = loader.load_font("/path/to/font.ttf")

# 检查中文常用字
chinese_chars = "你好世界中文字体测试"
supported = []
unsupported = []

for char in chinese_chars:
    code = ord(char)
    if code in info.supported_chars:
        supported.append(char)
    else:
        unsupported.append(char)

print(f"支持的字符: {''.join(supported)}")
print(f"不支持的字符: {''.join(unsupported)}")
```

---

### 示例 3: 分析字距调整

```python
import sys
sys.path.insert(0, 'src')

from core.glyph_renderer import GlyphRenderer
import freetype

renderer = GlyphRenderer()
face = freetype.Face("/path/to/font.ttf")
renderer.set_font_face("font", face)
renderer.set_size(24)

# 常见的字距调整对
kerning_pairs = [
    ("A", "V"),
    ("T", "o"),
    ("W", "A"),
    ("V", "A"),
    ("F", "A"),
]

print("字距调整分析:")
for left, right in kerning_pairs:
    left_code = ord(left)
    right_code = ord(right)
    kern_x, kern_y = renderer.get_kerning("font", left_code, right_code)
    
    if kern_x != 0 or kern_y != 0:
        print(f"{left}{right}: ({kern_x}, {kern_y})")
```

---

## 🧪 测试

### 运行特定测试

```bash
# 测试字体加载器
python -m pytest tests/test_font_loader.py -v

# 测试字形渲染器
python -m pytest tests/test_glyph_renderer.py -v

# 测试特定函数
python -m pytest tests/test_font_loader.py::TestFontLoader::test_load_real_font -v
```

### 生成测试报告

```bash
# HTML 覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html

# 在浏览器中查看
xdg-open htmlcov/index.html  # Linux
open htmlcov/index.html      # macOS
```

---

## 📂 项目结构

```
LVFontConv/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── core/              # 核心功能
│   │   ├── font_loader.py     # 字体加载器 ✅
│   │   ├── glyph_renderer.py  # 字形渲染器 ✅
│   │   └── range_parser.py    # 范围解析器 ✅
│   ├── utils/             # 工具模块
│   │   ├── logger.py          # 日志管理器 ✅
│   │   └── config.py          # 配置管理器 ✅
│   ├── ui/                # UI 模块 (Phase 3)
│   └── writers/           # 输出格式 (Phase 2)
├── tests/                 # 测试代码
│   ├── test_font_loader.py    # 10 tests ✅
│   └── test_glyph_renderer.py # 20 tests ✅
├── docs/                  # 文档
│   ├── requirements.md        # 需求文档
│   ├── tasks.md              # 任务分解
│   └── phase1-summary.md     # Phase 1 总结
├── demo.py                # 演示工具 ✅
├── requirements.txt       # 依赖列表
└── README.md             # 项目说明
```

---

## 🛠️ 开发

### 添加新功能

1. 在 `src/` 相应模块添加代码
2. 在 `tests/` 添加测试用例
3. 运行测试确保通过
4. 提交代码

### 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 保持测试覆盖率 > 80%

---

## 📝 日志

日志文件位置: `~/.lvfontconv/logs/`

查看日志:
```bash
tail -f ~/.lvfontconv/logs/lvfontconv_*.log
```

---

## 🔮 路线图

### ✅ Phase 1: 项目基础 (已完成)
- ✅ 日志系统
- ✅ 配置管理
- ✅ 范围解析
- ✅ 字体加载
- ✅ 字形渲染

### 🚧 Phase 2: LVGL 输出 (开发中)
- ⏳ LVGL 数据结构
- ⏳ LVGL Writer
- ⏳ Binary Writer
- ⏳ 转换器核心

### 📅 Phase 3: GUI 界面
- ⏳ 主窗口
- ⏳ 字体列表
- ⏳ 参数配置
- ⏳ 转换执行

### 📅 Phase 4: 预览功能
- ⏳ 预览控件
- ⏳ 网格背景
- ⏳ Color Depth 切换
- ⏳ 预览模式

---

## ❓ 常见问题

### Q: 为什么 GUI 没有显示？
A: GUI 界面将在 Phase 3 实现。当前版本（Phase 1）只完成了核心功能模块。

### Q: 如何测试功能？
A: 运行 `python demo.py` 查看演示，或使用 Python 导入相应模块。

### Q: 支持哪些字体格式？
A: 支持 TTF, OTF, WOFF, WOFF2 格式。

### Q: 如何报告问题？
A: 请在项目的 GitHub Issues 中报告问题。

---

## 📞 获取帮助

- 📖 查看文档: `docs/`
- 🧪 运行演示: `python demo.py`
- 🧪 运行测试: `python -m pytest tests/ -v`
- 📝 查看日志: `~/.lvfontconv/logs/`

---

**版本**: 0.1.0  
**更新日期**: 2025-11-07  
**状态**: Phase 1 完成 ✅
