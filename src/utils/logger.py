"""
Logger module for LVFontConv
Provides logging functionality with file and console output
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """
    Centralized logging manager for LVFontConv
    
    Supports both console and file logging with different log levels.
    """
    
    _instance: Optional['Logger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one logger instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger"""
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True
    
    def _setup_logger(self) -> None:
        """Setup the logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / '.lvfontconv' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        log_filename = f"lvfontconv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file = log_dir / log_filename
        
        # Create logger
        self.logger = logging.getLogger('LVFontConv')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (DEBUG and above)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Logger initialized. Log file: {log_file}")
        
        # Keep only last 10 log files
        self._cleanup_old_logs(log_dir, keep=10)
    
    def _cleanup_old_logs(self, log_dir: Path, keep: int = 10) -> None:
        """
        Remove old log files, keeping only the most recent ones
        
        Args:
            log_dir: Directory containing log files
            keep: Number of recent log files to keep
        """
        try:
            log_files = sorted(
                log_dir.glob('lvfontconv_*.log'),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            for old_log in log_files[keep:]:
                try:
                    old_log.unlink()
                    self.logger.debug(f"Deleted old log file: {old_log}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete old log file {old_log}: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old logs: {e}")
    
    def debug(self, message: str) -> None:
        """Log a debug message"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log an info message"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message"""
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        """Log an exception with traceback"""
        self.logger.exception(message)
    
    def set_console_level(self, level: int) -> None:
        """
        Set the console log level
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
                self.logger.info(f"Console log level set to {logging.getLevelName(level)}")
                break
    
    def set_file_level(self, level: int) -> None:
        """
        Set the file log level
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
                self.logger.info(f"File log level set to {logging.getLevelName(level)}")
                break


# Global logger instance
_logger = Logger()


# Convenience functions
def debug(message: str) -> None:
    """Log a debug message"""
    _logger.debug(message)


def info(message: str) -> None:
    """Log an info message"""
    _logger.info(message)


def warning(message: str) -> None:
    """Log a warning message"""
    _logger.warning(message)


def error(message: str) -> None:
    """Log an error message"""
    _logger.error(message)


def critical(message: str) -> None:
    """Log a critical message"""
    _logger.critical(message)


def exception(message: str) -> None:
    """Log an exception with traceback"""
    _logger.exception(message)


def get_logger() -> Logger:
    """Get the global logger instance"""
    return _logger


if __name__ == "__main__":
    # Test the logger
    logger = get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Caught an exception")
