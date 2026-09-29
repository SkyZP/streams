"""
gui.py
Antarmuka StreamPad gaya "glass dashboard": pill nav yang solid (bukan
indikator melayang yang gampang meleset posisinya), kartu tombol dengan
glow saat hover, orb dekoratif di background, dan sistem Profile supaya
satu DumbPad bisa punya beberapa set tombol berbeda.
"""
import os
import subprocess
import sys
import uuid

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QUrl
from PySide6.QtGui import QColor
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QLineEdit, QComboBox, QFileDialog, QSlider,
    QMessageBox, QColorDialog, QScrollArea, QButtonGroup, QInputDialog,
    QGraphicsDropShadowEffect, QGraphicsBlurEffect, QFormLayout
)

from modules import config_manager
from modules.audio_manager import AudioManager
from modules.hotkey_manager import HotkeyManager

ACTION_LABELS = {"sound": "Putar Suara", "app": "Buka Aplikasi"}
ACTION_ICONS = {"sound": "🔊", "app": "🚀"}


def format_ms(ms: int) -> str:
    ms = max(0, int(ms))
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02d}"


def launch_app(path: str, args: str):
    if not path:
        return
    try:
        if sys.platform == "win32" and not args:
            os.startfile(path)
        else:
            parts = [path] + [a for a in args.split(" ") if a]
            subprocess.Popen(parts, shell=False)
    except Exception as e:
        print(f"Gagal membuka aplikasi '{path}': {e}")


# ---------------------------------------------------------------- Glow helpers
class GlowButton(QPushButton):
    """Tombol pill dengan glow halus saat hover — dipakai di nav & profile bar."""

    def __init__(self, text: str, object_name: str = "NavItem", glow_color: str = "#6470ff", parent=None):
        super().__init__(text, parent)
        self.setObjectName(object_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(glow_color))
        self.setGraphicsEffect(self._shadow)
        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _animate(self, value: float):
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(value)
        self._anim.start()

    def enterEvent(self, event):
        self._animate(16)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0)
        super().leaveEvent(event)


class GlowOrb(QWidget):
    """Bulatan blur lembut buat dekorasi background, seperti referensi dashboard."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet(f"background: {color}; border-radius: 140px;")
        self.setFixedSize(280, 280)
        blur = QGraphicsBlurEffect(self)
        blur.setBlurRadius(70)
        self.setGraphicsEffect(blur)


# ---------------------------------------------------------------- Segmented toggle
class SegmentedToggle(QWidget):
    """Toggle 'Jalankan / Edit' — dua pill solid dalam satu kapsul kaca."""
    toggled = Signal(bool)  # True = edit mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassPill")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.btn_run = GlowButton("▶  Jalankan", "NavItemAccent", "#6470ff")
        self.btn_edit = GlowButton("✎  Edit", "NavItemAccent", "#6470ff")
        for b in (self.btn_run, self.btn_edit):
            b.setCheckable(True)
            layout.addWidget(b)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.btn_run, 0)
        self.group.addButton(self.btn_edit, 1)
        self.btn_run.setChecked(True)
        self.group.idClicked.connect(lambda idx: self.toggled.emit(idx == 1))


# ---------------------------------------------------------------- Profile bar
class ProfileBar(QWidget):
    profile_changed = Signal(str)   # profile id
    manage_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        pill = QWidget()
        pill.setObjectName("GlassPill")
        self.pill_layout = QHBoxLayout(pill)
        self.pill_layout.setContentsMargins(4, 4, 4, 4)
        self.pill_layout.setSpacing(2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(46)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(pill)
        self.pill = pill
        outer.addWidget(scroll, 1)

        self.add_btn = GlowButton("＋ Profile", "NavAdd", "#6470ff")
        self.add_btn.clicked.connect(self._request_add)
        outer.addWidget(self.add_btn)

        self.manage_btn = GlowButton("⚙", "NavAdd", "#6470ff")
        self.manage_btn.setFixedWidth(44)
        self.manage_btn.clicked.connect(self.manage_requested.emit)
        outer.addWidget(self.manage_btn)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._on_add = None

    def _request_add(self):
        if self._on_add:
            self._on_add()

    def set_add_handler(self, fn):
        self._on_add = fn

    def populate(self, profiles: list, active_id: str):
        for b in self.group.buttons():
            self.group.removeButton(b)
        while self.pill_layout.count():
            item = self.pill_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for profile in profiles:
            btn = GlowButton(profile["name"], "NavItem", "#6470ff")
            btn.setCheckable(True)
            btn.setChecked(profile["id"] == active_id)
            btn.clicked.connect(lambda checked=False, pid=profile["id"]: self.profile_changed.emit(pid))
            self.group.addButton(btn)
            self.pill_layout.addWidget(btn)


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
        self.shadow.setColor(QColor(data.get("color", "#6470ff")))
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

        color = self.data.get("color", "#6470ff")
        self.shadow.setColor(QColor(color))
        darker = QColor(color).darker(160).name()
        self.setStyleSheet(
            f"""
            QPushButton#DeckButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {color}, stop:1 {darker});
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 20px;
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
        self._animate_glow(30)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_glow(0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._animate_glow(48)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._animate_glow(30 if self.underMouse() else 0)
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------- Hotkey capture
class HotkeyCaptureButton(QPushButton):
    captured = Signal(str)
    DEFAULT_TEXT = "🎙  Rekam tombol (DumbPad / keyboard)"

    def __init__(self, hotkey_manager: HotkeyManager, line_edit: QLineEdit, parent=None):
        super().__init__(self.DEFAULT_TEXT, parent)
        self.hotkey_manager = hotkey_manager
        self.line_edit = line_edit
        self.clicked.connect(self._start_capture)
        self.captured.connect(self._on_captured)

    def _start_capture(self):
        self.setText("Menunggu... tekan tombolnya sekarang")
        self.setEnabled(False)
        self.hotkey_manager.capture_next_key(lambda key_name: self.captured.emit(key_name))

    def _on_captured(self, key_name):
        self.line_edit.setText(key_name)
        self.setText(self.DEFAULT_TEXT)
        self.setEnabled(True)


# ---------------------------------------------------------------- Config dialog
class ButtonConfigDialog(QDialog):
    def __init__(self, button_data: dict, hotkey_manager: HotkeyManager, audio_manager: AudioManager,
                 parent=None, allow_delete: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Tombol")
        self.setMinimumWidth(440)
        self.button_data = dict(button_data)
        self.hotkey_manager = hotkey_manager
        self.audio_manager = audio_manager
        self.delete_requested = False
        self._duration_ms = 0
        self._probe_player = None

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

        # --- Potong durasi (trim) ---
        self.trim_start_slider = QSlider(Qt.Orientation.Horizontal)
        self.trim_end_slider = QSlider(Qt.Orientation.Horizontal)
        self.trim_start_slider.setRange(0, 0)
        self.trim_end_slider.setRange(0, 0)
        self.trim_start_slider.valueChanged.connect(self._on_trim_start_changed)
        self.trim_end_slider.valueChanged.connect(self._on_trim_end_changed)

        self.trim_time_label = QLabel("0:00 — 0:00 / 0:00")
        self.trim_time_label.setObjectName("Hint")

        preview_btn = QPushButton("▶  Preview Potongan")
        preview_btn.clicked.connect(self._preview_trim)

        self.trim_start_label = field_label("POTONG — MULAI")
        form.addRow(self.trim_start_label, self.trim_start_slider)
        self.trim_end_label = field_label("POTONG — SELESAI")
        form.addRow(self.trim_end_label, self.trim_end_slider)
        self.trim_info_label = field_label("")
        form.addRow(self.trim_info_label, self.trim_time_label)
        self.trim_preview_placeholder = field_label("")
        form.addRow(self.trim_preview_placeholder, preview_btn)
        self._trim_widgets = [
            self.trim_start_slider, self.trim_end_slider, self.trim_time_label,
            self.trim_start_label, self.trim_end_label, self.trim_info_label,
            self.trim_preview_placeholder, preview_btn
        ]
        self._preview_btn = preview_btn

        # Muat durasi kalau sudah ada file suara tersimpan sebelumnya
        if self.button_data.get("sound_path"):
            self._probe_duration(
                self.button_data["sound_path"],
                keep_existing=True,
                existing_start=self.button_data.get("sound_start_ms", 0),
                existing_end=self.button_data.get("sound_end_ms"),
            )

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

        color_row = QHBoxLayout()
        self.color_value = self.button_data.get("color", "#6470ff")
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
            # file baru -> reset potongan ke full (0 .. durasi)
            self._probe_duration(path, keep_existing=False)

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
        has_duration = is_sound and self._duration_ms > 0
        for w in self._trim_widgets:
            w.setVisible(has_duration)
        for w in (self.app_row_label, self.app_row_widget, self.app_args_label, self.app_args_edit):
            w.setVisible(is_app)

    # --- Trim (potong durasi) ---
    def _probe_duration(self, path: str, keep_existing: bool, existing_start: int = 0, existing_end=None):
        self._duration_ms = 0
        if self._probe_player:
            self._probe_player.deleteLater()
        self._probe_player = QMediaPlayer()

        def on_duration(duration: int):
            if duration <= 0:
                return
            self._duration_ms = duration
            self.trim_start_slider.setRange(0, duration)
            self.trim_end_slider.setRange(0, duration)
            if keep_existing:
                start = min(max(existing_start or 0, 0), duration)
                end = existing_end if existing_end else duration
                end = min(max(end, start + 100), duration)
            else:
                start, end = 0, duration
            self.trim_start_slider.setValue(start)
            self.trim_end_slider.setValue(end)
            self._update_trim_label()
            self._update_visible_fields()

        self._probe_player.durationChanged.connect(on_duration)
        self._probe_player.setSource(QUrl.fromLocalFile(path))

    def _on_trim_start_changed(self, value: int):
        if value > self.trim_end_slider.value() - 100:
            self.trim_start_slider.blockSignals(True)
            self.trim_start_slider.setValue(max(0, self.trim_end_slider.value() - 100))
            self.trim_start_slider.blockSignals(False)
        self._update_trim_label()

    def _on_trim_end_changed(self, value: int):
        if value < self.trim_start_slider.value() + 100:
            self.trim_end_slider.blockSignals(True)
            self.trim_end_slider.setValue(min(self._duration_ms, self.trim_start_slider.value() + 100))
            self.trim_end_slider.blockSignals(False)
        self._update_trim_label()

    def _update_trim_label(self):
        start = self.trim_start_slider.value()
        end = self.trim_end_slider.value()
        self.trim_time_label.setText(
            f"{format_ms(start)} — {format_ms(end)}  /  total {format_ms(self._duration_ms)}"
        )

    def _preview_trim(self):
        path = self.sound_path_edit.text()
        if not path:
            return
        start = self.trim_start_slider.value()
        end = self.trim_end_slider.value()
        volume = self.sound_volume_slider.value() / 100.0
        self.audio_manager.play(path, volume, start_ms=start, end_ms=end)

    def get_result(self) -> dict:
        data = dict(self.button_data)
        data["label"] = self.label_edit.text().strip() or "Tombol"
        data["action_type"] = self.action_combo.currentData()
        data["sound_path"] = self.sound_path_edit.text()
        data["sound_volume"] = self.sound_volume_slider.value() / 100.0
        if self._duration_ms > 0:
            start = self.trim_start_slider.value()
            end = self.trim_end_slider.value()
            data["sound_start_ms"] = start
            data["sound_end_ms"] = None if end >= self._duration_ms else end
        else:
            data["sound_start_ms"] = 0
            data["sound_end_ms"] = None
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

    def done(self, result):
        if self._probe_player:
            self._probe_player.deleteLater()
            self._probe_player = None
        super().done(result)


# ---------------------------------------------------------------- Profile manager dialog
class ProfileManagerDialog(QDialog):
    def __init__(self, profiles: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kelola Profile")
        self.setMinimumWidth(420)
        self.profiles = [dict(p) for p in profiles]  # kerja di salinan; batal = tidak ada perubahan
        self.deleted_ids = set()

        outer = QVBoxLayout(self)
        title = QLabel("Kelola Profile")
        title.setObjectName("DialogTitle")
        outer.addWidget(title)

        self.rows_layout = QVBoxLayout()
        outer.addLayout(self.rows_layout)
        self.row_widgets = {}
        for p in self.profiles:
            self._add_row(p)

        add_btn = QPushButton("＋ Tambah Profile Baru")
        add_btn.clicked.connect(self._add_new_profile)
        outer.addWidget(add_btn)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = QPushButton("Batal")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Simpan")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._on_save)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        outer.addSpacing(6)
        outer.addLayout(button_row)

    def _add_row(self, profile: dict):
        row = QHBoxLayout()
        edit = QLineEdit(profile["name"])
        row.addWidget(edit)
        del_btn = QPushButton("🗑")
        del_btn.setObjectName("Danger")
        del_btn.setFixedWidth(44)
        del_btn.clicked.connect(lambda: self._remove_row(profile["id"]))
        row.addWidget(del_btn)
        container = QWidget()
        container.setLayout(row)
        self.rows_layout.addWidget(container)
        self.row_widgets[profile["id"]] = (container, edit)

    def _add_new_profile(self):
        name, ok = QInputDialog.getText(self, "Profile Baru", "Nama profile:", text=f"Profile {len(self.profiles) + 1}")
        if ok and name.strip():
            new_p = config_manager.new_profile(name.strip())
            self.profiles.append(new_p)
            self._add_row(new_p)

    def _remove_row(self, profile_id: str):
        if len(self.profiles) - len(self.deleted_ids) <= 1:
            QMessageBox.warning(self, "Tidak Bisa Dihapus", "Minimal harus ada 1 profile.")
            return
        confirm = QMessageBox.question(
            self, "Hapus Profile", "Hapus profile ini beserta semua tombolnya?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.deleted_ids.add(profile_id)
        container, _ = self.row_widgets.pop(profile_id)
        container.deleteLater()

    def _on_save(self):
        for p in self.profiles:
            if p["id"] in self.row_widgets:
                p["name"] = self.row_widgets[p["id"]][1].text().strip() or p["name"]
        self.profiles = [p for p in self.profiles if p["id"] not in self.deleted_ids]
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._show_anim = anim


# ---------------------------------------------------------------- Main window
class MainWindow(QMainWindow):
    action_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.action_requested.connect(self._execute_action)
        self.setWindowTitle("StreamPad — Soundboard & Macro Deck untuk DumbPad")
        self.resize(1000, 680)

        self.config = config_manager.load_config()
        self.audio_manager = AudioManager()
        self.hotkey_manager = HotkeyManager()
        self.edit_mode = False

        self._build_ui()
        self._register_all_hotkeys()

    def _active_profile(self) -> dict:
        return config_manager.get_active_profile(self.config)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        # orb dekoratif di background, seperti pada referensi dashboard
        orb1 = GlowOrb("#6470ff", root)
        orb1.move(-80, -60)
        orb2 = GlowOrb("#8b5cf6", root)
        orb2.move(760, 420)
        orb1.lower()
        orb2.lower()

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

        self.profile_bar = ProfileBar()
        self.profile_bar.set_add_handler(self._add_profile)
        self.profile_bar.profile_changed.connect(self._switch_profile)
        self.profile_bar.manage_requested.connect(self._open_profile_manager)
        outer.addWidget(self.profile_bar)

        self.hint = QLabel()
        self.hint.setObjectName("Hint")
        outer.addWidget(self.hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(16)
        scroll.setWidget(self.grid_container)
        outer.addWidget(scroll)

        self._refresh_profile_bar()
        self._render_buttons()
        self._update_hint()

    def _update_hint(self):
        if self.edit_mode:
            self.hint.setText("Mode Edit — klik kartu tombol untuk mengubah atau menghapusnya.")
        else:
            self.hint.setText("Mode Jalankan — klik kartu tombol untuk memutar suara atau membuka aplikasi.")

    def _refresh_profile_bar(self):
        self.profile_bar.populate(self.config["profiles"], self.config["active_profile"])

    def _render_buttons(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        profile = self._active_profile()
        buttons = profile.get("buttons", [])
        if not buttons:
            empty = QWidget()
            box = QVBoxLayout(empty)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon = QLabel("🎛️")
            icon.setStyleSheet("font-size: 48px;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t = QLabel("Belum ada tombol di profile ini")
            t.setObjectName("EmptyTitle")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s = QLabel("Klik \"＋ Tambah Tombol\" untuk membuat tombol pertama.")
            s.setObjectName("EmptyText")
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(icon)
            box.addWidget(t)
            box.addWidget(s)
            self.grid.addWidget(empty, 0, 0)
            return

        columns = profile.get("columns", 4)
        for index, button_data in enumerate(buttons):
            deck_btn = DeckButton(button_data)
            deck_btn.clicked.connect(lambda checked=False, b=button_data: self._on_button_clicked(b))
            row, col = divmod(index, columns)
            self.grid.addWidget(deck_btn, row, col)

    def _set_edit_mode(self, is_edit: bool):
        self.edit_mode = is_edit
        self._update_hint()

    # ---------------- Profile actions ----------------
    def _add_profile(self):
        name, ok = QInputDialog.getText(
            self, "Profile Baru", "Nama profile:",
            text=f"Profile {len(self.config['profiles']) + 1}"
        )
        if ok and name.strip():
            profile = config_manager.new_profile(name.strip())
            self.config["profiles"].append(profile)
            self.config["active_profile"] = profile["id"]
            self._save_and_refresh()

    def _switch_profile(self, profile_id: str):
        if profile_id == self.config["active_profile"]:
            return
        self.config["active_profile"] = profile_id
        self._save_and_refresh()

    def _open_profile_manager(self):
        dialog = ProfileManagerDialog(self.config["profiles"], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config["profiles"] = dialog.profiles
            if self.config["active_profile"] not in [p["id"] for p in self.config["profiles"]]:
                self.config["active_profile"] = self.config["profiles"][0]["id"]
            self._save_and_refresh()

    # ---------------- Button actions ----------------
    def _add_button(self):
        new_data = config_manager.new_button(str(uuid.uuid4()))
        dialog = ButtonConfigDialog(new_data, self.hotkey_manager, self.audio_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()
            self._active_profile().setdefault("buttons", []).append(result)
            self._save_and_refresh()

    def _on_button_clicked(self, button_data: dict):
        if self.edit_mode:
            dialog = ButtonConfigDialog(button_data, self.hotkey_manager, self.audio_manager, self, allow_delete=True)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                buttons = self._active_profile()["buttons"]
                if dialog.delete_requested:
                    confirm = QMessageBox.question(
                        self, "Hapus Tombol", f"Hapus tombol '{button_data.get('label')}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        self._active_profile()["buttons"] = [b for b in buttons if b["id"] != button_data["id"]]
                        self._save_and_refresh()
                    return
                result = dialog.get_result()
                for i, b in enumerate(buttons):
                    if b["id"] == button_data["id"]:
                        buttons[i] = result
                        break
                self._save_and_refresh()
            return

        self._execute_action(button_data)

    def _execute_action(self, button_data: dict):
        action = button_data.get("action_type")
        if action == "sound":
            self.audio_manager.play(
                button_data.get("sound_path", ""),
                button_data.get("sound_volume", 1.0),
                start_ms=button_data.get("sound_start_ms", 0) or 0,
                end_ms=button_data.get("sound_end_ms"),
            )
        elif action == "app":
            launch_app(button_data.get("app_path", ""), button_data.get("app_args", ""))

    def _register_all_hotkeys(self):
        self.hotkey_manager.unregister_all()
        for button_data in self._active_profile().get("buttons", []):
            hotkey = button_data.get("hotkey")
            if hotkey:
                self.hotkey_manager.register(hotkey, lambda b=button_data: self.action_requested.emit(b))

    def _save_and_refresh(self):
        config_manager.save_config(self.config)
        self._refresh_profile_bar()
        self._render_buttons()
        self._register_all_hotkeys()
        self._update_hint()

    def closeEvent(self, event):
        self.hotkey_manager.unregister_all()
        config_manager.save_config(self.config)
        super().closeEvent(event)
