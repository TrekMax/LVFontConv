"""
后台工作线程

提供后台任务处理,避免 UI 卡顿
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable, Any

from utils.logger import get_logger

logger = get_logger()


class WorkerThread(QThread):
    """通用后台工作线程"""
    
    # 信号
    finished = pyqtSignal(object)  # 任务完成,携带结果
    error = pyqtSignal(Exception)  # 任务出错,携带异常
    progress = pyqtSignal(int, str)  # 进度更新 (百分比, 消息)
    
    def __init__(self, task_func: Callable, *args, **kwargs):
        """
        初始化工作线程
        
        Args:
            task_func: 要执行的任务函数
            *args, **kwargs: 传递给任务函数的参数
        """
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """执行任务"""
        try:
            logger.debug(f"后台任务开始: {self.task_func.__name__}")
            result = self.task_func(*self.args, **self.kwargs)
            
            if not self._is_cancelled:
                self.finished.emit(result)
                logger.debug(f"后台任务完成: {self.task_func.__name__}")
        except Exception as e:
            logger.error(f"后台任务失败: {e}", exc_info=True)
            self.error.emit(e)
    
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True
        logger.debug("后台任务已取消")
    
    def is_cancelled(self):
        """检查是否已取消"""
        return self._is_cancelled
