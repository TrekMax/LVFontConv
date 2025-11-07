#!/usr/bin/env python3
"""
LVFontConv - Main Entry Point
A PyQt6-based font converter for LVGL with preview capabilities
"""

import sys
from PyQt6.QtWidgets import QApplication


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("LVFontConv")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("LVFontConv")
    
    # TODO: Import and create main window
    # from ui.main_window import MainWindow
    # window = MainWindow()
    # window.show()
    
    print("LVFontConv v0.1.0")
    print("Main window not implemented yet.")
    print("Project structure initialized successfully!")
    
    # For now, just exit
    return 0
    # return app.exec()


if __name__ == "__main__":
    sys.exit(main())
