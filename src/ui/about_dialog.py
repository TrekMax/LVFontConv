"""
关于对话框 - 显示应用程序信息

显示版本号、作者、许可证等信息。
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class AboutDialog(QDialog):
    """关于对话框"""
    
    VERSION = "1.0.0"
    AUTHOR = "LVGL Font Converter Team"
    LICENSE = "MIT License"
    DESCRIPTION = "LVGL 字体转换工具 - 将 TTF/OTF 字体转换为 LVGL C 代码"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 LVFontConv")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 应用名称
        title_label = QLabel("LVFontConv")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本号
        version_label = QLabel(f"版本 {self.VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # 描述
        desc_label = QLabel(self.DESCRIPTION)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addSpacing(10)
        
        # 作者
        author_label = QLabel(f"<b>作者:</b> {self.AUTHOR}")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)
        
        # 许可证
        license_label = QLabel(f"<b>许可证:</b> {self.LICENSE}")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)
        
        layout.addSpacing(10)
        
        # 项目链接
        link_label = QLabel(
            '<a href="https://github.com/lvgl/lv_font_conv">GitHub 项目主页</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(link_label)
        
        layout.addStretch()
        
        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("关闭")
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    @staticmethod
    def show_about(parent=None):
        """显示关于对话框"""
        dialog = AboutDialog(parent)
        dialog.exec()
