"""
字体预览组件

提供字形预览功能，包括：
- 网格模式：显示所有字形
- 文本模式：输入文本预览
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QScrollArea, QPushButton,
    QSpinBox, QCheckBox, QProgressDialog
)
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QImage
import numpy as np

from core.font_loader import FontLoader
from core.glyph_renderer import GlyphRenderer
from ui.worker_thread import WorkerThread
from utils.logger import get_logger

logger = get_logger()


class GlyphPreviewCanvas(QWidget):
    """字形预览画布"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.glyphs = []  # [(char_code, glyph_data), ...]
        self.show_grid = True
        self.cell_size = 64
        self.columns = 16
        
        self.setMinimumSize(800, 600)
        self.setBackgroundRole(self.backgroundRole())
        self.setAutoFillBackground(True)
    
    def set_glyphs(self, glyphs):
        """设置要显示的字形"""
        self.glyphs = glyphs
        
        # 计算所需的高度
        if glyphs:
            rows = (len(glyphs) + self.columns - 1) // self.columns
            height = rows * self.cell_size + 40
            self.setMinimumHeight(height)
        
        self.update()
    
    def set_cell_size(self, size):
        """设置单元格大小"""
        self.cell_size = size
        if self.glyphs:
            rows = (len(self.glyphs) + self.columns - 1) // self.columns
            height = rows * self.cell_size + 40
            self.setMinimumHeight(height)
        self.update()
    
    def set_show_grid(self, show):
        """设置是否显示网格"""
        self.show_grid = show
        self.update()
    
    def paintEvent(self, event):
        """绘制字形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.glyphs:
            # 显示提示信息
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "请添加字体并选择字符范围"
            )
            return
        
        # 绘制字形
        for i, (char_code, glyph_data) in enumerate(self.glyphs):
            row = i // self.columns
            col = i % self.columns
            
            x = col * self.cell_size + 10
            y = row * self.cell_size + 10
            
            # 绘制单元格边框
            if self.show_grid:
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawRect(x, y, self.cell_size - 2, self.cell_size - 2)
            
            # 绘制字符标签
            painter.setPen(QColor(100, 100, 100))
            font = QFont("monospace", 8)
            painter.setFont(font)
            label = f"U+{char_code:04X}"
            painter.drawText(x + 2, y + 12, label)
            
            # 绘制字形位图
            if glyph_data and glyph_data.bitmap is not None and glyph_data.bitmap.size > 0:
                self._draw_glyph_bitmap(
                    painter,
                    glyph_data,
                    x + self.cell_size // 2,
                    y + self.cell_size // 2
                )
    
    def _draw_glyph_bitmap(self, painter, glyph_data, center_x, center_y):
        """绘制字形位图"""
        bitmap = glyph_data.bitmap
        width = glyph_data.width
        height = glyph_data.height
        
        if width == 0 or height == 0:
            return
        
        # 创建 QImage
        # 假设 bitmap 是灰度图
        if bitmap.ndim == 1:
            bitmap = bitmap.reshape(height, width)
        
        # FreeType 返回的 bitmap 可能是不同位深度的灰度图
        # 需要归一化到 0-255 范围
        if bitmap.max() > 0:
            # 将 bitmap 缩放到 0-255 范围
            normalized = (bitmap.astype(np.float32) / bitmap.max() * 255).astype(np.uint8)
        else:
            normalized = bitmap.astype(np.uint8)
        
        # 转换为 RGBA (黑色字形)
        # 使用 normalized bitmap 作为 alpha 通道，RGB 设为 0
        image_data = np.zeros((height, width, 4), dtype=np.uint8)
        image_data[:, :, 0] = 0          # R (黑色)
        image_data[:, :, 1] = 0          # G (黑色)
        image_data[:, :, 2] = 0          # B (黑色)
        image_data[:, :, 3] = normalized # A (不透明度)
        
        # 创建 QImage
        qimage = QImage(
            image_data.data,
            width,
            height,
            width * 4,
            QImage.Format.Format_RGBA8888
        )
        
        # 计算位置（居中）
        x = center_x - width // 2
        y = center_y - height // 2
        
        # 绘制
        painter.drawImage(x, y, qimage)


class PreviewWidget(QWidget):
    """
    字体预览组件
    
    提供字形网格预览和文本预览功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.font_path = None
        self.font_loader = None
        self.renderer = None
        self.worker_thread = None  # 后台渲染线程
        self.progress_dialog = None  # 进度对话框
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 预览画布（放在滚动区域中）
        self.canvas = GlyphPreviewCanvas()
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def _create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 模式选择
        layout.addWidget(QLabel("预览模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["网格视图", "文本预览"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_combo)
        
        layout.addSpacing(20)
        
        # 字体大小
        layout.addWidget(QLabel("字体大小:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 128)
        self.size_spin.setValue(16)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        layout.addWidget(self.size_spin)
        
        layout.addSpacing(20)
        
        # 单元格大小（仅网格模式）
        self.cell_size_label = QLabel("单元格:")
        layout.addWidget(self.cell_size_label)
        self.cell_size_spin = QSpinBox()
        self.cell_size_spin.setRange(32, 128)
        self.cell_size_spin.setValue(64)
        self.cell_size_spin.valueChanged.connect(self._on_cell_size_changed)
        layout.addWidget(self.cell_size_spin)
        
        layout.addSpacing(20)
        
        # 显示网格
        self.grid_check = QCheckBox("显示网格")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self.grid_check)
        
        layout.addStretch()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self.refresh_btn)
        
        return panel
    
    def set_font(self, font_path: str, size: int = 16):
        """设置要预览的字体"""
        self.font_path = font_path
        
        try:
            # 加载字体
            if self.font_loader:
                # 卸载之前的字体
                self.font_loader = None
            
            self.font_loader = FontLoader()
            font_info = self.font_loader.load_font(font_path)
            
            # 创建渲染器
            self.renderer = GlyphRenderer()
            
            # 从 FontLoader 获取 FreeType Face 并设置到渲染器
            if font_path in self.font_loader._freetype_faces:
                face = self.font_loader._freetype_faces[font_path]
                self.renderer.set_font_face(font_path, face)
                # 设置大小(必须在 set_font_face 之后)
                self.renderer.set_size(size)
            
            logger.info(f"预览字体已加载: {font_info.family_name}, 大小: {size}px")
            
        except Exception as e:
            logger.error(f"加载字体失败: {e}", exc_info=True)
    
    def set_ranges(self, ranges: list, symbols: str = ""):
        """设置要预览的字符范围"""
        if not self.font_path or not self.renderer:
            return
        
        # 收集字符码点
        codepoints = set()
        
        for range_str in ranges:
            try:
                if '-' in range_str:
                    # 范围格式: "0x30-0x39" 或 "48-57"
                    start_str, end_str = range_str.split('-')
                    start = int(start_str, 0)  # auto-detect base
                    end = int(end_str, 0)
                    codepoints.update(range(start, end + 1))
            except:
                pass
        
        # 添加符号
        for char in symbols:
            codepoints.add(ord(char))
        
        total_chars = len(codepoints)
        
        # 如果字符数量很多,使用后台线程
        if total_chars > 100:
            self._render_glyphs_async(sorted(codepoints))
        else:
            self._render_glyphs_sync(sorted(codepoints))
    
    def _render_glyphs_sync(self, codepoints):
        """同步渲染字形(少量字符)"""
        glyphs = []
        for code in codepoints:
            try:
                glyph_data = self.renderer.render_glyph(self.font_path, code)
                glyphs.append((code, glyph_data))
            except Exception as e:
                logger.debug(f"渲染字符 U+{code:04X} 失败: {e}")
        
        self.canvas.set_glyphs(glyphs)
        logger.info(f"预览已更新: {len(glyphs)} 个字形")
    
    def _render_glyphs_async(self, codepoints):
        """异步渲染字形(大量字符)"""
        # 取消之前的任务
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.cancel()
            self.worker_thread.wait()
        
        # 显示进度对话框
        self.progress_dialog = QProgressDialog(
            "正在渲染字形...",
            "取消",
            0,
            len(codepoints),
            self
        )
        self.progress_dialog.setWindowTitle("预览")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self._on_render_cancelled)
        
        # 创建后台任务
        def render_task():
            glyphs = []
            for i, code in enumerate(codepoints):
                if self.worker_thread and self.worker_thread.is_cancelled():
                    break
                
                try:
                    glyph_data = self.renderer.render_glyph(self.font_path, code)
                    glyphs.append((code, glyph_data))
                except Exception as e:
                    logger.debug(f"渲染字符 U+{code:04X} 失败: {e}")
                
                # 更新进度(每10个字符更新一次,避免过于频繁)
                if i % 10 == 0 and self.progress_dialog:
                    self.progress_dialog.setValue(i)
            
            return glyphs
        
        # 启动后台线程
        self.worker_thread = WorkerThread(render_task)
        self.worker_thread.finished.connect(self._on_render_finished)
        self.worker_thread.error.connect(self._on_render_error)
        self.worker_thread.start()
    
    def _on_render_finished(self, glyphs):
        """渲染完成"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.canvas.set_glyphs(glyphs)
        logger.info(f"预览已更新: {len(glyphs)} 个字形")
    
    def _on_render_error(self, error):
        """渲染出错"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        logger.error(f"渲染失败: {error}")
    
    def _on_render_cancelled(self):
        """取消渲染"""
        if self.worker_thread:
            self.worker_thread.cancel()
            logger.info("用户取消渲染")
    
    def _on_mode_changed(self, index):
        """模式切换"""
        # TODO: 实现文本预览模式
        logger.info(f"预览模式: {self.mode_combo.currentText()}")
    
    def _on_size_changed(self, value):
        """字体大小改变"""
        if self.renderer:
            self.renderer.set_size(value)
            # 重新渲染
            # TODO: 触发重新渲染
    
    def _on_cell_size_changed(self, value):
        """单元格大小改变"""
        self.canvas.set_cell_size(value)
    
    def _on_grid_toggled(self, checked):
        """网格显示切换"""
        self.canvas.set_show_grid(checked)
    
    def _on_refresh(self):
        """刷新预览"""
        # TODO: 从主窗口获取当前字体和范围
        logger.info("刷新预览")
