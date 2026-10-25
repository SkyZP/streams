"""
gui.py
Antarmuka StreamPad bergaya Liquid Glass: background cair yang bergerak
pelan, panel & tombol kaca dengan kilau dan rim terang, tombol export,
plus sistem Profile dan potong durasi suara.
"""
import os
import subprocess
import sys
import uuid
import json

from PySide6.QtCore import Qt, Signal, QUrl, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QFontMetrics
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QFileDialog, QSlider, QMessageBox,
    QColorDialog, QScrollArea, QButtonGroup, QInputDialog, QFormLayout,
    QSizePolicy, QDialog
)

from modules import config_manager
from modules.audio_manager import AudioManager
from modules.hotkey_manager import HotkeyManager
from modules.glass import (
    Tween, paint_glass, paint_glow, LiquidBackground, GlassPanel,
    GlassPillButton, GlassTab, GlassDialog
)

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


# ---------------------------------------------------------------- Profile bar
class ProfileBar(QWidget):
    profile_changed = Signal(str)   # id profile yang dipilih
    manage_requested = Signal()
    add_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self.panel = GlassPanel(radius=25)
        self.panel.setFixedHeight(50)
        self.tab_layout = QHBoxLayout(self.panel)
        self.tab_layout.setContentsMargins(5, 4, 5, 4)
        self.tab_layout.setSpacing(2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(50)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(self.panel)
        outer.addWidget(scroll, 1)

        add_btn = GlassPillButton("＋ Profile")
        add_btn.clicked.connect(self.add_requested.emit)
        outer.addWidget(add_btn)

        manage_btn = GlassPillButton("⚙")
        manage_btn.setFixedWidth(52)
        manage_btn.clicked.connect(self.manage_requested.emit)
        outer.addWidget(manage_btn)

    def populate(self, profiles: list, active_id: str):
        for tab in list(self._tabs.values()):
            self._group.removeButton(tab)
        self._tabs.clear()
        while self.tab_layout.count():
            item = self.tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for profile in profiles:
            tab = GlassTab(profile["name"])
            tab.set_checked_silent(profile["id"] == active_id)
            tab.clicked.connect(lambda checked=False, pid=profile["id"]: self.profile_changed.emit(pid))
            self._group.addButton(tab)
            self._tabs[profile["id"]] = tab
            self.tab_layout.addWidget(tab)
        self.tab_layout.addStretch()

    def set_active(self, profile_id: str):
        tab = self._tabs.get(profile_id)
        if tab is not None and not tab.isChecked():
            tab.setChecked(True)


# ---------------------------------------------------------------- Deck button
class DeckButton(QPushButton):
    """Kartu tombol kaca bertinta warna pilihan user, dengan glow saat hover."""
    MARGIN = 14

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("DeckButton")
        self.data = data
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumWidth(156)
        self.setFixedHeight(136)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._hover = Tween(self, 240)
        self._press = Tween(self, 120)

    def refresh(self):
        self.update()

    def enterEvent(self, event):
        self._hover.go(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover.go(0.0)
        self._press.go(0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._press.go(1.0)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._press.go(0.0)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        m = self.MARGIN
        body = QRectF(self.rect()).adjusted(m, m, -m, -m)
        shrink = 3.0 * self._press.current
        body = body.adjusted(shrink, shrink, -shrink, -shrink)

        color = QColor(self.data.get("color", "#6470ff"))
        hover = self._hover.current
        radius = 24.0

        paint_glow(p, body, radius, color, 0.20 + 0.80 * hover)
        paint_glass(p, body, radius, tint=color, strength=1.0 + 0.30 * hover)

        # ikon
        icon = ACTION_ICONS.get(self.data.get("action_type", "sound"), "🔘")
        icon_font = QFont("Segoe UI Emoji")
        icon_font.setPixelSize(30)
        p.setFont(icon_font)
        p.setPen(QColor(255, 255, 255, 245))
        p.drawText(QRectF(body.left(), body.top() + 9, body.width(), 40),
                   Qt.AlignmentFlag.AlignCenter, icon)

        # label
        label_font = QFont("Segoe UI")
        label_font.setPixelSize(13)
        label_font.setWeight(QFont.Weight.DemiBold)
        p.setFont(label_font)
        fm = QFontMetrics(label_font)
        text = fm.elidedText(self.data.get("label", "Tombol"),
                             Qt.TextElideMode.ElideRight, int(body.width() - 22))
        p.setPen(QColor(255, 255, 255, 250))
        p.drawText(QRectF(body.left() + 11, body.top() + 51, body.width() - 22, 20),
                   Qt.AlignmentFlag.AlignCenter, text)

        # chip hotkey
        hotkey = self.data.get("hotkey", "")
        if hotkey:
            chip_font = QFont("Segoe UI")
            chip_font.setPixelSize(10)
            chip_font.setWeight(QFont.Weight.DemiBold)
            cfm = QFontMetrics(chip_font)
            label = hotkey.upper()
            cw = min(body.width() - 22, cfm.horizontalAdvance(label) + 20)
            chip = QRectF(body.center().x() - cw / 2.0, body.bottom() - 27, cw, 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 42))
            p.drawRoundedRect(chip, 9, 9)
            p.setFont(chip_font)
            p.setPen(QColor(255, 255, 255, 225))
            p.drawText(chip, Qt.AlignmentFlag.AlignCenter, label)


# ---------------------------------------------------------------- Hotkey capture
class HotkeyCaptureButton(GlassPillButton):
    captured = Signal(str)
    DEFAULT_TEXT = "🎙  Rekam tombol"

    def __init__(self, hotkey_manager: HotkeyManager, line_edit: QLineEdit, parent=None):
        super().__init__(self.DEFAULT_TEXT, "normal", parent)
        self.hotkey_manager = hotkey_manager
        self.line_edit = line_edit
        self.clicked.connect(self._start_capture)
        self.captured.connect(self._on_captured)

    def _start_capture(self):
        self.setText("Menunggu... tekan tombolnya")
        self.setEnabled(False)
        self.hotkey_manager.capture_next_key(lambda key_name: self.captured.emit(key_name))

    def _on_captured(self, key_name):
        self.line_edit.setText(key_name)
        self.setText(self.DEFAULT_TEXT)
        self.setEnabled(True)


# ---------------------------------------------------------------- Config dialog
class ButtonConfigDialog(GlassDialog):
    def __init__(self, button_data: dict, hotkey_manager: HotkeyManager, audio_manager: AudioManager,
                 parent=None, allow_delete: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Konfigurasi Tombol")
        self.setMinimumWidth(500)
        self.button_data = dict(button_data)
        self.hotkey_manager = hotkey_manager
        self.audio_manager = audio_manager
        self.delete_requested = False
        self._duration_ms = 0
        self._probe_player = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(6)
        title = QLabel("Konfigurasi Tombol")
        title.setObjectName("DialogTitle")
        outer.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)
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

        # --- Suara ---
        sound_row = QHBoxLayout()
        self.sound_path_edit = QLineEdit(self.button_data.get("sound_path", ""))
        self.sound_path_edit.setReadOnly(True)
        sound_browse = GlassPillButton("Pilih File")
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

        preview_btn = GlassPillButton("▶  Preview Potongan")
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

        if self.button_data.get("sound_path"):
            self._probe_duration(
                self.button_data["sound_path"],
                keep_existing=True,
                existing_start=self.button_data.get("sound_start_ms", 0),
                existing_end=self.button_data.get("sound_end_ms"),
            )

        # --- Aplikasi ---
        app_row = QHBoxLayout()
        self.app_path_edit = QLineEdit(self.button_data.get("app_path", ""))
        self.app_path_edit.setReadOnly(True)
        app_browse = GlassPillButton("Pilih File")
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

        # --- Warna ---
        color_row = QHBoxLayout()
        self.color_value = self.button_data.get("color", "#6470ff")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self._update_color_preview()
        color_btn = GlassPillButton("Pilih Warna")
        color_btn.clicked.connect(self._choose_color)
        color_row.addWidget(self.color_preview)
        color_row.addWidget(color_btn)
        color_row.addStretch()
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow(field_label("WARNA"), color_widget)

        # --- Tombol bawah ---
        button_row = QHBoxLayout()
        if allow_delete:
            delete_btn = GlassPillButton("Hapus Tombol", "danger")
            delete_btn.clicked.connect(self._request_delete)
            button_row.addWidget(delete_btn)
        button_row.addStretch()

        cancel_btn = GlassPillButton("Batal")
        cancel_btn.clicked.connect(self.reject)
        save_btn = GlassPillButton("Simpan", "primary")
        save_btn.clicked.connect(self.accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        outer.addSpacing(8)
        outer.addLayout(button_row)

        self._update_visible_fields()

    def _request_delete(self):
        self.delete_requested = True
        self.accept()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(
            f"background-color: {self.color_value}; border-radius: 16px;"
            " border: 1px solid rgba(255,255,255,0.45);"
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

    def done(self, result):
        if self._probe_player:
            self._probe_player.deleteLater()
            self._probe_player = None
        super().done(result)


# ---------------------------------------------------------------- Profile manager dialog
class ProfileManagerDialog(GlassDialog):
    def __init__(self, profiles: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kelola Profile")
        self.setMinimumWidth(460)
        self.profiles = [dict(p) for p in profiles]
        self.deleted_ids = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(8)
        title = QLabel("Kelola Profile")
        title.setObjectName("DialogTitle")
        outer.addWidget(title)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(8)
        outer.addLayout(self.rows_layout)
        self.row_widgets = {}
        for p in self.profiles:
            self._add_row(p)

        add_btn = GlassPillButton("＋ Tambah Profile Baru")
        add_btn.clicked.connect(self._add_new_profile)
        outer.addWidget(add_btn)

        button