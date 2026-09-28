"""
styles.py
Tema modern untuk StreamPad: gelap, gradasi halus, sudut membulat.
"""

DARK_THEME = """
QWidget {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #e8eaf2;
}
QMainWindow, QDialog { background: #12141c; }
#Root {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #171a27, stop:1 #0c0d12);
}
QLabel { background: transparent; }

#Title { font-size: 28px; font-weight: 700; color: #ffffff; }
#Subtitle { color: #7d8299; font-size: 13px; }
#Hint { color: #7d8299; font-size: 12px; }
#DialogTitle { font-size: 19px; font-weight: 700; color: #ffffff; padding-bottom: 4px; }
#FieldLabel { color: #8b90a8; font-size: 11px; font-weight: 700; letter-spacing: 1px; padding-top: 6px; }
#EmptyTitle { font-size: 18px; font-weight: 700; color: #ffffff; }
#EmptyText { color: #7d8299; font-size: 13px; }

QPushButton {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 9px 16px;
}
QPushButton:hover { background: rgba(255, 255, 255, 0.11); }
QPushButton:pressed { background: rgba(255, 255, 255, 0.04); }
QPushButton:disabled { color: #6b7088; }

#Primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6470ff, stop:1 #8b5cf6);
    border: none;
    color: #ffffff;
    font-weight: 600;
    padding: 10px 20px;
}
#Primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7883ff, stop:1 #9d75f8);
}
#Primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #535ee8, stop:1 #7c4ce6);
}

#Pill { border-radius: 18px; padding: 9px 18px; }
#Pill:checked {
    background: rgba(100, 112, 255, 0.22);
    border: 1px solid #6470ff;
    color: #cfd3ff;
}

#Seg { border-radius: 12px; padding: 11px 14px; }
#Seg:checked {
    background: #5865f2;
    border: 1px solid #7b86ff;
    color: #ffffff;
    font-weight: 600;
}

#Danger {
    background: rgba(237, 66, 69, 0.14);
    border: 1px solid rgba(237, 66, 69, 0.45);
    color: #ff8f91;
}
#Danger:hover { background: rgba(237, 66, 69, 0.25); }

QLineEdit {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 9px 12px;
    selection-background-color: #5865f2;
}
QLineEdit:focus { border: 1px solid #6470ff; }
QLineEdit:read-only { color: #b6bbd0; }

QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 0.10);
    border-radius: 3px;
}
QSlider::sub-page:horizontal { background: #6470ff; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #ffffff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.16);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.28); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QToolTip {
    background: #1c1f2e;
    color: #e8eaf2;
    border: 1px solid #2c3046;
    padding: 4px 8px;
}
"""
