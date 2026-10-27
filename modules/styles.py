"""
styles.py
QSS untuk elemen standar (teks, kolom input, slider, scrollbar, dialog bawaan).
Panel, tombol, tab, dan toggle TIDAK memakai QSS: semuanya digambar manual di
modules/glass.py supaya bisa memakai efek Liquid Glass.
"""

DARK_THEME = """
QWidget {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #f4f4f5;
}
QLabel { background: transparent; }

#Title { font-size: 32px; font-weight: 700; letter-spacing: -0.5px; color: #ffffff; }
#Subtitle { color: rgba(255, 255, 255, 0.55); font-size: 12px; }
#Status { color: rgba(255, 255, 255, 0.55); font-size: 12px; }
#SectionTitle { font-size: 12px; font-weight: 700; letter-spacing: 1.5px; color: rgba(255,255,255,0.45); padding-top: 8px; }
#Hint { color: rgba(255, 255, 255, 0.45); font-size: 12px; }
#DialogTitle { font-size: 20px; font-weight: 700; color: #ffffff; padding-bottom: 6px; }
#FieldLabel { color: rgba(255, 255, 255, 0.55); font-size: 11px; font-weight: 700; letter-spacing: 1px; }
#EmptyTitle { font-size: 19px; font-weight: 700; color: #ffffff; }
#EmptyText { color: rgba(255, 255, 255, 0.55); font-size: 13px; }

/* Kolom input kaca */
QLineEdit {
    background: rgba(255, 255, 255, 0.075);
    border: 1px solid rgba(255, 255, 255, 0.17);
    border-radius: 16px;
    padding: 10px 16px;
    selection-background-color: rgba(255, 255, 255, 0.30);
}
QLineEdit:focus {
    background: rgba(255, 255, 255, 0.11);
    border: 1px solid rgba(255, 255, 255, 0.55);
}
QLineEdit:read-only { color: rgba(255, 255, 255, 0.75); }

QComboBox {
    background: rgba(255, 255, 255, 0.075);
    border: 1px solid rgba(255, 255, 255, 0.17);
    border-radius: 16px;
    padding: 9px 16px;
}
QComboBox:hover { background: rgba(255, 255, 255, 0.11); }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView {
    background: #141416;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 12px;
    padding: 4px;
    selection-background-color: rgba(255, 255, 255, 0.18);
    outline: none;
}

/* Slider kaca */
QSlider::groove:horizontal {
    height: 8px;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 4px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,255,255,0.55), stop:1 rgba(255,255,255,0.85));
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background: qradialgradient(cx:0.4, cy:0.35, radius:0.8, fx:0.35, fy:0.3,
        stop:0 #ffffff, stop:1 #d6d6d6);
    border: 1px solid rgba(255, 255, 255, 0.85);
    width: 20px;
    height: 20px;
    margin: -7px 0;
    border-radius: 11px;
}

/* Scrollbar */
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.20);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.34); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

/* Dialog bawaan Qt (konfirmasi hapus, input nama profile) */
QMessageBox, QInputDialog { background: #0e0e10; }
QMessageBox QPushButton, QInputDialog QPushButton {
    background: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 14px;
    padding: 8px 20px;
    min-width: 70px;
}
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
    background: rgba(255, 255, 255, 0.18);
}
QMessageBox QPushButton:default, QInputDialog QPushButton:default {
    background: rgba(255, 255, 255, 0.28);
    border: 1px solid rgba(255, 255, 255, 0.45);
}

QToolTip {
    background: #1a1a1d;
    color: #f4f4f5;
    border: 1px solid rgba(255, 255, 255, 0.18);
    padding: 4px 8px;
}
"""
