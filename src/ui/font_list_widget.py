"""
字体列表组件

显示已添加的字体文件列表，支持：
- 添加/删除字体
- 编辑字符范围
- 显示字体信息
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLabel,
    QLineEdit, QTextEdit, QMessageBox, QFileDialog,
    QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

from utils.logger import get_logger

logger = get_logger()


@dataclass
class FontSource:
    """字体源数据类"""
    path: str
    ranges: List[str] = field(default_factory=list)  # ["0x30-0x39", "0x41-0x5A"]
    symbols: str = ""  # "©®™"
    
    def __str__(self):
        return Path(self.path).name
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return Path(self.path).name
    
    @property
    def char_count(self) -> int:
        """估算字符数"""
        count = len(self.symbols)
        for r in self.ranges:
            if '-' in r:
                parts = r.split('-')
                if len(parts) == 2:
                    try:
                        start = int(parts[0], 0)
                        end = int(parts[1], 0)
                        count += (end - start + 1)
                    except:
                        pass
        return count
    
    def to_dict(self):
        """转换为字典用于序列化"""
        return {
            "path": self.path,
            "ranges": self.ranges,
            "symbols": self.symbols,
            "display_name": self.display_name
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            path=data["path"],
            ranges=data.get("ranges", []),
            symbols=data.get("symbols", "")
        )


class FontListWidget(QWidget):
    """
    字体列表组件
    
    左侧显示字体列表，右侧显示字体详情和范围编辑。
    """
    
    # 信号
    font_added = pyqtSignal(str)  # 添加字体
    font_removed = pyqtSignal(int)  # 移除字体
    font_changed = pyqtSignal()  # 字体列表变化
    
    def __init__(self):
        """初始化组件"""
        super().__init__()
        
        self.font_sources: List[FontSource] = []
        self.current_font: Optional[FontSource] = None
        
        self._init_ui()
        
        logger.debug("FontListWidget 初始化完成")
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：字体列表
        left_widget = self._create_font_list_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：字体详情
        right_widget = self._create_font_detail_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def _create_font_list_panel(self) -> QWidget:
        """创建字体列表面板"""
        widget = QGroupBox("字体列表")
        layout = QVBoxLayout(widget)
        
        # 字体列表
        self.font_list = QListWidget()
        self.font_list.currentItemChanged.connect(self._on_font_selected)
        layout.addWidget(self.font_list)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("添加字体")
        self.btn_add.clicked.connect(self._on_add_font)
        button_layout.addWidget(self.btn_add)
        
        self.btn_remove = QPushButton("移除")
        self.btn_remove.clicked.connect(self._on_remove_font)
        self.btn_remove.setEnabled(False)
        button_layout.addWidget(self.btn_remove)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return widget
    
    def _create_font_detail_panel(self) -> QWidget:
        """创建字体详情面板"""
        widget = QGroupBox("字体详情")
        layout = QVBoxLayout(widget)
        
        # 字体信息
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout(info_group)
        
        self.lbl_font_path = QLabel("路径: -")
        self.lbl_font_path.setWordWrap(True)
        info_layout.addWidget(self.lbl_font_path)
        
        self.lbl_char_count = QLabel("字符数: -")
        info_layout.addWidget(self.lbl_char_count)
        
        layout.addWidget(info_group)
        
        # 字符范围
        range_group = QGroupBox("字符范围")
        range_layout = QVBoxLayout(range_group)
        
        # 说明
        help_text = QLabel(
            "输入字符范围，每行一个，格式:\n"
            "  • 范围: 0x30-0x39 (数字 0-9)\n"
            "  • 范围: 0x41-0x5A (大写字母 A-Z)\n"
            "  • 十进制: 48-57 (也是 0-9)\n"
            "示例:\n"
            "  0x30-0x39\n"
            "  0x41-0x5A\n"
            "  0x61-0x7A"
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        range_layout.addWidget(help_text)
        
        self.txt_ranges = QTextEdit()
        self.txt_ranges.setPlaceholderText("每行一个范围，如: 0x30-0x39")
        self.txt_ranges.setMaximumHeight(120)
        self.txt_ranges.textChanged.connect(self._on_ranges_changed)
        range_layout.addWidget(self.txt_ranges)
        
        layout.addWidget(range_group)
        
        # 符号字符
        symbol_group = QGroupBox("单独符号")
        symbol_layout = QVBoxLayout(symbol_group)
        
        symbol_help = QLabel("直接输入要包含的符号字符:")
        symbol_help.setStyleSheet("color: #666; font-size: 11px;")
        symbol_layout.addWidget(symbol_help)
        
        self.txt_symbols = QLineEdit()
        self.txt_symbols.setPlaceholderText("如: .,!?:;-+*/=()[]{}@#$%&")
        self.txt_symbols.textChanged.connect(self._on_symbols_changed)
        symbol_layout.addWidget(self.txt_symbols)
        
        layout.addWidget(symbol_group)
        
        layout.addStretch()
        
        # 默认禁用编辑
        self._set_detail_enabled(False)
        
        return widget
    
    def _set_detail_enabled(self, enabled: bool):
        """设置详情面板是否可编辑"""
        self.txt_ranges.setEnabled(enabled)
        self.txt_symbols.setEnabled(enabled)
    
    # ========== 事件处理 ==========
    
    def _on_add_font(self):
        """添加字体"""
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "选择字体文件",
            "",
            "字体文件 (*.ttf *.otf *.woff *.woff2);;所有文件 (*)"
        )
        
        if not filenames:
            return
        
        for filepath in filenames:
            # 检查是否已存在
            if any(f.path == filepath for f in self.font_sources):
                logger.warning(f"字体已存在: {filepath}")
                continue
            
            # 创建字体源
            font_source = FontSource(path=filepath)
            self.font_sources.append(font_source)
            
            # 添加到列表
            item = QListWidgetItem(font_source.display_name)
            item.setData(Qt.ItemDataRole.UserRole, len(self.font_sources) - 1)
            self.font_list.addItem(item)
            
            logger.info(f"添加字体: {filepath}")
            self.font_added.emit(filepath)
        
        self.font_changed.emit()
    
    def _on_remove_font(self):
        """移除字体"""
        current_item = self.font_list.currentItem()
        if not current_item:
            return
        
        index = current_item.data(Qt.ItemDataRole.UserRole)
        font_source = self.font_sources[index]
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要移除字体 '{font_source.display_name}' 吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从列表移除
            self.font_list.takeItem(self.font_list.row(current_item))
            self.font_sources.pop(index)
            
            # 更新所有 item 的索引
            for i in range(self.font_list.count()):
                item = self.font_list.item(i)
                item.setData(Qt.ItemDataRole.UserRole, i)
            
            logger.info(f"移除字体: {font_source.path}")
            self.font_removed.emit(index)
            self.font_changed.emit()
            
            # 清空详情
            if not self.font_sources:
                self._clear_details()
    
    def _on_font_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """字体选中变化"""
        if current:
            index = current.data(Qt.ItemDataRole.UserRole)
            self.current_font = self.font_sources[index]
            self._update_details(self.current_font)
            self.btn_remove.setEnabled(True)
            self._set_detail_enabled(True)
        else:
            self.current_font = None
            self._clear_details()
            self.btn_remove.setEnabled(False)
            self._set_detail_enabled(False)
    
    def _on_ranges_changed(self):
        """字符范围变化"""
        if not self.current_font:
            return
        
        # 解析范围
        text = self.txt_ranges.toPlainText()
        ranges = [line.strip() for line in text.split('\n') if line.strip()]
        
        self.current_font.ranges = ranges
        self._update_char_count()
        
        logger.debug(f"更新范围: {ranges}")
    
    def _on_symbols_changed(self, text: str):
        """符号字符变化"""
        if not self.current_font:
            return
        
        self.current_font.symbols = text
        self._update_char_count()
        
        logger.debug(f"更新符号: {text}")
    
    def _update_details(self, font_source: FontSource):
        """更新详情显示"""
        self.lbl_font_path.setText(f"路径: {font_source.path}")
        
        # 更新范围
        self.txt_ranges.blockSignals(True)
        self.txt_ranges.setPlainText('\n'.join(font_source.ranges))
        self.txt_ranges.blockSignals(False)
        
        # 更新符号
        self.txt_symbols.blockSignals(True)
        self.txt_symbols.setText(font_source.symbols)
        self.txt_symbols.blockSignals(False)
        
        self._update_char_count()
    
    def _update_char_count(self):
        """更新字符数显示"""
        if self.current_font:
            count = self.current_font.char_count
            self.lbl_char_count.setText(f"字符数: 约 {count} 个")
    
    def _clear_details(self):
        """清空详情"""
        self.lbl_font_path.setText("路径: -")
        self.lbl_char_count.setText("字符数: -")
        self.txt_ranges.clear()
        self.txt_symbols.clear()
    
    # ========== 公共接口 ==========
    
    def get_font_sources(self) -> List[FontSource]:
        """获取所有字体源"""
        return self.font_sources.copy()
    
    def clear_fonts(self):
        """清空所有字体"""
        self.font_list.clear()
        self.font_sources.clear()
        self.current_font = None
        self._clear_details()
        self.btn_remove.setEnabled(False)
        self._set_detail_enabled(False)
        self.font_changed.emit()
    
    def add_font_source(self, font_source: FontSource):
        """添加字体源（用于加载项目）"""
        self.font_sources.append(font_source)
        
        item = QListWidgetItem(font_source.display_name)
        item.setData(Qt.ItemDataRole.UserRole, len(self.font_sources) - 1)
        self.font_list.addItem(item)
        
        self.font_changed.emit()
