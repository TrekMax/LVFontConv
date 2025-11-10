"""
配置组件 - 管理字体转换参数配置

提供字体大小、BPP、压缩方式、LVGL版本等配置选项的图形界面。
"""

from dataclasses import dataclass, field
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QComboBox, QRadioButton, 
    QButtonGroup, QCheckBox, QLineEdit, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.logger import get_logger

logger = get_logger()


@dataclass
class ConvertConfig:
    """转换配置数据类"""
    # 字体大小
    font_size: int = 16
    
    # BPP (bits per pixel)
    bpp: int = 4
    
    # 压缩方式
    compression: str = "rle"  # none, rle
    
    # LVGL 版本
    lvgl_version: int = 8  # 7, 8, 9
    
    # 输出格式
    output_format: str = "lvgl"  # lvgl, bin, dump
    
    # 输出目录
    output_dir: str = "./output"
    
    # 输出文件名
    output_name: str = "my_font"
    
    # 高级选项
    no_compress: bool = False
    no_prefilter: bool = False
    no_kerning: bool = False
    lcd: bool = False
    lcd_v: bool = False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'font_size': self.font_size,
            'bpp': self.bpp,
            'compression': self.compression,
            'lvgl_version': self.lvgl_version,
            'output_format': self.output_format,
            'output_dir': self.output_dir,
            'output_name': self.output_name,
            'no_compress': self.no_compress,
            'no_prefilter': self.no_prefilter,
            'no_kerning': self.no_kerning,
            'lcd': self.lcd,
            'lcd_v': self.lcd_v,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConvertConfig':
        """从字典创建"""
        return cls(
            font_size=data.get('font_size', 16),
            bpp=data.get('bpp', 4),
            compression=data.get('compression', 'rle'),
            lvgl_version=data.get('lvgl_version', 8),
            output_format=data.get('output_format', 'lvgl'),
            output_dir=data.get('output_dir', './output'),
            output_name=data.get('output_name', 'my_font'),
            no_compress=data.get('no_compress', False),
            no_prefilter=data.get('no_prefilter', False),
            no_kerning=data.get('no_kerning', False),
            lcd=data.get('lcd', False),
            lcd_v=data.get('lcd_v', False),
        )


class ConfigWidget(QWidget):
    """配置组件"""
    
    # 信号
    config_changed = pyqtSignal()  # 配置变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConvertConfig()
        self._init_ui()
        logger.info("配置组件初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 基本配置
        basic_group = self._create_basic_config()
        layout.addWidget(basic_group)
        
        # 输出配置
        output_group = self._create_output_config()
        layout.addWidget(output_group)
        
        # 高级选项
        advanced_group = self._create_advanced_config()
        layout.addWidget(advanced_group)
        
        layout.addStretch()
    
    def _create_basic_config(self) -> QGroupBox:
        """创建基本配置组"""
        group = QGroupBox("基本配置")
        layout = QFormLayout(group)
        
        # 字体大小
        size_layout = QHBoxLayout()
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(8)
        self.size_slider.setMaximum(200)
        self.size_slider.setValue(self.config.font_size)
        self.size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.size_slider.setTickInterval(16)
        
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setMinimum(8)
        self.size_spinbox.setMaximum(200)
        self.size_spinbox.setValue(self.config.font_size)
        self.size_spinbox.setSuffix(" px")
        
        # 双向绑定
        self.size_slider.valueChanged.connect(self.size_spinbox.setValue)
        self.size_spinbox.valueChanged.connect(self.size_slider.setValue)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_spinbox)
        layout.addRow("字体大小:", size_layout)
        
        # BPP (位深度)
        bpp_layout = QHBoxLayout()
        self.bpp_group = QButtonGroup(self)
        
        for bpp in [1, 2, 4, 8]:
            radio = QRadioButton(f"{bpp} bit")
            self.bpp_group.addButton(radio, bpp)
            bpp_layout.addWidget(radio)
            if bpp == self.config.bpp:
                radio.setChecked(True)
        
        self.bpp_group.buttonClicked.connect(self._on_bpp_changed)
        bpp_layout.addStretch()
        layout.addRow("位深度 (BPP):", bpp_layout)
        
        # LVGL 版本
        self.lvgl_version_combo = QComboBox()
        self.lvgl_version_combo.addItems(["7", "8", "9"])
        self.lvgl_version_combo.setCurrentText(str(self.config.lvgl_version))
        self.lvgl_version_combo.currentTextChanged.connect(self._on_lvgl_version_changed)
        layout.addRow("LVGL 版本:", self.lvgl_version_combo)
        
        return group
    
    def _create_output_config(self) -> QGroupBox:
        """创建输出配置组"""
        group = QGroupBox("输出配置")
        layout = QFormLayout(group)
        
        # 输出格式
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems([
            "LVGL C 文件 (lvgl)",
            "二进制文件 (bin)",
            "转储文件 (dump)"
        ])
        self.output_format_combo.setCurrentIndex(0)
        self.output_format_combo.currentIndexChanged.connect(self._on_output_format_changed)
        layout.addRow("输出格式:", self.output_format_combo)
        
        # 输出目录
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(self.config.output_dir)
        self.output_dir_edit.setPlaceholderText("例如: ./output")
        self.output_dir_edit.textChanged.connect(self._on_output_dir_changed)
        output_dir_layout.addWidget(self.output_dir_edit)
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._on_browse_output_dir)
        output_dir_layout.addWidget(browse_button)
        
        layout.addRow("输出目录:", output_dir_layout)
        
        # 压缩方式
        self.compression_combo = QComboBox()
        self.compression_combo.addItems([
            "RLE 压缩 (rle)",
            "无压缩 (none)"
        ])
        self.compression_combo.setCurrentIndex(0)
        self.compression_combo.currentIndexChanged.connect(self._on_compression_changed)
        layout.addRow("压缩方式:", self.compression_combo)
        
        # 输出文件名
        output_name_layout = QHBoxLayout()
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setText(self.config.output_name)
        self.output_name_edit.setPlaceholderText("例如: my_font")
        self.output_name_edit.textChanged.connect(self._on_output_name_changed)
        output_name_layout.addWidget(self.output_name_edit)
        
        browse_file_button = QPushButton("另存为...")
        browse_file_button.clicked.connect(self._on_browse_output_file)
        output_name_layout.addWidget(browse_file_button)
        
        layout.addRow("输出文件名:", output_name_layout)
        
        return group
    
    def _create_advanced_config(self) -> QGroupBox:
        """创建高级配置组"""
        group = QGroupBox("高级选项")
        layout = QVBoxLayout(group)
        
        # 禁用压缩
        self.no_compress_check = QCheckBox("禁用压缩 (--no-compress)")
        self.no_compress_check.setChecked(self.config.no_compress)
        self.no_compress_check.stateChanged.connect(self._on_no_compress_changed)
        layout.addWidget(self.no_compress_check)
        
        # 禁用预过滤
        self.no_prefilter_check = QCheckBox("禁用预过滤 (--no-prefilter)")
        self.no_prefilter_check.setChecked(self.config.no_prefilter)
        self.no_prefilter_check.stateChanged.connect(self._on_no_prefilter_changed)
        layout.addWidget(self.no_prefilter_check)
        
        # 禁用字距调整
        self.no_kerning_check = QCheckBox("禁用字距调整 (--no-kerning)")
        self.no_kerning_check.setChecked(self.config.no_kerning)
        self.no_kerning_check.stateChanged.connect(self._on_no_kerning_changed)
        layout.addWidget(self.no_kerning_check)
        
        # LCD 模式
        self.lcd_check = QCheckBox("LCD 模式 (--lcd)")
        self.lcd_check.setChecked(self.config.lcd)
        self.lcd_check.setToolTip("水平 LCD 渲染")
        self.lcd_check.stateChanged.connect(self._on_lcd_changed)
        layout.addWidget(self.lcd_check)
        
        # LCD 垂直模式
        self.lcd_v_check = QCheckBox("LCD 垂直模式 (--lcd-v)")
        self.lcd_v_check.setChecked(self.config.lcd_v)
        self.lcd_v_check.setToolTip("垂直 LCD 渲染")
        self.lcd_v_check.stateChanged.connect(self._on_lcd_v_changed)
        layout.addWidget(self.lcd_v_check)
        
        return group
    
    # 事件处理
    def _on_size_changed(self, value: int):
        """字体大小改变"""
        self.config.font_size = value
        self.config_changed.emit()
        logger.debug(f"字体大小: {value}")
    
    def _on_bpp_changed(self):
        """BPP 改变"""
        button = self.bpp_group.checkedButton()
        if button:
            bpp = self.bpp_group.id(button)
            self.config.bpp = bpp
            self.config_changed.emit()
            logger.debug(f"BPP: {bpp}")
    
    def _on_lvgl_version_changed(self, text: str):
        """LVGL 版本改变"""
        self.config.lvgl_version = int(text)
        self.config_changed.emit()
        logger.debug(f"LVGL 版本: {text}")
    
    def _on_output_format_changed(self, index: int):
        """输出格式改变"""
        formats = ["lvgl", "bin", "dump"]
        self.config.output_format = formats[index]
        self.config_changed.emit()
        logger.debug(f"输出格式: {formats[index]}")
    
    def _on_compression_changed(self, index: int):
        """压缩方式改变"""
        compressions = ["rle", "none"]
        self.config.compression = compressions[index]
        self.config_changed.emit()
        logger.debug(f"压缩方式: {compressions[index]}")
    
    def _on_output_name_changed(self, text: str):
        """输出文件名改变"""
        self.config.output_name = text
        self.config_changed.emit()
    
    def _on_output_dir_changed(self, text: str):
        """输出目录改变"""
        self.config.output_dir = text
        self.config_changed.emit()
    
    def _on_browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.config.output_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def _on_browse_output_file(self):
        """浏览输出文件"""
        # 根据输出格式确定文件过滤器
        format_filters = {
            0: "C 文件 (*.c);;所有文件 (*)",  # lvgl
            1: "二进制文件 (*.bin);;所有文件 (*)",  # bin
            2: "文本文件 (*.txt);;所有文件 (*)",  # dump
        }
        
        current_format = self.output_format_combo.currentIndex()
        file_filter = format_filters.get(current_format, "所有文件 (*)")
        
        # 构建默认文件名（包含目录）
        import os
        default_path = os.path.join(
            self.config.output_dir,
            self.config.output_name
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出文件",
            default_path,
            file_filter
        )
        
        if file_path:
            # 分离目录和文件名
            import os
            dir_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            # 移除扩展名
            file_name_without_ext = os.path.splitext(file_name)[0]
            
            # 更新目录和文件名
            self.output_dir_edit.setText(dir_path)
            self.output_name_edit.setText(file_name_without_ext)
    
    def _on_no_compress_changed(self, state: int):
        """禁用压缩改变"""
        self.config.no_compress = bool(state)
        self.config_changed.emit()
    
    def _on_no_prefilter_changed(self, state: int):
        """禁用预过滤改变"""
        self.config.no_prefilter = bool(state)
        self.config_changed.emit()
    
    def _on_no_kerning_changed(self, state: int):
        """禁用字距调整改变"""
        self.config.no_kerning = bool(state)
        self.config_changed.emit()
    
    def _on_lcd_changed(self, state: int):
        """LCD 模式改变"""
        self.config.lcd = bool(state)
        if self.config.lcd and self.config.lcd_v:
            # 互斥: 如果启用 LCD,禁用 LCD-V
            self.lcd_v_check.setChecked(False)
        self.config_changed.emit()
    
    def _on_lcd_v_changed(self, state: int):
        """LCD 垂直模式改变"""
        self.config.lcd_v = bool(state)
        if self.config.lcd_v and self.config.lcd:
            # 互斥: 如果启用 LCD-V,禁用 LCD
            self.lcd_check.setChecked(False)
        self.config_changed.emit()
    
    # 公共 API
    def get_config(self) -> ConvertConfig:
        """获取当前配置"""
        return self.config
    
    def set_config(self, config: ConvertConfig):
        """设置配置"""
        self.config = config
        
        # 更新 UI
        self.size_slider.setValue(config.font_size)
        self.size_spinbox.setValue(config.font_size)
        
        # 设置 BPP
        for button in self.bpp_group.buttons():
            if self.bpp_group.id(button) == config.bpp:
                button.setChecked(True)
                break
        
        self.lvgl_version_combo.setCurrentText(str(config.lvgl_version))
        
        # 输出格式
        formats = ["lvgl", "bin", "dump"]
        if config.output_format in formats:
            self.output_format_combo.setCurrentIndex(formats.index(config.output_format))
        
        # 压缩方式
        compressions = ["rle", "none"]
        if config.compression in compressions:
            self.compression_combo.setCurrentIndex(compressions.index(config.compression))
        
        self.output_dir_edit.setText(config.output_dir)
        self.output_name_edit.setText(config.output_name)
        
        # 高级选项
        self.no_compress_check.setChecked(config.no_compress)
        self.no_prefilter_check.setChecked(config.no_prefilter)
        self.no_kerning_check.setChecked(config.no_kerning)
        self.lcd_check.setChecked(config.lcd)
        self.lcd_v_check.setChecked(config.lcd_v)
        
        logger.info("配置已加载")
    
    def reset_config(self):
        """重置为默认配置"""
        self.set_config(ConvertConfig())
        logger.info("配置已重置")
