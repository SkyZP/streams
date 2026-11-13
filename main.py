"""
main.py
Entry point aplikasi StreamPad.

Cara pakai:
  - Saat development: python main.py
  - Setelah di-build (lihat README.md): tinggal double klik .exe hasilnya,
    tanpa perlu instalasi apa pun (portable).
"""
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from modules.styles import DARK_THEME
from modules.gui import MainWindow


def resource_path(relative_path: str) -> str:
    """
    Path ke file resource (misal ikon) yang tetap benar baik saat dijalankan
    dari source (python main.py) maupun setelah dibundel jadi .exe oleh
    PyInstaller (file diekstrak sementara ke folder sys._MEIPASS).
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StreamPad")
    app.setStyleSheet(DARK_THEME)

    icon_path = resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)  # ikon default untuk semua window (termasuk dialog)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(app_icon)  # ikon di title bar & taskbar
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
