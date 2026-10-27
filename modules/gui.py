"""
gui.py
Antarmuka StreamPad bergaya kaca bening monokrom: background hitam-putih
blur, panel & tombol transparan, plus sistem Profile, potong durasi suara,
pengaturan tersimpan, dan export/import config.json.
"""
import os
import subprocess
import sys
import uuid

from PySide6.QtCore import Qt, Signal, QUrl, QRectF, QSize, QTimer
from PySide6.QtGui import QColor, QPainter, QFont, QFontMetrics
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QFileDialog, QSlider,
    QColorDialog, QScrollArea, QButtonGroup, QFormLayout,
    QSizePolicy, QDialog
)

from modules import config_manager
from modules.audio_manager import AudioManager
from modules.hotkey_manager import HotkeyManager, key_name_from_event
from modules.glass import (
    Tween, paint_glass, paint_glow, draw_icon, LiquidBackground, GlassPanel,
    GlassPillButton, GlassTab, GlassToggle, GlassSwitch, IconWidget, GlassDialog
)

ACTION_LABELS = {"sound": "Putar Suara", "app": "Buka Aplikasi"}
ACTION_ICONS = {"sound": "sound", "app": "app"}


# ---------------------------------------------------------------- Dialog kecil bergaya kaca
class GlassMessageDialog(GlassDialog):
    """Pengganti QMessageBox / QInputDialog supaya semua dialog seragam."""

    def __init__(self, parent, title, message, ok_text="OK", cancel_text="Batal",
                 danger=False, input_text=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(10)
        head = QLabel(title)
        head.setObjectName("DialogTitle")
        outer.addWidget(head)
        body = QLabel(message)
        body.setWordWrap(True)
        body.setObjectName("EmptyText")
        outer.addWidget(body)
        self.edit = None
        if input_text is not None:
            self.edit = QLineEdit(input_text)
            self.edit.selectAll()
            self.edit.returnPressed.connect(self.accept)
            outer.addWidget(self.edit)
        row = QHBoxLayout()
        row.addStretch()
        if cancel_text:
            cancel = GlassPillButton(cancel_text)
            cancel.clicked.connect(self.reject)
            row.addWidget(cancel)
        ok = GlassPillButton(ok_text, "danger" if danger else "primary")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        outer.addSpacing(6)
        outer.addLayout(row)

    def text(self) -> str:
        return self.edit.text().strip() if self.edit else ""


def ask_text(parent, title, label, default=""):
    dlg = GlassMessageDialog(parent, title, label, "OK", "Batal", input_text=default)
    if dlg.exec() == QDialog.DialogCode.Accepted and dlg.text():
        return dlg.text()
    return None


def confirm(parent, title, message, ok_text="Ya", danger=False) -> bool:
    dlg = GlassMessageDialog(parent, title, message, ok_text, "Batal", danger=danger)
    return dlg.exec() == QDialog.DialogCode.Accepted


def notify(parent, title, message):
    GlassMessageDialog(parent, title, message, "OK", None).exec()


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

        add_btn = GlassPillButton("+  Profile")
        add_btn.clicked.connect(self.add_requested.emit)
        outer.addWidget(add_btn)

        manage_btn = GlassPillButton("⚙")
        manage_btn.setFixedWidth(56)
        manage_btn.setToolTip("Pengaturan")
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

        color = QColor(self.data.get("color", "#ffffff"))
        hover = self._hover.current
        radius = 24.0

        paint_glow(p, body, radius, QColor(255, 255, 255), 0.15 + 0.85 * hover)
        paint_glass(p, body, radius, None, strength=1.15 + 0.9 * hover, rim=1.0 + 0.4 * hover)

        # ikon garis monokrom
        icon = ACTION_ICONS.get(self.data.get("action_type", "sound"), "sound")
        icon_rect = QRectF(body.center().x() - 17, body.top() + 16, 34, 34)
        draw_icon(p, icon, icon_rect, QColor(255, 255, 255, 235), 2.2)

        # titik aksen kecil sesuai warna pilihan user
        if color.name().lower() != "#ffffff":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(QRectF(body.right() - 20, body.top() + 12, 8, 8))

        # label
        label_font = QFont("Segoe UI")
        label_font.setPixelSize(13)
        label_font.setWeight(QFont.Weight.DemiBold)
        p.setFont(label_font)
        fm = QFontMetrics(label_font)
        text = fm.elidedText(self.data.get("label", "Tombol"),
                             Qt.TextElideMode.ElideRight, int(body.width() - 22))
        p.setPen(QColor(255, 255, 255, 250))
        p.drawText(QRectF(body.left() + 11, body.top() + 56, body.width() - 22, 20),
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
            chip = QRectF(body.center().x() - cw / 2.0, body.bottom() - 28, cw, 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 34))
            p.drawRoundedRect(chip, 9, 9)
            p.setFont(chip_font)
            p.setPen(QColor(255, 255, 255, 215))
            p.drawText(chip, Qt.AlignmentFlag.AlignCenter, label)


# ---------------------------------------------------------------- Hotkey capture
class HotkeyCaptureButton(GlassPillButton):
    """Klik, lalu tekan tombol (atau tombol di DumbPad) untuk merekam hotkey. Esc = batal."""
    DEFAULT_TEXT = "●  Rekam tombol"

    def __init__(self, hotkey_manager: HotkeyManager, line_edit: QLineEdit, parent=None):
        super().__init__(self.DEFAULT_TEXT, "normal", parent)
        self.line_edit = line_edit
        self._capturing = False
        self.clicked.connect(self._start_capture)

    def _start_capture(self):
        self._capturing = True
        self.setText("Tekan tombolnya... (Esc batal)")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.grabKeyboard()

    def _stop_capture(self):
        self._capturing = False
        self.releaseKeyboard()
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setText(self.DEFAULT_TEXT)

    def keyPressEvent(self, event):
        if not self._capturing:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Escape:
            self._stop_capture()
            return
        name = key_name_from_event(event)
        if name:
            self.line_edit.setText(name)
            self._stop_capture()

    def focusOutEvent(self, event):
        if self._capturing:
            self._stop_capture()
        super().focusOutEvent(event)


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
            self.action_combo.addItem(text, key)
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

        # Muat durasi kalau sudah ada file suara tersimpan sebelumnya
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
        self.color_value = self.button_data.get("color", "#ffffff")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self._update_color_preview()
        color_btn = GlassPillButton("Pilih Warna Aksen")
        color_btn.clicked.connect(self._choose_color)
        color_row.addWidget(self.color_preview)
        color_row.addWidget(color_btn)
        color_row.addStretch()
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow(field_label("AKSEN"), color_widget)

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
        self.profiles = [dict(p) for p in profiles]  # kerja di salinan; batal = tidak ada perubahan
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

        add_btn = GlassPillButton("+  Tambah Profile Baru")
        add_btn.clicked.connect(self._add_new_profile)
        outer.addWidget(add_btn)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = GlassPillButton("Batal")
        cancel_btn.clicked.connect(self.reject)
        save_btn = GlassPillButton("Simpan", "primary")
        save_btn.clicked.connect(self._on_save)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        outer.addSpacing(8)
        outer.addLayout(button_row)

    def _add_row(self, profile: dict):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        edit = QLineEdit(profile["name"])
        row.addWidget(edit)
        del_btn = GlassPillButton("Hapus", "danger")
        del_btn.setFixedWidth(84)
        del_btn.clicked.connect(lambda checked=False, pid=profile["id"]: self._remove_row(pid))
        row.addWidget(del_btn)
        container = QWidget()
        container.setLayout(row)
        self.rows_layout.addWidget(container)
        self.row_widgets[profile["id"]] = (container, edit)

    def _add_new_profile(self):
        name = ask_text(self, "Profile Baru", "Nama profile:", f"Profile {len(self.profiles) + 1}")
        if name:
            new_p = config_manager.new_profile(name)
            self.profiles.append(new_p)
            self._add_row(new_p)

    def _remove_row(self, profile_id: str):
        if len(self.profiles) - len(self.deleted_ids) <= 1:
            notify(self, "Tidak Bisa Dihapus", "Minimal harus ada 1 profile.")
            return
        if not confirm(self, "Hapus Profile", "Hapus profile ini beserta semua tombolnya?", "Hapus", danger=True):
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


# ---------------------------------------------------------------- Settings dialog
class SettingsDialog(GlassDialog):
    """Pengaturan aplikasi + simpan / export / import config.json."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.win = window
        self.setWindowTitle("Pengaturan")
        self.setMinimumWidth(520)
        cfg = window.config
        profile = window._active_profile()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(8)
        title = QLabel("Pengaturan")
        title.setObjectName("DialogTitle")
        outer.addWidget(title)

        def section(text):
            lbl = QLabel(text)
            lbl.setObjectName("SectionTitle")
            outer.addWidget(lbl)

        def row(label_text, widget, value_label=None):
            r = QHBoxLayout()
            lbl = QLabel(label_text)
            r.addWidget(lbl)
            r.addStretch()
            if value_label is not None:
                r.addWidget(value_label)
            r.addWidget(widget)
            outer.addLayout(r)

        section("TAMPILAN & SUARA")
        self.columns_slider = QSlider(Qt.Orientation.Horizontal)
        self.columns_slider.setRange(1, 8)
        self.columns_slider.setValue(int(profile.get("columns", 4)))
        self.columns_slider.setFixedWidth(200)
        self.columns_value = QLabel(str(self.columns_slider.value()))
        self.columns_slider.valueChanged.connect(lambda v: self.columns_value.setText(str(v)))
        row(f"Tombol per baris (profile \u201c{profile['name']}\u201d)", self.columns_slider, self.columns_value)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(cfg["settings"].get("master_volume", 1.0) * 100))
        self.volume_slider.setFixedWidth(200)
        self.volume_value = QLabel(f"{self.volume_slider.value()}%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_value.setText(f"{v}%"))
        row("Volume utama (semua suara)", self.volume_slider, self.volume_value)

        self.anim_switch = GlassSwitch(cfg["settings"].get("animate_background", True))
        row("Animasi background", self.anim_switch)

        section("DATA & BACKUP")
        path_label = QLabel(config_manager.CONFIG_PATH)
        path_label.setObjectName("Hint")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(path_label)
        note = QLabel("Semua perubahan (durasi potongan, volume, hotkey, dll) otomatis tersimpan di file ini.")
        note.setObjectName("Hint")
        note.setWordWrap(True)
        outer.addWidget(note)

        io_row = QHBoxLayout()
        export_btn = GlassPillButton("Export config.json")
        export_btn.clicked.connect(self._export)
        import_btn = GlassPillButton("Import config.json")
        import_btn.clicked.connect(self._import)
        io_row.addWidget(export_btn)
        io_row.addWidget(import_btn)
        io_row.addStretch()
        outer.addLayout(io_row)

        manage_btn = GlassPillButton("Kelola Profile…")
        manage_btn.clicked.connect(self._manage_profiles)
        pr = QHBoxLayout()
        pr.addWidget(manage_btn)
        pr.addStretch()
        outer.addLayout(pr)

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_btn = GlassPillButton("Tutup")
        cancel_btn.clicked.connect(self.reject)
        save_btn = GlassPillButton("Simpan", "primary")
        save_btn.clicked.connect(self._save)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        outer.addSpacing(8)
        outer.addLayout(button_row)

    def _save(self):
        self.win.apply_settings(
            columns=self.columns_slider.value(),
            master_volume=self.volume_slider.value() / 100.0,
            animate_background=self.anim_switch.isChecked(),
        )
        self.accept()

    def _export(self):
        self.win.export_config_dialog()

    def _import(self):
        if self.win.import_config_dialog():
            self.accept()

    def _manage_profiles(self):
        self.accept()
        self.win._open_profile_manager()


# ---------------------------------------------------------------- Main window
class MainWindow(QMainWindow):
    # Hotkey datang dari thread library keyboard; signal ini memindahkannya
    # ke thread utama Qt supaya audio & UI aman dijalankan.
    action_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.action_requested.connect(self._execute_action)
        self.setWindowTitle("StreamPad — Soundboard & Macro Deck untuk DumbPad")
        self.resize(1040, 700)
        self.setMinimumSize(820, 540)

        self.config = config_manager.load_config()
        self.audio_manager = AudioManager()
        self.hotkey_manager = HotkeyManager()
        self.edit_mode = False

        self._build_ui()
        self._apply_global_settings()
        self._register_all_hotkeys()

    def _active_profile(self) -> dict:
        return config_manager.get_active_profile(self.config)

    def _build_ui(self):
        root = LiquidBackground()
        self.backdrop = root
        root.setObjectName("Root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
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

        self.toggle = GlassToggle()
        self.toggle.toggled.connect(self._set_edit_mode)
        header_row.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        add_btn = GlassPillButton("+  Tambah Tombol", "primary")
        add_btn.clicked.connect(self._add_button)
        header_row.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(header_row)

        self.profile_bar = ProfileBar()
        self.profile_bar.add_requested.connect(self._add_profile)
        self.profile_bar.profile_changed.connect(self._switch_profile)
        self.profile_bar.manage_requested.connect(self._open_settings)
        outer.addWidget(self.profile_bar)

        hint_row = QHBoxLayout()
        self.hint = QLabel()
        self.hint.setObjectName("Hint")
        self.status = QLabel("")
        self.status.setObjectName("Status")
        hint_row.addWidget(self.hint)
        hint_row.addStretch()
        hint_row.addWidget(self.status)
        outer.addLayout(hint_row)
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status.setText(""))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        self.grid_container = QWidget()
        self.grid_container.setAutoFillBackground(False)
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.grid_container)
        outer.addWidget(scroll, 1)

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
        columns = max(1, profile.get("columns", 4))

        if not buttons:
            panel = GlassPanel(radius=28)
            panel.setMinimumHeight(240)
            box = QVBoxLayout(panel)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon = IconWidget("pad", 64)
            box.addWidget(icon, 0, Qt.AlignmentFlag.AlignHCenter)
            t = QLabel("Belum ada tombol di profile ini")
            t.setObjectName("EmptyTitle")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            s = QLabel("Klik \"+ Tambah Tombol\" untuk membuat tombol pertama.")
            s.setObjectName("EmptyText")
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(t)
            box.addWidget(s)
            self.grid.addWidget(panel, 0, 0, 1, columns)
            return

        for index, button_data in enumerate(buttons):
            deck_btn = DeckButton(button_data)
            deck_btn.clicked.connect(lambda checked=False, b=button_data: self._on_button_clicked(b))
            row, col = divmod(index, columns)
            self.grid.addWidget(deck_btn, row, col)
        for c in range(columns):
            self.grid.setColumnStretch(c, 1)

    def _set_edit_mode(self, is_edit: bool):
        self.edit_mode = is_edit
        self._update_hint()

    # ---------------- Profile actions ----------------
    def _add_profile(self):
        name = ask_text(self, "Profile Baru", "Nama profile:", f"Profile {len(self.config['profiles']) + 1}")
        if name:
            profile = config_manager.new_profile(name)
            self.config["profiles"].append(profile)
            self.config["active_profile"] = profile["id"]
            self._save_and_refresh()

    def _switch_profile(self, profile_id: str):
        if profile_id == self.config["active_profile"]:
            return
        self.config["active_profile"] = profile_id
        self._persist()
        # tab sudah beranimasi sendiri; cukup ganti isi grid & hotkey
        self._render_buttons()
        self._register_all_hotkeys()

    def _open_settings(self):
        SettingsDialog(self, self).exec()

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
                    if confirm(self, "Hapus Tombol", f"Hapus tombol '{button_data.get('label')}'?",
                               "Hapus", danger=True):
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

    # ---------------- Simpan / export / import ----------------
    def _persist(self) -> bool:
        ok = config_manager.save_config(self.config)
        if ok:
            self.status.setText("✓ Tersimpan")
            self._status_timer.start(2200)
        else:
            self.status.setText("⚠ Gagal menyimpan")
            notify(self, "Gagal Menyimpan",
                   "Tidak bisa menulis config.json di:\n" + config_manager.CONFIG_PATH +
                   "\n\nCoba pindahkan aplikasi keluar dari file .zip / folder read-only, "
                   "atau gunakan Export config.json di Pengaturan.")
        return ok

    def _apply_global_settings(self):
        st = self.config["settings"]
        self.audio_manager.master_volume = float(st.get("master_volume", 1.0))
        self.backdrop.set_animated(bool(st.get("animate_background", True)))

    def apply_settings(self, columns, master_volume, animate_background):
        self._active_profile()["columns"] = int(columns)
        self.config["settings"]["master_volume"] = float(master_volume)
        self.config["settings"]["animate_background"] = bool(animate_background)
        self._apply_global_settings()
        self._save_and_refresh()

    def export_config_dialog(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Config", "config.json", "JSON (*.json)")
        if not path:
            return
        try:
            config_manager.export_config(self.config, path)
            self.status.setText("✓ Config di-export")
            self._status_timer.start(2500)
        except Exception as e:
            notify(self, "Export Gagal", str(e))

    def import_config_dialog(self) -> bool:
        path, _ = QFileDialog.getOpenFileName(self, "Import Config", "", "JSON (*.json)")
        if not path:
            return False
        try:
            data = config_manager.import_config(path)
        except Exception as e:
            notify(self, "Import Gagal", f"File tidak bisa dibaca:\n{e}")
            return False
        if not confirm(self, "Import Config",
                       "Pengaturan & tombol saat ini akan diganti dengan isi file ini. Lanjutkan?", "Import"):
            return False
        self.config = data
        self._apply_global_settings()
        self._save_and_refresh()
        return True

    def _save_and_refresh(self):
        self._persist()
        self._refresh_profile_bar()
        self._render_buttons()
        self._register_all_hotkeys()
        self._update_hint()

    def closeEvent(self, event):
        self.hotkey_manager.unregister_all()
        config_manager.save_config(self.config)
        super().closeEvent(event)
