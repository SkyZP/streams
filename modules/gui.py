"""
gui.py
Antarmuka utama StreamPad: grid tombol yang bisa dikustomisasi penuh,
mode edit, dan dialog konfigurasi per tombol (suara, volume, hotkey DumbPad).
"""
import uuid

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QFormLayout, QLineEdit, QComboBox, QFileDialog,
    QDoubleSpinBox, QDialogButtonBox, QMessageBox, QSlider, QColorDialog,
    QScrollArea
)

from modules import config_manager
from modules.audio_manager import AudioManager
from modules.volume_manager import VolumeManager
from modules.hotkey_manager import HotkeyManager

ACTION_LABELS = {
    "sound": "Putar Suara",
    "volume_up": "Volume Naik",
    "volume_down": "Volume Turun",
    "volume_mute": "Mute / Unmute",
    "volume_set": "Set Volume ke Level Tertentu",
}


class HotkeyCaptureButton(QPushButton):
    """Tombol untuk merekam hotkey berikutnya — bisa dari keyboard biasa ATAU DumbPad."""

    captured = Signal(str)

    def __init__(self, hotkey_manager: HotkeyManager, line_edit: QLineEdit, parent=None):
        super().__init__("Rekam tombol (tekan di DumbPad / keyboard)...", parent)
        self.hotkey_manager = hotkey_manager
        self.line_edit = line_edit
        self.clicked.connect(self._start_capture)
        self.captured.connect(self._on_captured)

    def _start_capture(self):
        self.setText("Menunggu... tekan tombolnya sekarang")
        self.setEnabled(False)
        # callback dipanggil dari thread library keyboard, jadi lewat signal
        self.hotkey_manager.capture_next_key(lambda key_name: self.captured.emit(key_name))

    def _on_captured(self, key_name):
        self.line_edit.setText(key_name)
        self.setText("Rekam tombol (tekan di DumbPad / keyboard)...")
        self.setEnabled(True)


class ButtonConfigDialog(QDialog):
    def __init__(self, button_data: dict, hotkey_manager: HotkeyManager, parent=None, allow_delete: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Tombol")
        self.setMinimumWidth(420)
        self.button_data = dict(button_data)
        self.hotkey_manager = hotkey_manager
        self.delete_requested = False

        layout = QFormLayout(self)

        self.label_edit = QLineEdit(self.button_data.get("label", ""))
        layout.addRow("Nama Tombol:", self.label_edit)

        self.action_combo = QComboBox()
        for key, text in ACTION_LABELS.items():
            self.action_combo.addItem(text, key)
        current_index = self.action_combo.findData(self.button_data.get("action_type", "sound"))
        self.action_combo.setCurrentIndex(max(0, current_index))
        self.action_combo.currentIndexChanged.connect(self._update_visible_fields)
        layout.addRow("Aksi:", self.action_combo)

        # --- Sound file ---
        sound_row = QHBoxLayout()
        self.sound_path_edit = QLineEdit(self.button_data.get("sound_path", ""))
        self.sound_path_edit.setReadOnly(True)
        browse_btn = QPushButton("Pilih File...")
        browse_btn.clicked.connect(self._browse_sound)
        sound_row.addWidget(self.sound_path_edit)
        sound_row.addWidget(browse_btn)
        self.sound_row_widget = QWidget()
        self.sound_row_widget.setLayout(sound_row)
        layout.addRow("File Suara:", self.sound_row_widget)

        self.sound_volume_spin = QDoubleSpinBox()
        self.sound_volume_spin.setRange(0.0, 1.0)
        self.sound_volume_spin.setSingleStep(0.05)
        self.sound_volume_spin.setValue(self.button_data.get("sound_volume", 1.0))
        layout.addRow("Volume Suara Ini (0-1):", self.sound_volume_spin)

        # --- Volume step (untuk volume_up/down) ---
        self.volume_step_spin = QDoubleSpinBox()
        self.volume_step_spin.setRange(0.01, 1.0)
        self.volume_step_spin.setSingleStep(0.01)
        self.volume_step_spin.setValue(self.button_data.get("volume_step", 0.05))
        layout.addRow("Step Volume (naik/turun):", self.volume_step_spin)

        # --- Volume level (untuk volume_set) ---
        self.volume_level_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_level_slider.setRange(0, 100)
        self.volume_level_slider.setValue(int(self.button_data.get("volume_level", 0.5) * 100))
        layout.addRow("Set Level Volume (%):", self.volume_level_slider)

        # --- Hotkey dari DumbPad ---
        hotkey_row = QHBoxLayout()
        self.hotkey_edit = QLineEdit(self.button_data.get("hotkey", ""))
        capture_btn = HotkeyCaptureButton(self.hotkey_manager, self.hotkey_edit)
        hotkey_row.addWidget(self.hotkey_edit)
        hotkey_row.addWidget(capture_btn)
        hotkey_widget = QWidget()
        hotkey_widget.setLayout(hotkey_row)
        layout.addRow("Hotkey (tombol DumbPad):", hotkey_widget)

        # --- Warna tombol ---
        color_row = QHBoxLayout()
        self.color_value = self.button_data.get("color", "#3a3f4b")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self._update_color_preview()
        color_btn = QPushButton("Pilih Warna")
        color_btn.clicked.connect(self._choose_color)
        color_row.addWidget(self.color_preview)
        color_row.addWidget(color_btn)
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        layout.addRow("Warna Tombol:", color_widget)

        button_row = QHBoxLayout()
        if allow_delete:
            delete_btn = QPushButton("Hapus Tombol")
            delete_btn.setStyleSheet("background-color: #a33; border: none;")
            delete_btn.clicked.connect(self._request_delete)
            button_row.addWidget(delete_btn)
        button_row.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_row.addWidget(buttons)
        layout.addRow(button_row)

        self._update_visible_fields()

    def _request_delete(self):
        self.delete_requested = True
        self.accept()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(
            f"background-color: {self.color_value}; border-radius: 4px; border: 1px solid #555;"
        )

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.color_value), self, "Pilih Warna Tombol")
        if color.isValid():
            self.color_value = color.name()
            self._update_color_preview()

    def _browse_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih File Suara", "", "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if path:
            self.sound_path_edit.setText(path)

    def _update_visible_fields(self):
        action = self.action_combo.currentData()
        self.sound_row_widget.setVisible(action == "sound")
        self.sound_volume_spin.setVisible(action == "sound")
        self.volume_step_spin.setVisible(action in ("volume_up", "volume_down"))
        self.volume_level_slider.setVisible(action == "volume_set")

    def get_result(self) -> dict:
        data = dict(self.button_data)
        data["label"] = self.label_edit.text().strip() or "Tombol"
        data["action_type"] = self.action_combo.currentData()
        data["sound_path"] = self.sound_path_edit.text()
        data["sound_volume"] = self.sound_volume_spin.value()
        data["volume_step"] = self.volume_step_spin.value()
        data["volume_level"] = self.volume_level_slider.value() / 100.0
        data["hotkey"] = self.hotkey_edit.text().strip()
        data["color"] = self.color_value
        return data


class DeckButton(QPushButton):
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("DeckButton")
        self.data = data
        self.refresh()

    def refresh(self):
        label = self.data.get("label", "Tombol")
        hotkey = self.data.get("hotkey", "")
        display = f"{label}\n[{hotkey}]" if hotkey else label
        self.setText(display)
        color = self.data.get("color", "#3a3f4b")
        self.setStyleSheet(
            f"""
            QPushButton#DeckButton {{
                background-color: {color};
                border-radius: 16px;
                min-width: 120px;
                min-height: 96px;
                font-weight: 600;
            }}
            QPushButton#DeckButton:hover {{
                border: 2px solid #5865f2;
            }}
            """
        )


class MainWindow(QMainWindow):
    # Hotkey datang dari thread library keyboard; signal ini memindahkannya
    # ke thread utama Qt supaya audio & UI aman dijalankan.
    action_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.action_requested.connect(self._execute_action)
        self.setWindowTitle("StreamPad — Soundboard & Macro Deck untuk DumbPad")
        self.resize(920, 640)

        self.config = config_manager.load_config()
        self.audio_manager = AudioManager()
        self.hotkey_manager = HotkeyManager()
        self.edit_mode = False

        try:
            self.volume_manager = VolumeManager()
        except Exception as e:
            self.volume_manager = None
            print(f"Peringatan: kontrol volume tidak tersedia di sistem ini ({e})")

        self._build_ui()
        self._register_all_hotkeys()

    # ---------------- UI ----------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        header_row = QHBoxLayout()
        title = QLabel("StreamPad")
        title.setObjectName("Header")
        header_row.addWidget(title)
        header_row.addStretch()

        self.edit_btn = QPushButton("Mode Edit: OFF")
        self.edit_btn.setObjectName("ToolbarButton")
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        header_row.addWidget(self.edit_btn)

        add_btn = QPushButton("+ Tambah Tombol")
        add_btn.setObjectName("ToolbarButton")
        add_btn.clicked.connect(self._add_button)
        header_row.addWidget(add_btn)

        root.addLayout(header_row)

        hint = QLabel(
            "Mode Edit ON → klik tombol untuk mengubah/hapus. Mode Edit OFF → klik untuk menjalankan aksi."
        )
        hint.setStyleSheet("color: #8b8fa3; font-size: 12px;")
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(14)
        scroll.setWidget(self.grid_container)
        root.addWidget(scroll)

        self.status_label = QLabel("")
        self.statusBar().addWidget(self.status_label)
        self._update_status()

        self._render_buttons()

    def _render_buttons(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        columns = self.config.get("columns", 4)
        for index, button_data in enumerate(self.config.get("buttons", [])):
            deck_btn = DeckButton(button_data)
            deck_btn.clicked.connect(lambda checked=False, b=button_data: self._on_button_clicked(b))
            row, col = divmod(index, columns)
            self.grid.addWidget(deck_btn, row, col)

    def _update_status(self):
        if self.volume_manager:
            vol = int(self.volume_manager.get_volume() * 100)
            muted = " (Muted)" if self.volume_manager.is_muted() else ""
            self.status_label.setText(f"Volume Sistem: {vol}%{muted}")
        else:
            self.status_label.setText("Kontrol volume tidak tersedia di sistem ini")

    # ---------------- Aksi tombol ----------------
    def _add_button(self):
        new_data = config_manager.new_button(str(uuid.uuid4()))
        dialog = ButtonConfigDialog(new_data, self.hotkey_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
            self.config.setdefault("buttons", []).append(result)
            self._save_and_refresh()

    def _on_button_clicked(self, button_data: dict):
        if self.edit_mode:
            dialog = ButtonConfigDialog(button_data, self.hotkey_manager, self, allow_delete=True)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                if dialog.delete_requested:
                    confirm = QMessageBox.question(
                        self, "Hapus Tombol", f"Hapus tombol '{button_data.get('label')}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        self._delete_button(button_data["id"])
                    return
                result = dialog.get_result()
                for i, b in enumerate(self.config["buttons"]):
                    if b["id"] == button_data["id"]:
                        self.config["buttons"][i] = result
                        break
                self._save_and_refresh()
            return

        self._execute_action(button_data)

    def _execute_action(self, button_data: dict):
        action = button_data.get("action_type")
        if action == "sound":
            self.audio_manager.play(button_data.get("sound_path", ""), button_data.get("sound_volume", 1.0))
        elif action == "volume_up" and self.volume_manager:
            self.volume_manager.change_volume(button_data.get("volume_step", 0.05))
        elif action == "volume_down" and self.volume_manager:
            self.volume_manager.change_volume(-button_data.get("volume_step", 0.05))
        elif action == "volume_mute" and self.volume_manager:
            self.volume_manager.toggle_mute()
        elif action == "volume_set" and self.volume_manager:
            self.volume_manager.set_volume(button_data.get("volume_level", 0.5))
        self._update_status()

    def _delete_button(self, button_id: str):
        self.config["buttons"] = [b for b in self.config["buttons"] if b["id"] != button_id]
        self._save_and_refresh()

    # ---------------- Mode edit ----------------
    def _toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.edit_btn.setText(f"Mode Edit: {'ON' if self.edit_mode else 'OFF'}")

    # ---------------- Hotkey global (termasuk dari DumbPad) ----------------
    def _register_all_hotkeys(self):
        self.hotkey_manager.unregister_all()
        for button_data in self.config.get("buttons", []):
            hotkey = button_data.get("hotkey")
            if hotkey:
                self.hotkey_manager.register(hotkey, lambda b=button_data: self.action_requested.emit(b))

    def _save_and_refresh(self):
        config_manager.save_config(self.config)
        self._render_buttons()
        self._register_all_hotkeys()

    def closeEvent(self, event):
        self.hotkey_manager.unregister_all()
        config_manager.save_config(self.config)
        super().closeEvent(event)
