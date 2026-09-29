"""
styles.py
Tema "glass dashboard" — pill nav melengkung, kartu kaca, glow lembut,
terinspirasi dari referensi dashboard modern.
"""

DARK_THEME = """
QWidget {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #e8eaf2;
}
QMainWindow, QDialog { background: #0b0c11; }
#Root { background: #0b0c11; }
QLabel { background: transparent; }

#Title { font-size: 26px; font-weight: 700; color: #ffffff; }
#Subtitle { color: #7d8299; font-size: 12px; }
#Hint { color: #6b7088; font-size: 12px; }
#DialogTitle { font-size: 18px; font-weight: 700; color: #ffffff; }
#FieldLabel { color: #8b90a8; font-size: 11px; font-weight: 700; letter-spacing: 1px; padding-top: 6px; }
#EmptyTitle { font-size: 18px; font-weight: 700; color: #ffffff; }
#EmptyText { color: #7d8299; font-size: 13px; }

/* Kartu kaca umum (nav pill, dialog panel, dsb) */
#GlassPill {
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
}
#GlassCard {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 20px;
}

QPushButton {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
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
    border-radius: 16px;
}
#Primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7883ff, stop:1 #9d75f8);
}
#Primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #535ee8, stop:1 #7c4ce6);
}

/* Item dalam pill nav (profile tabs, segmented toggle) */
#NavItem {
    background: transparent;
    border: none;
    border-radius: 16px;
    padding: 8px 16px;
    color: #9095ac;
    font-weight: 600;
}
#NavItem:hover { color: #e8eaf2; }
#NavItem:checked {
    background: #ffffff;
    color: #12131a;
}
#NavItemAccent:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6470ff, stop:1 #8b5cf6);
    color: #ffffff;
}
#NavAdd {
    background: rgba(255, 255, 255, 0.08);
    border: 1px dashed rgba(255, 255, 255, 0.25);
    border-radius: 16px;
    color: #c8cbe0;
    font-weight: 700;
    padding: 8px 14px;
}
#NavAdd:hover { background: rgba(255, 255, 255, 0.14); }

#Danger {
    background: rgba(237, 66, 69, 0.14);
    border: 1px solid rgba(237, 66, 69, 0.45);
    color: #ff8f91;
    border-radius: 14px;
}
#Danger:hover { background: rgba(237, 66, 69, 0.25); }

QLineEdit {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 12px;
    padding: 9px 12px;
    selection-background-color: #6470ff;
}
QLineEdit:focus { border: 1px solid #6470ff; }
QLineEdit:read-only { color: #b6bbd0; }

QComboBox {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 12px;
    padding: 8px 12px;
}
QComboBox QAbstractItemView {
    background: #171923;
    border: 1px solid rgba(255,255,255,0.1);
    selection-background-color: #6470ff;
    border-radius: 8px;
}

QSlider::groove:horizontal { height: 6px; background: rgba(255, 255, 255, 0.10); border-radius: 3px; }
QSlider::sub-page:horizontal { background: #6470ff; border-radius: 3px; }
QSlider::handle:horizontal { background: #ffffff; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.16); border-radius: 4px; min-height: 30px; min-width: 30px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: rgba(255, 255, 255, 0.28); }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QToolTip { background: #1c1f2e; color: #e8eaf2; border: 1px solid #2c3046; padding: 4px 8px; }
"""
