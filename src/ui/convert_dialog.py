"""
转换对话框 - 显示字体转换进度和日志输出

提供进度条、日志输出、取消按钮和成功/失败状态显示。
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QFont

from core.simple_converter import SimpleFontConverter
from utils.logger import get_logger

logger = get_logger()


class ConvertThread(QThread):
    """转换工作线程"""
    
    # 信号
    progress_updated = pyqtSignal(int, str)  # (进度, 消息)
    log_message = pyqtSignal(str)  # 日志消息
    conversion_finished = pyqtSignal(bool, str)  # (成功, 消息)
    
    def __init__(self, fonts, config):
        super().__init__()
        self.fonts = fonts  # 字体源列表
        self.config = config  # 转换配置
        self.is_cancelled = False
    
    def run(self):
        """执行转换任务"""
        try:
            self.log_message.emit("=" * 60)
            self.log_message.emit("开始字体转换")
            self.log_message.emit("=" * 60)
            
            # 显示配置信息
            self.log_message.emit(f"字体数量: {len(self.fonts)}")
            self.log_message.emit(f"字体大小: {self.config.font_size}px")
            self.log_message.emit(f"位深度: {self.config.bpp} bit")
            self.log_message.emit(f"LVGL 版本: {self.config.lvgl_version}")
            self.log_message.emit(f"输出格式: {self.config.output_format}")
            self.log_message.emit(f"压缩方式: {self.config.compression}")
            self.log_message.emit("")
            
            total_fonts = len(self.fonts)
            
            # 创建转换器
            converter = SimpleFontConverter()
            
            # 设置进度回调
            def progress_callback(message: str, percentage: int):
                self.log_message.emit(f"  {message}")
            
            converter.set_progress_callback(progress_callback)
            
            for i, font in enumerate(self.fonts):
                if self.is_cancelled:
                    self.log_message.emit("\n转换已取消")
                    self.conversion_finished.emit(False, "用户取消操作")
                    return
                
                # 更新进度
                progress = int((i / total_fonts) * 100)
                self.progress_updated.emit(progress, f"处理字体 {i+1}/{total_fonts}")
                
                # 显示字体信息
                self.log_message.emit(f"[{i+1}/{total_fonts}] 处理字体: {font.display_name}")
                self.log_message.emit(f"  路径: {font.path}")
                self.log_message.emit(f"  范围: {', '.join(font.ranges) if font.ranges else '无'}")
                self.log_message.emit(f"  符号: {font.symbols if font.symbols else '无'}")
                self.log_message.emit(f"  字符数: {font.char_count}")
                self.log_message.emit("")
                
                # 执行转换
                output_path = f"/tmp/{self.config.output_name}_{i}"  # TODO: 使用实际输出路径
                
                success = converter.convert_font(
                    font_path=font.path,
                    ranges=font.ranges,
                    symbols=font.symbols,
                    size=self.config.font_size,
                    bpp=self.config.bpp,
                    output_path=output_path,
                    compression=self.config.compression,
                    lvgl_version=self.config.lvgl_version,
                    no_kerning=self.config.no_kerning,
                    lcd_mode=self.config.lcd,
                    lcd_v_mode=self.config.lcd_v
                )
                
                if success:
                    self.log_message.emit(f"  ✓ 转换完成: {output_path}.c")
                else:
                    self.log_message.emit(f"  ✗ 转换失败")
                    self.conversion_finished.emit(False, f"字体 {font.display_name} 转换失败")
                    return
                
                self.log_message.emit("")
            
            # 完成
            self.progress_updated.emit(100, "转换完成")
            self.log_message.emit("=" * 60)
            self.log_message.emit("所有字体转换完成!")
            self.log_message.emit("=" * 60)
            self.conversion_finished.emit(True, f"成功转换 {total_fonts} 个字体")
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            self.log_message.emit(f"\n错误: {error_msg}")
            self.conversion_finished.emit(False, error_msg)
            logger.error(error_msg, exc_info=True)
    
    def cancel(self):
        """取消转换"""
        self.is_cancelled = True
        logger.info("转换线程取消请求")


class ConvertDialog(QDialog):
    """转换对话框"""
    
    def __init__(self, fonts, config, parent=None):
        super().__init__(parent)
        self.fonts = fonts
        self.config = config
        self.convert_thread: Optional[ConvertThread] = None
        self.is_finished = False
        
        self._init_ui()
        logger.info("转换对话框初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("字体转换")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 状态标签
        self.status_label = QLabel("准备转换...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 日志输出
        log_label = QLabel("转换日志:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 9))
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def start_conversion(self):
        """开始转换"""
        # 创建并启动转换线程
        self.convert_thread = ConvertThread(self.fonts, self.config)
        
        # 连接信号
        self.convert_thread.progress_updated.connect(self._on_progress_updated)
        self.convert_thread.log_message.connect(self._on_log_message)
        self.convert_thread.conversion_finished.connect(self._on_conversion_finished)
        
        # 启动线程
        self.convert_thread.start()
        logger.info("转换线程已启动")
    
    def _on_progress_updated(self, value: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def _on_log_message(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def _on_conversion_finished(self, success: bool, message: str):
        """转换完成"""
        self.is_finished = True
        
        if success:
            self.status_label.setText("✓ " + message)
            self.status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: green;"
            )
            logger.info(f"转换成功: {message}")
        else:
            self.status_label.setText("✗ " + message)
            self.status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: red;"
            )
            logger.error(f"转换失败: {message}")
        
        # 更新按钮状态
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        self.close_button.setFocus()
    
    def _on_cancel(self):
        """取消转换"""
        if self.is_finished:
            self.reject()
            return
        
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消转换吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.convert_thread and self.convert_thread.isRunning():
                self.status_label.setText("正在取消...")
                self.cancel_button.setEnabled(False)
                self.convert_thread.cancel()
                logger.info("用户取消转换")
    
    def closeEvent(self, event):
        """关闭事件"""
        if not self.is_finished and self.convert_thread and self.convert_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "转换正在进行中，确定要关闭吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.convert_thread.cancel()
                self.convert_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    @staticmethod
    def show_and_convert(fonts, config, parent=None) -> bool:
        """显示对话框并执行转换
        
        Args:
            fonts: 字体源列表
            config: 转换配置
            parent: 父窗口
            
        Returns:
            bool: 转换是否成功
        """
        dialog = ConvertDialog(fonts, config, parent)
        
        # 延迟启动转换(让对话框先显示)
        QTimer.singleShot(100, dialog.start_conversion)
        
        result = dialog.exec()
        return dialog.is_finished and result == QDialog.DialogCode.Accepted
