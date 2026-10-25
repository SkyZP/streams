DARK_THEME = """
QMainWindow {
    background-color: #121212;
}
QWidget#GlassPanel {
    background-color: rgba(255, 255, 255, 5);
    border: 1px solid rgba(255, 255, 255, 15);
    border-radius: 12px;
}
QPushButton {
    background-color: rgba(255, 255, 255, 8);
    border: 1px solid rgba(255, 255, 255, 20);
    border-radius: 18px;
    color: #FFFFFF;
    padding: 8px 20px;
    font-size: 13px;
    min-width: 120px;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 15);
    border: 1px solid rgba(255, 255, 255, 35);
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 3);
}
QLabel {
    color: #FFFFFF;
}
QLineEdit, QComboBox, QSpinBox {
    background-color: rgba(0, 0, 0, 150);
    border: 1px solid rgba(255, 255, 255, 25);
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px;
}
"""