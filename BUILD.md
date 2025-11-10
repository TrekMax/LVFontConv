# LVFontConv 打包说明

## 依赖安装

首先确保安装了 PyInstaller:

```bash
pip install pyinstaller
```

## 打包步骤

### 1. 运行打包脚本

```bash
python build.py
```

### 2. 查看输出

打包完成后,可执行文件位于 `dist/LVFontConv/` 目录:

- **Linux**: `dist/LVFontConv/LVFontConv`
- **Windows**: `dist/LVFontConv/LVFontConv.exe`
- **macOS**: `dist/LVFontConv/LVFontConv.app`

### 3. 测试可执行文件

```bash
cd dist/LVFontConv
./LVFontConv  # Linux/macOS
# 或
LVFontConv.exe  # Windows
```

## 单文件模式

如果需要单文件模式(所有内容打包到一个可执行文件),在 `build.py` 中取消注释 `--onefile` 选项:

```python
# 单文件模式
"--onefile",
```

注意:单文件模式启动较慢,因为需要解压临时文件。

## 添加图标

1. 准备图标文件:
   - Windows: `resources/icon.ico` (256x256)
   - macOS: `resources/icon.icns`
   - Linux: `resources/icon.png` (256x256)

2. 在 `build.py` 中取消注释对应的图标选项

## 自定义打包

编辑 `build.py` 中的 `pyinstaller_args` 列表来自定义打包选项:

- `--hidden-import`: 添加隐藏导入的模块
- `--exclude-module`: 排除不需要的模块以减小体积
- `--add-data`: 添加数据文件(格式: `源路径:目标路径`)

## 常见问题

### 1. 打包后无法运行

检查是否缺少动态库依赖。使用 `ldd` (Linux) 或 `otool -L` (macOS) 检查依赖:

```bash
ldd dist/LVFontConv/LVFontConv
```

### 2. 体积过大

- 使用 `--exclude-module` 排除不需要的模块
- 不要使用 `--onefile`,使用目录模式
- 在虚拟环境中打包,避免打包系统全局包

### 3. 启动速度慢

- 不使用 `--onefile` 单文件模式
- 使用 `--strip` 去除符号表
- 考虑使用 `--bootloader-ignore-signals` (某些情况)

## 分发

打包完成后,可以将 `dist/LVFontConv/` 整个目录压缩分发:

```bash
cd dist
tar -czf LVFontConv-v1.0.0-linux-x64.tar.gz LVFontConv/
# 或
zip -r LVFontConv-v1.0.0-linux-x64.zip LVFontConv/
```

## 版本信息 (Windows)

Windows 平台需要创建 `version_info.txt` 文件:

```bash
pyi-grab_version --version-file version_info.txt python.exe
```

然后编辑 `version_info.txt` 填写应用信息。
