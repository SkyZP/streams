"""
glass.py
Komponen visual bergaya kaca bening (monokrom) untuk StreamPad.

Qt tidak bisa mem-blur isi desktop di belakang window, jadi efeknya
disimulasikan: background aplikasi berupa gumpalan putih/abu yang di-blur
di atas hitam, lalu semua panel/tombol digambar transparan (hampir bening)
dengan kilau tipis di atas dan garis tepi halus. Tanpa warna-warni.
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

ACCENT = QColor(255, 255, 255)


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
# (cx, cy, radius_factor, gray, alpha, amplitudo_x, amplitudo_y, kecepatan)
_BLOBS = [
    (0.12, 0.10, 0.62, 255, 46, 0.06, 0.05, 1.0),
    (0.92, 0.22, 0.55, 205, 34, 0.05, 0.07, 0.8),
    (0.70, 0.98, 0.68, 255, 40, 0.07, 0.04, 1.2),
    (0.16, 0.92, 0.50, 170, 34, 0.05, 0.06, 0.9),
]


def paint_liquid_backdrop(p: QPainter, rect, phase: float):
    """Background hitam dengan gumpalan putih/abu yang di-blur dan bergeser pelan."""
    p.fillRect(rect, QColor(9, 9, 11))
    w = float(rect.width())
    h = float(rect.height())
    base = max(w, h)
    for cx, cy, rf, g, alpha, ax, ay, speed in _BLOBS:
        x = (cx + ax * math.sin(phase * speed)) * w
        y = (cy + ay * math.cos(phase * speed * 1.3)) * h
        grad = QRadialGradient(QPointF(x, y), rf * base)
        grad.setColorAt(0.0, QColor(g, g, g, alpha))
        grad.setColorAt(0.5, QColor(g, g, g, int(alpha * 0.35)))
        grad.setColorAt(1.0, QColor(g, g, g, 0))
        p.fillRect(rect, QBrush(grad))


def paint_glass(p: QPainter, rect: QRectF, radius: float, tint=None, strength=1.0, rim=1.0):
    """
    Satu permukaan kaca bening. `tint` hanya dipakai untuk aksen halus
    (tombol hapus = kemerahan); selain itu kaca selalu netral putih.
    `strength` mengatur ketebalan, `rim` mengatur terang garis tepi.
    """
    if strength <= 0.001:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    # 1) isian dasar: hampir bening
    fill = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    if tint is None:
        fill.setColorAt(0.0, QColor(255, 255, 255, _a(26 * strength)))
        fill.setColorAt(1.0, QColor(255, 255, 255, _a(10 * strength)))
    else:
        fill.setColorAt(0.0, QColor(tint.red(), tint.green(), tint.blue(), _a(52 * strength)))
        fill.setColorAt(1.0, QColor(tint.red(), tint.green(), tint.blue(), _a(26 * strength)))
    p.fillPath(path, QBrush(fill))

    p.setClipPath(path)

    # 2) kilau tipis di bagian atas
    hl_rect = QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.45)
    hl = QLinearGradient(hl_rect.topLeft(), hl_rect.bottomLeft())
    hl.setColorAt(0.0, QColor(255, 255, 255, _a(34 * strength)))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillRect(hl_rect, QBrush(hl))

    p.setClipping(False)

    # 3) garis tepi halus
    rim_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    rim_grad.setColorAt(0.00, QColor(255, 255, 255, _a(120 * rim)))
    rim_grad.setColorAt(0.40, QColor(255, 255, 255, _a(34 * rim)))
    rim_grad.setColorAt(0.65, QColor(255, 255, 255, _a(26 * rim)))
    rim_grad.setColorAt(1.00, QColor(255, 255, 255, _a(80 * rim)))
    p.setPen(QPen(QBrush(rim_grad), 1.0))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
    p.restore()


def paint_glow(p: QPainter, body: QRectF, radius: float, color: QColor, amount: float,
               steps: int = 7, spread: float = 1.6):
    """Cahaya lembut di sekeliling `body` (dibutuhkan margin >= steps*spread)."""
    if amount <= 0.01:
        return
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(1, steps + 1):
        falloff = (1.0 - i / (steps + 1.0)) ** 2
        c = QColor(color.red(), color.green(), color.blue(), _a(amount * 30 * falloff))
        p.setPen(QPen(c, spread * 1.3))
        grow = i * spread
        p.drawRoundedRect(body.adjusted(-grow, -grow, grow, grow), radius + grow, radius + grow)
    p.restore()


def draw_icon(p: QPainter, kind: str, rect: QRectF, color: QColor, width: float = 2.0):
    """Ikon garis monokrom: 'sound' (speaker), 'app' (grid 2x2), 'pad' (grid 4 kotak)."""
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    if kind == "sound":
        sp = QPainterPath()
        sp.moveTo(x + w * 0.10, y + h * 0.38)
        sp.lineTo(x + w * 0.30, y + h * 0.38)
        sp.lineTo(x + w * 0.52, y + h * 0.18)
        sp.lineTo(x + w * 0.52, y + h * 0.82)
        sp.lineTo(x + w * 0.30, y + h * 0.62)
        sp.lineTo(x + w * 0.10, y + h * 0.62)
        sp.closeSubpath()
        p.drawPath(sp)
        p.drawArc(QRectF(x + w * 0.42, y + h * 0.30, w * 0.26, h * 0.40), -60 * 16, 120 * 16)
        p.drawArc(QRectF(x + w * 0.42, y + h * 0.14, w * 0.46, h * 0.72), -60 * 16, 120 * 16)
    else:
        gap = w * 0.10
        cell = (min(w, h) - gap) / 2.0
        ox = x + (w - (cell * 2 + gap)) / 2.0
        oy = y + (h - (cell * 2 + gap)) / 2.0
        for r in range(2):
            for c in range(2):
                cr = QRectF(ox + c * (cell + gap), oy + r * (cell + gap), cell, cell)
                p.drawRoundedRect(cr, cell * 0.28, cell * 0.28)
    p.restore()


# ------------------------------------------------------------------ Background
class LiquidBackground(QWidget):
    """Widget root: background cair yang bergerak pelan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self._animate = True
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_animated(self, value: bool):
        self._animate = bool(value)
        self.update()

    def _tick(self):
        if not self._animate:
            return
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
        if self.variant == "danger":
            return QColor(255, 99, 99)
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

        primary = self.variant == "primary"
        if enabled and (primary or hover > 0.01):
            paint_glow(p, body, radius, QColor(255, 255, 255), (0.35 if primary else 0.0) + 0.65 * hover,
                       steps=3, spread=1.3)
        base = 1.9 if primary else 1.0
        strength = (base + 0.7 * hover) if enabled else 0.6
        paint_glass(p, body, radius, tint, strength, rim=1.25 if primary else 1.0)

        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 245 if enabled else 130))
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
            paint_glass(p, body, radius, None, sel * 1.9, rim=1.2)
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
    Toggle dua sisi (Jalankan / Edit). Thumb kaca meluncur dengan efek cairan
    (sedikit melar saat bergerak). Semua gambar dijaga di dalam batas widget
    supaya tidak pernah terpotong.
    """
    toggled = Signal(bool)  # True = sisi kanan (edit)
    MARGIN = 4

    def __init__(self, left_text="▶  Jalankan", right_text="✎  Edit", parent=None):
        super().__init__(parent)
        self.left_text = left_text
        self.right_text = right_text
        self._index = 0
        self.setFixedSize(252, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pos = Tween(self, 380, QEasingCurve.Type.InOutCubic, initial=0.0)

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
        m = self.MARGIN
        full = QRectF(self.rect()).adjusted(m, m, -m, -m)
        paint_glass(p, full, full.height() / 2.0, None, 1.0)

        pad = 4.0
        inner = full.adjusted(pad, pad, -pad, -pad)
        seg_w = inner.width() / 2.0
        pos = max(0.0, min(1.0, self._pos.current))
        stretch = max(0.0, 4.0 * pos * (1.0 - pos))  # 0 di ujung, 1 di tengah gerakan
        extra = seg_w * 0.22 * stretch

        left = inner.left() + pos * seg_w - extra * pos
        right = inner.left() + (pos + 1.0) * seg_w + extra * (1.0 - pos)
        thumb = QRectF(max(inner.left(), left), inner.top(),
                       min(inner.right(), right) - max(inner.left(), left), inner.height())
        paint_glass(p, thumb, thumb.height() / 2.0, None, 2.2, rim=1.3)

        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        left_rect = QRectF(inner.left(), inner.top(), seg_w, inner.height())
        right_rect = QRectF(inner.left() + seg_w, inner.top(), seg_w, inner.height())
        p.setPen(QColor(255, 255, 255, _a(255 - 115 * pos)))
        p.drawText(left_rect, Qt.AlignmentFlag.AlignCenter, self.left_text)
        p.setPen(QColor(255, 255, 255, _a(140 + 115 * pos)))
        p.drawText(right_rect, Qt.AlignmentFlag.AlignCenter, self.right_text)


# ------------------------------------------------------------------ Switch
class GlassSwitch(QWidget):
    """Saklar on/off kecil bergaya kaca."""
    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self.setFixedSize(54, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pos = Tween(self, 200, QEasingCurve.Type.OutCubic, initial=1.0 if checked else 0.0)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool):
        self._checked = bool(value)
        self._pos.go(1.0 if value else 0.0)

    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        body = QRectF(self.rect()).adjusted(2, 4, -2, -4)
        pos = self._pos.current
        paint_glass(p, body, body.height() / 2.0, None, 1.0 + 1.2 * pos)
        d = body.height() - 6
        x = body.left() + 3 + pos * (body.width() - d - 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, _a(150 + 100 * pos)))
        p.drawEllipse(QRectF(x, body.top() + 3, d, d))


# ------------------------------------------------------------------ Icon widget
class IconWidget(QWidget):
    def __init__(self, kind="pad", size=56, parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        draw_icon(p, self._kind, QRectF(self.rect()).adjusted(4, 4, -4, -4),
                  QColor(255, 255, 255, 200), 2.2)


# ------------------------------------------------------------------ Dialog
class GlassDialog(QDialog):
    """Dialog dengan background cair + bingkai kaca, fade-in halus saat dibuka."""

    def paintEvent(self, event):
        p = QPainter(self)
        paint_liquid_backdrop(p, self.rect(), 1.7)
        paint_glass(p, QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, None, 0.5, rim=0.6)

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
