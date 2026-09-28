"""
gui.py
Antarmuka modern StreamPad: kartu tombol dengan efek glow saat hover,
toggle Jalankan/Edit dengan indikator geser beranimasi, dan dialog
konfigurasi yang fade-in. Aksi tombol dipangkas jadi dua: Putar Suara
dan Buka Aplikasi (biar simpel, sisanya dikombinasikan dengan app lain).
"""
import os
import subprocess
import sys
import uuid

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QRect
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QLineEdit, QComboBox, QFileDialog, QSlider,
    QDialogButtonBox, QMessageBox, QColorDialog, QScrollArea, QButtonGroup,
    QGraphicsDropShadowEffect, QFormLayout
)

from modules import config_manager
from modules.audio_manager import AudioManager
from modules.hotkey_manager import HotkeyManager

ACTION_LABELS = {"sound": "Putar Suara", "app": "Buka Aplikasi"}
ACTION_ICONS = {"sound": "🔊", "app": "🚀"}


def launch_app(path: str, args: str):
    if not path:
        return
    try:
        parts = [path] + ([a for a in args.split(" ") if a] if args else [])
        if sys.platform == "win32":
            os.startfile(path) if not args else subprocess.Popen(parts, shell=False)
        else:
            subprocess.Popen(parts)
    except Exception as e:
        print(f"Gagal membuka aplikasi '{path}': {e}")


# ---------------------------------------------------------------- Segmented toggle
class SegmentedToggle(QWidget):
    """Toggle 'Jalankan / Edit' dengan indikator pill yang meluncur beranimasi."""
    toggled = Signal(bool)  # True = edit mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._indicator = QWidget(self)
        self._indicator.setObjectName("SegIndicator")
        self._indicator.setStyleSheet(
            "#SegIndicator { background: #5865f2; border-radius: 10px; }"
        )
        self._indicator.lower()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_run = QPushButton("▶  Jalankan")
        self.btn_edit = QPushButton("✎  Edit")
        for b in (self.btn_run, self.btn_edit):
            b.setObjectName("Seg")
            b.setCheckable(True)
            b.setFlat(True)
            b.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(b)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.btn_run, 0)
        self.group.addButton(self.btn_edit, 1)
        self.btn_run.setChecked(True)
        self.group.idClicked.connect(self._on_clicked)

        self.setStyleSheet(
            "SegmentedToggle { background: rgba(255,255,255,0.05);"
            " border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; }"
        )

        self._anim = QPropertyAnimation(self._indicator, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        QTimer.singleShot(0, lambda: self._move_indicator(animate=False))

    def _on_clicked(self, idx):
        self._move_indicator(animate=True)
        self.toggled.emit(idx == 1)

    def _move_indicator(self, animate: bool):
        target = self.btn_edit if self.group.checkedId() == 1 else self.btn_run
        rect = QRect(4, 4, target.width() - 8, target.height() - 8)
        rect.moveTop(4)
        rect.moveLeft(target.x() + 4)
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._indicator.geometry())
            self._anim.setEndValue(rect)
            self._anim.start()
        else:
            self._indicator.setGeometry(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, lambda: self._move_indicator(animate=False))


# ---------------------------------------------------------------- Deck button
class DeckButton(QPushButton):
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("DeckButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.data = data

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(0)
        self.shadow.setOffset(0, 0)
        self._accent = QColor(data.get("color", "#5865f2"))
        self.shadow.setColor(self._accent)
        self.setGraphicsEffect(self.shadow)

        self._glow = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self._glow.setDuration(180)
        self._glow.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.refresh()

    def refresh(self):
        icon = ACTION_ICONS.get(self.data.get("action_type", "sound"), "🔘")
        label = self.data.get("label", "Tombol")
        hotkey = self.data.get("hotkey", "")
        text = f"{icon}\n{label}" + (f"\n[{hotkey}]" if hotkey else "")
        self.setText(text)

        color = self.data.get("color", "#5865f2")
        self._accent = QColor(color)
        self.shadow.setColor(self._accent)
        darker = QColor(color).darker(160).name()
        self.setStyleSheet(
            f"""
            QPushButton#DeckButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {darker});
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
                min-width: 128px;
                min-height: 104px;
                font-weight: 600;
                font-size: 13px;
                color: white;
                padding: 8px;
            }}
            """
        )

    def _animate_glow(self, to_value: float):
        self._glow.stop()
        self._glow.setStartValue(self.shadow.blurRadius())
        self._glow.setEndValue(to_value)
        self._glow.start()

    def enterEvent(self, event):
        self._animate_glow(28)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_glow(0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._animate_glow(45)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        target = 28 if self.underMouse() else 0
        self._animate_glow(target)
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------- Hotkey capture
class HotkeyCaptureButton(QPushButton):
    captured = Signal(str)
    DEFAULT_TEXT = "🎙  Rekam tombol (DumbPad / keyboard)"

    def __init__(self, hotkey_manager: HotkeyManager, line_edit: QLineEdit, parent=None):
        super().__init__(self.DEFAULT_TEXT, parent)
        self.setObjectName("Pill")
        self.hotkey_manager = hotkey_manager
        self.line_edit = line_edit
        self.clicked.connect(self._start_capture)
        self.captured.connect(self._on_captured)

    def _start_capture(self):
        self.setText("Menunggu... tekan tombolnya sekarang")
        self.setEnabled(False)
        # callback dari thread library keyboard -> lewat signal ke thread utama Qt
        self.hotkey_manager.capture_next_key(lambda key_name: self.captured.emit(key_name))

    def _on_captured(self, key_name):
        self.line_edit.setText(key_name)
        self.setText(self.DEFAULT_TEXT)
        self.setEnabled(True)


# ---------------------------------------------------------------- Config dialog
class ButtonConfigDialog(QDialog):
    def __init__(self, button_data: dict, hotkey_manager: HotkeyManager, parent=None, allow_delete: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Tombol")
        self.setMinimumWidth(440)
        self.button_data = dict(button_data)
        self.hotkey_manager = hotkey_manager
        self.delete_requested = False

        outer = QVBoxLayout(self)
        outer.setSpacing(4)
        title = QLabel("Konfigurasi Tombol")
        title.setObjectName("DialogTitle")
        outer.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        outer.addLayout(form)

        def field_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("FieldLabel")
            return lbl

        self.label_edit = QLineEdit(self.button_data.get("label", ""))
        form.addRow(field_label("NAMA TOMBOL"), self.label_edit)

        self.action_combo = QComboBox()
        for key, text in ACTION_LABELS.items():
            self.action_combo.addItem(f"{ACTION_ICONS[key]}  {text}", key)
        current_index = self.action_combo.findData(self.button_data.get("action_type", "sound"))
        self.action_combo.setCurrentIndex(max(0, current_index))
        self.action_combo.currentIndexChanged.connect(self._update_visible_fields)
        form.addRow(field_label("AKSI"), self.action_combo)

        # --- Sound fields ---
        sound_row = QHBoxLayout()
        self.sound_path_edit = QLineEdit(self.button_data.get("sound_path", ""))
        self.sound_path_edit.setReadOnly(True)
        sound_browse = QPushButton("Pilih File")
        sound_browse.clicked.connect(self._browse_sound)
        sound_row.addWidget(self.sound_path_edit)
        sound_row.addWidget(sound_browse)
        self.sound_row_widget = QWidget()
        self.sound_row_widget.setLayout(sound_row)
        self.sound_row_label = field_label("FILE SUARA")
        form.addRow(self.sound_row_label, self.sound_row_widget)

        self.sound_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sound_volume_slider.setRange(0, 100)
        self.sound_volume_slider.setValue(int(self.button_data.get("sound_volume", 1.0) * 100))
        self.sound_volume_label = field_label("VOLUME SUARA INI")
        form.addRow(self.sound_volume_label, self.sound_volume_slider)

        # --- App fields ---
        app_row = QHBoxLayout()
        self.app_path_edit = QLineEdit(self.button_data.get("app_path", ""))
        self.app_path_edit.setReadOnly(True)
        app_browse = QPushButton("Pilih File")
        app_browse.clicked.connect(self._browse_app)
        app_row.addWidget(self.app_path_edit)
        app_row.addWidget(app_browse)
        self.app_row_widget = QWidget()
        self.app_row_widget.setLayout(app_row)
        self.app_row_label = field_label("APLIKASI / FILE")
        form.addRow(self.app_row_label, self.app_row_widget)

        self.app_args_edit = QLineEdit(self.button_data.get("app_args", ""))
        self.app_args_edit.setPlaceholderText("opsional, misal: --fullscreen")
        self.app_args_label = field_label("ARGUMEN (OPSIONAL)")
        form.addRow(self.app_args_label, self.app_args_edit)

        # --- Hotkey ---
        hotkey_row = QHBoxLayout()
        self.hotkey_edit = QLineEdit(self.button_data.get("hotkey", ""))
        self.hotkey_edit.setReadOnly(True)
        self.hotkey_edit.setPlaceholderText("belum diatur")
        capture_btn = HotkeyCaptureButton(self.hotkey_manager, self.hotkey_edit)
        hotkey_row.addWidget(self.hotkey_edit)
        hotkey_row.addWidget(capture_btn)
        hotkey_widget = QWidget()
        hotkey_widget.setLayout(hotkey_row)
        form.addRow(field_label("HOTKEY DUMBPAD"), hotkey_widget)

        # --- Color ---
        color_row = QHBoxLayout()
        self.color_value = self.button_data.get("color", "#5865f2")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(28, 28)
        self._update_color_preview()
        color_btn = QPushButton("Pilih Warna")
        color_btn.clicked.connect(self._choose_color)
        color_row.addWidget(self.color_preview)
        color_row.addWidget(color_btn)
        color_row.addStretch()
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow(field_label("WARNA"), color_widget)

        # --- Buttons ---
        button_row = QHBoxLayout()
        if allow_delete:
            delete_btn = QPushButton("Hapus Tombol")
            delete_btn.setObjectName("Danger")
            delete_btn.clicked.connect(self._request_delete)
            button_row.addWidget(delete_btn)
        button_row.addStretch()

        cancel_btn = QPushButton("Batal")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Simpan")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self.accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        outer.addSpacing(6)
        outer.addLayout(button_row)

        self._update_visible_fields()

    def _request_delete(self):
        self.delete_requested = True
        self.accept()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(
            f"background-color: {self.color_value}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);"
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

    def _browse_app(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih Aplikasi / File", "", "All Files (*.*)")
        if path:
            self.app_path_edit.setText(path)

    def _update_visible_fields(self):
        action = self.action_combo.currentData()
        is_sound = action == "sound"
        is_app = action == "app"
        for w in (self.sound_row_label, self.sound_row_widget, self.sound_volume_label, self.sound_volume_slider):
            w.setVisible(is_sound)
        for w in (self.app_row_label, self.app_row_widget, self.app_args_label, self.app_args_edit):
            w.setVisible(is_app)

    def get_result(self) -> dict:
        data = dict(self.button_data)
        data["label"] = self.label_edit.text().strip() or "Tombol"
        data["action_type"] = self.action_combo.currentData()
        data["sound_path"] = self.sound_path_edit.text()
        data["sound_volume"] = self.sound_volume_slider.value() / 100.0
        data["app_path"] = self.app_path_edit.text()
        data["app_args"] = self.app_args_edit.text().strip()
        data["hotkey"] = self.hotkey_edit.text().strip()
        data["color"] = self.color_value
        return data

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._show_anim = anim


# ---------------------------------------------------------------- Main window
class MainWindow(QMainWindow):
    # Hotkey datang dari thread library keyboard; signal ini memindahkannya
    # ke thread utama Qt supaya audio & UI aman dijalankan.
    action_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.action_requested.connect(self._execute_action)
        self.setWindowTitle("StreamPad — Soundboard & Macro Deck untuk DumbPad")
        self.resize(960, 660)

        self.config = config_manager.load_config()
        self.audio_manager = AudioManager()
        self.hotkey_manager = HotkeyManager()
        self.edit_mode = False

        self._build_ui()
        self._register_all_hotkeys()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("StreamPad")
        title.setObjectName("Title")
        subtitle = QLabel("Soundboard & Macro Deck untuk DumbPad")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()

        self.toggle = SegmentedToggle()
        self.toggle.toggled.connect(self._set_edit_mode)
        header_row.addWidget(self.toggle)

        add_btn = QPushButton("＋  Tambah Tombol")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self._add_button)
        header_row.addWidget(add_btn)

        outer.addLayout(header_row)

        self.hint = QLabel()
        self.hint.setObjectName("Hint")
        outer.addWidget(self.hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(16)
        scroll.setWidget(self.grid_container)
        outer.addWidget(scroll)

        self._render_buttons()
        self._update_hint()

    def _update_hint(self):
        if self.edit_mode:
            self.hint.setText("Mode Edit — klik kartu tombol untuk mengubah atau menghapusnya.")
        else:
            self.hint.setText("Mode Jalankan — klik kartu tombol untuk memutar suara atau membuka aplikasi.")

    def _render_buttons(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        buttons = self.config.get("buttons", [])
        if not buttons:
            empty = QWidget()
            box = QVBoxLayout(empty)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon = QLabel("🎛️")
            icon.setStyleSheet("font-size: 48px;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t = QLabel("Belum ada tombol")
            t.setObjectName("EmptyTitle")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s = QLabel("Klik \"＋ Tambah Tombol\" untuk membuat tombol pertamamu.")
            s.setObjectName("EmptyText")
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(icon)
            box.addWidget(t)
            box.addWidget(s)
            self.grid.addWidget(empty, 0, 0)
            return

        columns = self.config.get("columns", 4)
        for index, button_data in enumerate(buttons):
            deck_btn = DeckButton(button_data)
            deck_btn.clicked.connect(lambda checked=False, b=button_data: self._on_button_clicked(b))
            row, col = divmod(index, columns)
            self.grid.addWidget(deck_btn, row, col)

    def _set_edit_mode(self, is_edit: bool):
        self.edit_mode = is_edit
        self._update_hint()

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
        elif action == "app":
            launch_app(button_data.get("app_path", ""), button_data.get("app_args", ""))

    def _delete_button(self, button_id: str):
        self.config["buttons"] = [b for b in self.config["buttons"] if b["id"] != button_id]
        self._save_and_refresh()

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
