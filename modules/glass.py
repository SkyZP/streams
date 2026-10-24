"""
glass.py
Komponen visual bergaya "Liquid Glass" untuk StreamPad.

Catatan teknis: Qt tidak bisa mem-blur isi desktop/jendela lain di belakang
window aplikasi. Jadi efek kaca di sini DISIMULASIKAN: background aplikasi
berupa gumpalan warna yang bergerak pelan (seperti cairan), lalu semua
panel/tombol digambar semi-transparan di atasnya dengan:
  - isian gradasi tipis (kaca),
  - kilau spekular di bagian atas,
  - pantulan cahaya lembut di bagian bawah,
  - garis tepi (rim) terang di sudut atas-kiri & bawah-kanan,
  - glow berwarna saat hover.
"""
import math

from PySide6.QtCore import (
    Qt, QRectF, QPointF, QSize, QTimer, QVariantAnimation, QEasingCurve, Signal
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QBrush, QPen, QLinearGradient,
    QRadialGradient, QFont, QFontMetrics
)
from PySide6.QtWidgets import QWidget, QPushButton, QDialog

ACCENT = QColor(100, 112, 255)


def _a(value) -> int:
    """Alpha aman: dibatasi 0..255."""
    return max(0, min(255, int(value)))


# ------------------------------------------------------------------ Tween
class Tween(QVariantAnimation):
    """Animasi nilai float sederhana yang otomatis memanggil update() pemiliknya."""

    def __init__(self, owner, duration=220, easing=QEasingCurve.Type.OutCubic, initial=0.0):
        super().__init__(owner)
        self._owner = owner
        self.current = float(initial)
        self.setDuration(duration)
        self.setEasingCurve(easing)
        self.valueChanged.connect(self._store)

    def _store(self, value):
        self.current = float(value)
        self._owner.update()

    def go(self, target: float):
        self.stop()
        self.setStartValue(float(self.current))
        self.setEndValue(float(target))
        self.start()

    def jump(self, value: float):
        self.stop()
        self.current = float(value)
        self._owner.update()


# ------------------------------------------------------------------ Painting helpers
# (cx, cy, radius_factor, (r, g, b), amplitudo_x, amplitudo_y, kecepatan)
_BLOBS = [
    (0.10, 0.08, 0.60, (100, 112, 255), 0.06, 0.05, 1.0),
    (0.90, 0.20, 0.55, (168, 85, 247), 0.05, 0.07, 0.8),
    (0.72, 0.95, 0.65, (236, 72, 153), 0.07, 0.04, 1.2),
    (0.18, 0.88, 0.50, (34, 211, 238), 0.05, 0.06, 0.9),
]


def paint_liquid_backdrop(p: QPainter, rect, phase: float):
    """Gambar background gelap + gumpalan warna yang bergeser pelan mengikuti `phase`."""
    p.fillRect(rect, QColor(8, 9, 14))
    w = float(rect.width())
    h = float(rect.height())
    base = max(w, h)
    for cx, cy, rf, col, ax, ay, speed in _BLOBS:
        x = (cx + ax * math.sin(phase * speed)) * w
        y = (cy + ay * math.cos(phase * speed * 1.3)) * h
        grad = QRadialGradient(QPointF(x, y), rf * base)
        grad.setColorAt(0.0, QColor(col[0], col[1], col[2], 125))
        grad.setColorAt(0.5, QColor(col[0], col[1], col[2], 42))
        grad.setColorAt(1.0, QColor(col[0], col[1], col[2], 0))
        p.fillRect(rect, QBrush(grad))


def paint_glass(p: QPainter, rect: QRectF, radius: float, tint=None, strength=1.0, rim=1.0):
    """
    Gambar satu permukaan kaca. `tint` (QColor) memberi warna pada kaca;
    `strength` mengatur keburaman/ketebalan; `rim` mengatur terang garis tepi.
    """
    if strength <= 0.001:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    # 1) isian dasar
    fill = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    if tint is None:
        fill.setColorAt(0.0, QColor(255, 255, 255, _a(36 * strength)))
        fill.setColorAt(1.0, QColor(255, 255, 255, _a(13 * strength)))
    else:
        top = QColor(tint)
        top.setAlpha(_a(105 * strength))
        bottom = QColor(tint).darker(150)
        bottom.setAlpha(_a(165 * strength))
        fill.setColorAt(0.0, top)
        fill.setColorAt(1.0, bottom)
    p.fillPath(path, QBrush(fill))

    p.setClipPath(path)

    # 2) kilau spekular di bagian atas
    hl_rect = QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.56)
    hl = QLinearGradient(hl_rect.topLeft(), hl_rect.bottomLeft())
    hl.setColorAt(0.0, QColor(255, 255, 255, _a(78 * strength)))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillRect(hl_rect, QBrush(hl))

    # 3) pantulan lembut di bagian bawah
    bl_rect = QRectF(rect.left(), rect.bottom() - rect.height() * 0.38, rect.width(), rect.height() * 0.38)
    bl = QLinearGradient(bl_rect.bottomLeft(), bl_rect.topLeft())
    bl.setColorAt(0.0, QColor(255, 255, 255, _a(26 * strength)))
    bl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillRect(bl_rect, QBrush(bl))

    p.setClipping(False)

    # 4) garis tepi (rim) terang di dua sudut berlawanan
    rim_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    rim_grad.setColorAt(0.00, QColor(255, 255, 255, _a(185 * rim)))
    rim_grad.setColorAt(0.35, QColor(255, 255, 255, _a(42 * rim)))
    rim_grad.setColorAt(0.65, QColor(255, 255, 255, _a(28 * rim)))
    rim_grad.setColorAt(1.00, QColor(255, 255, 255, _a(130 * rim)))
    p.setPen(QPen(QBrush(rim_grad), 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6), radius, radius)
    p.restore()


def paint_glow(p: QPainter, body: QRectF, radius: float, color: QColor, amount: float,
               steps: int = 7, spread: float = 1.6):
    """Cahaya berwarna lembut di sekeliling `body` (dibutuhkan margin >= steps*spread)."""
    if amount <= 0.01:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(1, steps + 1):
        falloff = (1.0 - i / (steps + 1.0)) ** 2
        c = QColor(color.red(), color.green(), color.blue(), _a(amount * 46 * falloff))
        p.setPen(QPen(c, spread * 1.3))
        grow = i * spread
        p.drawRoundedRect(body.adjusted(-grow, -grow, grow, grow), radius + grow, radius + grow)
    p.restore()


# ------------------------------------------------------------------ Background
class LiquidBackground(QWidget):
    """Widget root: background cair yang bergerak pelan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        win = self.window()
        if win is None or win.isMinimized() or not win.isVisible():
            return
        self._phase += 0.014
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        paint_liquid_backdrop(p, self.rect(), self._phase)


# ------------------------------------------------------------------ Panel
class GlassPanel(QWidget):
    def __init__(self, radius=22, strength=1.0, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._strength = strength

    def paintEvent(self, event):
        p = QPainter(self)
        paint_glass(p, QRectF(self.rect()).adjusted(1, 1, -1, -1), self._radius, None, self._strength)


# ------------------------------------------------------------------ Pill button
class GlassPillButton(QPushButton):
    """Tombol pill kaca. variant: 'normal' | 'primary' | 'danger'."""
    MARGIN = 4

    def __init__(self, text="", variant="normal", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(44)
        self._hover = Tween(self, 200)
        self._press = Tween(self, 120)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        return QSize(max(48, fm.horizontalAdvance(self.text()) + 44), 44)

    def _tint(self):
        if self.variant == "primary":
            return QColor(112, 100, 255)
        if self.variant == "danger":
            return QColor(237, 66, 69)
        return None

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
        shrink = 1.5 * self._press.current
        body = body.adjusted(shrink, shrink, -shrink, -shrink)
        radius = body.height() / 2.0
        tint = self._tint()
        enabled = self.isEnabled()
        hover = self._hover.current

        if tint is not None and enabled:
            paint_glow(p, body, radius, tint, 0.25 + 0.75 * hover, steps=3, spread=1.3)
        base = 1.0 if tint is not None else 0.9
        strength = (base + 0.4 * hover) if enabled else 0.65
        paint_glass(p, body, radius, tint, strength)

        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 240 if enabled else 170))
        p.drawText(body, Qt.AlignmentFlag.AlignCenter, self.text())


# ------------------------------------------------------------------ Tab (profile)
class GlassTab(QPushButton):
    """Tab untuk memilih profile. Yang terpilih tampil sebagai kaca bercahaya."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(40)
        self._sel = Tween(self, 260, QEasingCurve.Type.OutCubic)
        self._hover = Tween(self, 160)
        self.toggled.connect(lambda checked: self._sel.go(1.0 if checked else 0.0))

    def set_checked_silent(self, value: bool):
        self.blockSignals(True)
        self.setChecked(value)
        self.blockSignals(False)
        self._sel.jump(1.0 if value else 0.0)

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        return QSize(fm.horizontalAdvance(self.text()) + 40, 40)

    def enterEvent(self, event):
        self._hover.go(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover.go(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        body = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radius = body.height() / 2.0
        sel = max(0.0, min(1.0, self._sel.current))
        hover = self._hover.current

        if sel > 0.01:
            paint_glow(p, body, radius, ACCENT, 0.5 * sel, steps=2, spread=1.0)
            paint_glass(p, body, radius, QColor(124, 131, 255), sel * 1.15)
        elif hover > 0.01:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, _a(20 * hover)))
            p.drawRoundedRect(body, radius, radius)

        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        alpha = 165 + int(90 * max(sel, hover * 0.5))
        p.setPen(QColor(255, 255, 255, _a(alpha)))
        p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, self.text())


# ------------------------------------------------------------------ Liquid toggle
class GlassToggle(QWidget):
    """
    Toggle dua sisi (Jalankan / Edit). Thumb kaca meluncur dengan efek cairan:
    melar saat bergerak lalu 'memantul' sedikit saat berhenti.
    """
    toggled = Signal(bool)  # True = sisi kanan (edit)

    def __init__(self, left_text="▶  Jalankan", right_text="✎  Edit", parent=None):
        super().__init__(parent)
        self.left_text = left_text
        self.right_text = right_text
        self._index = 0
        self.setFixedSize(236, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pos = Tween(self, 520, QEasingCurve.Type.OutBack, initial=0.0)

    def index(self) -> int:
        return self._index

    def set_index(self, idx: int, emit: bool = True):
        if idx == self._index:
            return
        self._index = idx
        self._pos.go(float(idx))
        if emit:
            self.toggled.emit(idx == 1)

    def mousePressEvent(self, event):
        self.set_index(0 if event.position().x() < self.width() / 2.0 else 1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        full = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        paint_glass(p, full, full.height() / 2.0, None, 0.95)

        pad = 5.0
        seg_w = (full.width() - 2 * pad) / 2.0
        th = full.height() - 2 * pad
        pos = self._pos.current
        stretch = max(0.0, 4.0 * pos * (1.0 - pos))  # 0 di ujung, 1 di tengah gerakan
        extra = seg_w * 0.30 * stretch
        squish = th * 0.10 * stretch

        x = full.left() + pad + pos * seg_w - extra / 2.0
        thumb = QRectF(x, full.top() + pad + squish / 2.0, seg_w + extra, th - squish)
        paint_glow(p, thumb, thumb.height() / 2.0, ACCENT, 0.7, steps=3, spread=1.4)
        paint_glass(p, thumb, thumb.height() / 2.0, QColor(112, 100, 255), 1.55)

        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        left_rect = QRectF(full.left() + pad, full.top() + pad, seg_w, th)
        right_rect = QRectF(full.left() + pad + seg_w, full.top() + pad, seg_w, th)
        clamp = max(0.0, min(1.0, pos))
        p.setPen(QColor(255, 255, 255, _a(255 - 110 * clamp)))
        p.drawText(left_rect, Qt.AlignmentFlag.AlignCenter, self.left_text)
        p.setPen(QColor(255, 255, 255, _a(145 + 110 * clamp)))
        p.drawText(right_rect, Qt.AlignmentFlag.AlignCenter, self.right_text)


# ------------------------------------------------------------------ Dialog
class GlassDialog(QDialog):
    """Dialog dengan background cair + bingkai kaca, fade-in halus saat dibuka."""

    def paintEvent(self, event):
        p = QPainter(self)
        paint_liquid_backdrop(p, self.rect(), 1.7)
        paint_glass(p, QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, None, 0.55, rim=0.7)

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(lambda v: self.setWindowOpacity(float(v)))
        anim.start()
        self._fade_anim = anim
