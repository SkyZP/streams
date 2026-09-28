"""
main.py
Entry point aplikasi StreamPad.

Cara pakai:
  - Saat development: python main.py
  - Setelah di-build (lihat README.md): tinggal double klik StreamPad.exe,
    tanpa perlu instalasi apa pun (portable).
"""
import sys
from PySide6.QtWidgets import QApplication

from modules.styles import DARK_THEME
from modules.gui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StreamPad")
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
