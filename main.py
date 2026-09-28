import sys
import os
import json
import subprocess
import keyboard
import pygame
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QDialog, QLineEdit, QComboBox, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

pygame.mixer.init()

class EditDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Aksi")
        self.setFixedSize(400, 300)
        self.data = data
        self.new_path = data.get("path", "")

        layout = QVBoxLayout(self)

        self.name_input = QLineEdit(self.data.get("name", ""))
        layout.addWidget(QLabel("Nama Tombol:"))
        layout.addWidget(self.name_input)

        self.hotkey_input = QLineEdit(self.data.get("hotkey", ""))
        layout.addWidget(QLabel("Tombol Keyboard/Dumbpad:"))
        layout.addWidget(self.hotkey_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Putar Suara", "Buka Aplikasi"])
        self.type_combo.setCurrentText(self.data.get("type", "Putar Suara"))
        layout.addWidget(QLabel("Pilih Aksi:"))
        layout.addWidget(self.type_combo)

        self.file_label = QLabel(os.path.basename(self.new_path) if self.new_path else "Belum ada file")
        layout.addWidget(self.file_label)

        btn_browse = QPushButton("Cari File")
        btn_browse.clicked.connect(self.browse)
        layout.addWidget(btn_browse)

        btn_save = QPushButton("Simpan")
        btn_save.clicked.connect(self.accept_data)
        layout.addWidget(btn_save)

    def browse(self):
        action_type = self.type_combo.currentText()
        if action_type == "Putar Suara":
            path, _ = QFileDialog.getOpenFileName(self, "Pilih Audio", "", "Audio Files (*.wav *.ogg *.mp3)")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Pilih Aplikasi", "", "Executable (*.exe *.bat *.lnk)")
        if path:
            self.new_path = path
            self.file_label.setText(os.path.basename(path))

    def accept_data(self):
        self.data["name"] = self.name_input.text()
        self.data["hotkey"] = self.hotkey_input.text()
        self.data["type"] = self.type_combo.currentText()
        self.data["path"] = self.new_path
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamPad")
        self.resize(800, 600)

        self.edit_mode = False
        self.buttons_data = []
        self.ui_buttons = []
        self.config_file = "streampad_config.json"

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        top_layout = QHBoxLayout()
        title = QLabel("StreamPad")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        top_layout.addWidget(title)

        self.info_label = QLabel("Mode Edit OFF \u2192 klik untuk menjalankan aksi.")
        top_layout.addWidget(self.info_label)
        top_layout.addStretch()

        self.btn_edit = QPushButton("Mode Edit: OFF")
        self.btn_edit.clicked.connect(self.toggle_edit)
        top_layout.addWidget(self.btn_edit)

        btn_add = QPushButton("+ Tambah Tombol")
        btn_add.clicked.connect(lambda: self.add_button_data())
        top_layout.addWidget(btn_add)

        self.main_layout.addLayout(top_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; color: white; }
            QLabel { color: white; }
            QPushButton { background-color: #45475a; color: white; border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #585b70; }
            QLineEdit, QComboBox { background-color: #313244; color: white; border: 1px solid #45475a; padding: 5px; }
        """)

        self.load_config()

    def toggle_edit(self):
        self.edit_mode = not self.edit_mode
        self.btn_edit.setText("Mode Edit: ON" if self.edit_mode else "Mode Edit: OFF")
        self.info_label.setText("Mode Edit ON \u2192 klik tombol untuk mengubah/hapus." if self.edit_mode else "Mode Edit OFF \u2192 klik untuk menjalankan aksi.")
        if self.edit_mode:
            self.btn_edit.setStyleSheet("background-color: #89b4fa; color: black; border-radius: 5px; padding: 8px;")
        else:
            self.btn_edit.setStyleSheet("background-color: #45475a; color: white; border-radius: 5px; padding: 8px;")

    def add_button_data(self, data=None):
        if not data:
            data = {"name": "112", "hotkey": "", "type": "Putar Suara", "path": ""}
            self.buttons_data.append(data)
            self.save_config()
        self.render_buttons()

    def render_buttons(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        keyboard.unhook_all()
        self.ui_buttons.clear()

        for idx, data in enumerate(self.buttons_data):
            btn = QPushButton(f"{data['name']}\n[{data['hotkey']}]")
            btn.setFixedHeight(100)
            btn.setStyleSheet("""
                QPushButton { background-color: #5a1818; color: white; border-radius: 10px; font-size: 16px; font-weight: bold; }
                QPushButton:hover { background-color: #7a2020; }
            """)
            btn.clicked.connect(lambda checked, i=idx: self.handle_click(i))
            self.scroll_layout.addWidget(btn)
            self.ui_buttons.append(btn)

            if data["hotkey"] and data["path"]:
                try:
                    keyboard.add_hotkey(data["hotkey"], lambda d=data: self.execute_action(d))
                except:
                    pass

    def handle_click(self, idx):
        if self.edit_mode:
            dialog = EditDialog(self.buttons_data[idx], self)
            if dialog.exec():
                self.save_config()
                self.render_buttons()
        else:
            self.execute_action(self.buttons_data[idx])

    def execute_action(self, data):
        if not data["path"] or not os.path.exists(data["path"]):
            return
        if data["type"] == "Putar Suara":
            try:
                pygame.mixer.Sound(data["path"]).play()
            except:
                pass
        elif data["type"] == "Buka Aplikasi":
            try:
                if os.name == 'nt':
                    os.startfile(data["path"])
                else:
                    subprocess.Popen([data["path"]])
            except:
                pass

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.buttons_data, f)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.buttons_data = json.load(f)
            except:
                pass
        self.render_buttons()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("StreamPad")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
