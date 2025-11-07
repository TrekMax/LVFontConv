"""
LVFontConv 主窗口

PyQt6 主窗口实现，包含：
- 菜单栏
- 工具栏
- 状态栏
- 中心布局区域
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QSplitter, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from .font_list_widget import FontListWidget
from .config_widget import ConfigWidget
from .convert_dialog import ConvertDialog
from utils.logger import get_logger

logger = get_logger()


class MainWindow(QMainWindow):
    """
    LVFontConv 主窗口
    
    提供字体转换工具的主界面，包含：
    - 字体源列表
    - 参数配置面板
    - 预览区域
    - 转换控制
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle("LVFontConv - LVGL 字体转换工具")
        self.setMinimumSize(1024, 768)
        
        # 恢复窗口状态
        self.settings = QSettings("LVGL", "LVFontConv")
        self._restore_window_state()
        
        # 创建 UI 组件
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._init_ui()
        self._create_statusbar()
        
        logger.info("主窗口初始化完成")
    
    def _create_actions(self):
        """创建操作动作"""
        # 文件菜单动作
        self.action_new = QAction("新建项目(&N)", self)
        self.action_new.setShortcut(QKeySequence.StandardKey.New)
        self.action_new.setStatusTip("创建新的字体转换项目")
        self.action_new.triggered.connect(self._on_new_project)
        
        self.action_open = QAction("打开项目(&O)...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.setStatusTip("打开已保存的项目")
        self.action_open.triggered.connect(self._on_open_project)
        
        self.action_save = QAction("保存项目(&S)", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.setStatusTip("保存当前项目")
        self.action_save.triggered.connect(self._on_save_project)
        
        self.action_save_as = QAction("另存为(&A)...", self)
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.action_save_as.setStatusTip("将项目保存到新文件")
        self.action_save_as.triggered.connect(self._on_save_project_as)
        
        self.action_exit = QAction("退出(&X)", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.setStatusTip("退出应用程序")
        self.action_exit.triggered.connect(self.close)
        
        # 字体菜单动作
        self.action_add_font = QAction("添加字体(&A)", self)
        self.action_add_font.setShortcut(QKeySequence("Ctrl+A"))
        self.action_add_font.setStatusTip("添加字体文件")
        # 连接到字体列表组件的内部方法(稍后在 _init_ui 中设置)
        
        self.action_remove_font = QAction("移除字体(&R)", self)
        self.action_remove_font.setShortcut(QKeySequence("Del"))
        self.action_remove_font.setStatusTip("移除选中的字体")
        self.action_remove_font.setEnabled(False)
        # 连接到字体列表组件的内部方法(稍后在 _init_ui 中设置)
        self.action_remove_font.setEnabled(False)
        
        # 转换菜单动作
        self.action_convert = QAction("开始转换(&C)", self)
        self.action_convert.setShortcut(QKeySequence("F5"))
        self.action_convert.setStatusTip("执行字体转换")
        self.action_convert.triggered.connect(self._on_convert)
        
        self.action_preview = QAction("预览字体(&P)", self)
        self.action_preview.setShortcut(QKeySequence("F6"))
        self.action_preview.setStatusTip("预览转换后的字体效果")
        self.action_preview.triggered.connect(self._on_preview)
        
        # 帮助菜单动作
        self.action_about = QAction("关于(&A)", self)
        self.action_about.setStatusTip("关于 LVFontConv")
        self.action_about.triggered.connect(self._on_about)
        
        self.action_help = QAction("帮助文档(&H)", self)
        self.action_help.setShortcut(QKeySequence.StandardKey.HelpContents)
        self.action_help.setStatusTip("查看帮助文档")
        self.action_help.triggered.connect(self._on_help)
    
    def _create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)
        
        # 字体菜单
        font_menu = menubar.addMenu("字体(&O)")
        font_menu.addAction(self.action_add_font)
        font_menu.addAction(self.action_remove_font)
        
        # 转换菜单
        convert_menu = menubar.addMenu("转换(&C)")
        convert_menu.addAction(self.action_convert)
        convert_menu.addAction(self.action_preview)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction(self.action_help)
        help_menu.addSeparator()
        help_menu.addAction(self.action_about)
    
    def _create_toolbars(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setObjectName("mainToolbar")  # 设置对象名称以保存状态
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 添加常用操作
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_add_font)
        toolbar.addAction(self.action_remove_font)
        toolbar.addSeparator()
        toolbar.addAction(self.action_convert)
        toolbar.addAction(self.action_preview)
    
    def _init_ui(self):
        """初始化UI"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板 (字体列表)
        self.font_list_widget = FontListWidget()
        splitter.addWidget(self.font_list_widget)
        
        # 右侧面板 (配置)
        self.config_widget = ConfigWidget()
        splitter.addWidget(self.config_widget)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 连接字体列表信号
        self.font_list_widget.font_added.connect(self._on_font_list_changed)
        self.font_list_widget.font_removed.connect(self._on_font_list_changed)
        self.font_list_widget.font_changed.connect(self._on_font_list_changed)
        
        # 连接配置变化信号
        self.config_widget.config_changed.connect(self._on_config_changed)
        
        # 连接菜单/工具栏动作到字体列表组件的内部方法
        self.action_add_font.triggered.connect(self.font_list_widget._on_add_font)
        self.action_remove_font.triggered.connect(self.font_list_widget._on_remove_font)
    
    def _create_statusbar(self):
        """创建状态栏"""
        statusbar = QStatusBar()
        statusbar.showMessage("就绪")
        self.setStatusBar(statusbar)
    
    # ========== 事件处理 ==========
    
    def _on_new_project(self):
        """新建项目"""
        logger.info("新建项目")
        # TODO: 实现新建项目逻辑
        self.statusBar().showMessage("新建项目", 2000)
    
    def _on_open_project(self):
        """打开项目"""
        logger.info("打开项目")
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "打开项目",
            "",
            "LVFontConv 项目 (*.lvproj);;所有文件 (*)"
        )
        if filename:
            logger.info(f"打开项目: {filename}")
            # TODO: 实现打开项目逻辑
            self.statusBar().showMessage(f"已打开: {filename}", 2000)
    
    def _on_save_project(self):
        """保存项目"""
        logger.info("保存项目")
        # TODO: 实现保存项目逻辑
        self.statusBar().showMessage("项目已保存", 2000)
    
    def _on_save_project_as(self):
        """另存为项目"""
        logger.info("另存为项目")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "另存为项目",
            "",
            "LVFontConv 项目 (*.lvproj);;所有文件 (*)"
        )
        if filename:
            logger.info(f"另存为: {filename}")
            # TODO: 实现另存为逻辑
            self.statusBar().showMessage(f"已保存到: {filename}", 2000)
    
    def _on_font_list_changed(self):
        """字体列表变化"""
        fonts = self.font_list_widget.get_font_sources()
        count = len(fonts)
        
        # 更新状态栏
        if count == 0:
            self.statusBar().showMessage("没有字体", 2000)
        else:
            total_chars = sum(font.char_count for font in fonts)
            self.statusBar().showMessage(
                f"已添加 {count} 个字体，共 {total_chars} 个字符",
                2000
            )
        
        # 更新操作按钮状态
        has_fonts = count > 0
        self.action_remove_font.setEnabled(has_fonts)
        self.action_convert.setEnabled(has_fonts)
        self.action_preview.setEnabled(has_fonts)
        
        logger.info(f"字体列表更新: {count} 个字体")
    
    def _on_config_changed(self):
        """配置变化"""
        config = self.config_widget.get_config()
        logger.debug(f"配置更新: 大小={config.font_size}, BPP={config.bpp}, 格式={config.output_format}")
    
    def _on_convert(self):
        """开始转换"""
        # 获取字体列表和配置
        fonts = self.font_list_widget.get_font_sources()
        config = self.config_widget.get_config()
        
        if not fonts:
            QMessageBox.warning(
                self,
                "无法转换",
                "请先添加至少一个字体文件。"
            )
            return
        
        # 验证配置
        if not config.output_name.strip():
            QMessageBox.warning(
                self,
                "配置错误",
                "请设置输出文件名。"
            )
            return
        
        logger.info(f"开始转换 {len(fonts)} 个字体")
        
        # 显示转换对话框
        success = ConvertDialog.show_and_convert(fonts, config, self)
        
        if success:
            self.statusBar().showMessage("转换成功完成", 3000)
            logger.info("转换成功")
        else:
            self.statusBar().showMessage("转换未完成", 3000)
            logger.info("转换未完成或已取消")
    
    def _on_preview(self):
        """预览字体"""
        logger.info("预览字体")
        # TODO: 实现预览逻辑
        self.statusBar().showMessage("显示预览", 2000)
    
    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于 LVFontConv",
            "<h2>LVFontConv</h2>"
            "<p>LVGL 字体转换工具 Python 版</p>"
            "<p>版本: 1.0.0</p>"
            "<p>基于 PyQt6 开发</p>"
            "<p>© 2025 LVGL</p>"
        )
    
    def _on_help(self):
        """帮助文档"""
        logger.info("打开帮助文档")
        QMessageBox.information(
            self,
            "帮助",
            "帮助文档功能待实现"
        )
    
    # ========== 窗口状态管理 ==========
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        # 恢复窗口大小和位置
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复窗口状态（最大化等）
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口状态
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        logger.info("应用程序关闭")
        event.accept()
