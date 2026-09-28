"""
styles.py
Tema modern (dark, flat, rounded corner) untuk seluruh aplikasi StreamPad.
"""

DARK_THEME = """
QWidget {
    background-color: #1e1f26;
    color: #e6e6e6;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1e1f26;
}
QLabel#Header {
    font-size: 22px;
    font-weight: 700;
    padding: 6px 0;
    color: #ffffff;
}
QPushButton {
    background-color: #2b2d3a;
    border: 1px solid #3a3d4d;
    border-radius: 10px;
    padding: 8px 14px;
}
QPushButton:hover {
    background-color: #343747;
    border: 1px solid #5865f2;
}
QPushButton:pressed {
    background-color: #5865f2;
}
QPushButton#DeckButton {
    min-width: 120px;
    min-height: 96px;
    font-weight: 600;
    font-size: 14px;
    border-radius: 16px;
}
QPushButton#ToolbarButton {
    background-color: #5865f2;
    border: none;
    font-weight: 600;
    color: white;
    padding: 8px 16px;
}
QPushButton#ToolbarButton:hover {
    background-color: #707bf7;
}
QLineEdit, QComboBox, QDoubleSpinBox {
    background-color: #2b2d3a;
    border: 1px solid #3a3d4d;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #5865f2;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #3a3d4d;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #5865f2;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QStatusBar {
    background-color: #16171d;
    color: #a9adc1;
}
QDialog {
    background-color: #1e1f26;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background: #1e1f26;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #3a3d4d;
    border-radius: 5px;
    min-height: 24px;
}
"""
