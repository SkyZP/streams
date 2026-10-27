"""
hotkey_manager.py
Hotkey global memakai API resmi Windows `RegisterHotKey` (lewat ctypes).

Kenapa bukan library `keyboard`: library itu memasang "hook" ke SEMUA ketikan
di Windows, perilaku yang sama dengan keylogger, sehingga antivirus sering
menandai programnya sebagai trojan (false positive). RegisterHotKey hanya
memberi tahu aplikasi saat kombinasi tombol yang didaftarkan ditekan, tanpa
membaca ketikan lain, jadi jauh lebih aman dan tidak memicu antivirus.

DumbPad (QMK) terbaca Windows sebagai keyboard USB biasa. Tiap tombol fisik
mengirim kode tombol tertentu (disarankan F13-F24 supaya tidak bentrok).

Catatan: tombol yang didaftarkan sebagai hotkey tidak diteruskan ke aplikasi
lain selama StreamPad berjalan.
"""
import sys

from PySide6.QtCore import Qt, QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000

_MODIFIERS = {"ctrl": MOD_CONTROL, "control": MOD_CONTROL, "alt": MOD_ALT,
              "shift": MOD_SHIFT, "win": MOD_WIN, "windows": MOD_WIN}

_NAMED_VK = {
    "space": 0x20, "enter": 0x0D, "tab": 0x09, "backspace": 0x08,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23,
    "page up": 0x21, "page down": 0x22, "left": 0x25, "up": 0x26,
    "right": 0x27, "down": 0x28, "pause": 0x13, "print screen": 0x2C,
    "scroll lock": 0x91, "caps lock": 0x14, "num lock": 0x90,
}

# Qt.Key -> nama tombol
_QT_NAMES = {
    Qt.Key.Key_Space: "space", Qt.Key.Key_Return: "enter", Qt.Key.Key_Enter: "enter",
    Qt.Key.Key_Tab: "tab", Qt.Key.Key_Backspace: "backspace", Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Delete: "delete", Qt.Key.Key_Home: "home", Qt.Key.Key_End: "end",
    Qt.Key.Key_PageUp: "page up", Qt.Key.Key_PageDown: "page down",
    Qt.Key.Key_Left: "left", Qt.Key.Key_Up: "up", Qt.Key.Key_Right: "right",
    Qt.Key.Key_Down: "down", Qt.Key.Key_Pause: "pause", Qt.Key.Key_Print: "print screen",
    Qt.Key.Key_ScrollLock: "scroll lock", Qt.Key.Key_CapsLock: "caps lock",
    Qt.Key.Key_NumLock: "num lock",
}
_MODIFIER_KEYS = {Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
                  Qt.Key.Key_Meta, Qt.Key.Key_AltGr}


def key_name_from_event(event):
    """Ubah QKeyEvent jadi teks hotkey, misal 'f13' atau 'ctrl+shift+a'. None = belum valid."""
    key = event.key()
    if key in _MODIFIER_KEYS or key == Qt.Key.Key_unknown:
        return None
    if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F24:
        name = f"f{key - Qt.Key.Key_F1 + 1}"
    elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
        name = chr(ord("a") + key - Qt.Key.Key_A)
    elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
        name = chr(ord("0") + key - Qt.Key.Key_0)
    elif key in _QT_NAMES:
        name = _QT_NAMES[key]
    else:
        return None
    mods = event.modifiers()
    parts = []
    if mods & Qt.KeyboardModifier.ControlModifier:
        parts.append("ctrl")
    if mods & Qt.KeyboardModifier.AltModifier:
        parts.append("alt")
    if mods & Qt.KeyboardModifier.ShiftModifier:
        parts.append("shift")
    if mods & Qt.KeyboardModifier.MetaModifier:
        parts.append("win")
    return "+".join(parts + [name])


def parse_hotkey(text: str):
    """'ctrl+f13' -> (modifier_flags, virtual_key). Melempar ValueError kalau tidak dikenal."""
    mods, vk = 0, None
    for part in [p.strip().lower() for p in text.split("+") if p.strip()]:
        if part in _MODIFIERS:
            mods |= _MODIFIERS[part]
        elif part.startswith("f") and part[1:].isdigit() and 1 <= int(part[1:]) <= 24:
            vk = 0x70 + int(part[1:]) - 1
        elif len(part) == 1 and part.isalnum():
            vk = ord(part.upper())
        elif part in _NAMED_VK:
            vk = _NAMED_VK[part]
        else:
            raise ValueError(f"tombol '{part}' tidak dikenal")
    if vk is None:
        raise ValueError("tidak ada tombol utama")
    return mods, vk


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, on_hotkey):
        super().__init__()
        self._on_hotkey = on_hotkey

    def nativeEventFilter(self, event_type, message):
        if IS_WINDOWS and event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self._on_hotkey(int(msg.wParam))
                return True, 0
        return False, 0


class HotkeyManager:
    def __init__(self):
        self._by_text = {}   # hotkey_str -> id
        self._callbacks = {}  # id -> callback
        self._next_id = 1
        self._filter = None
        if IS_WINDOWS:
            self._filter = _HotkeyFilter(self._dispatch)
            QApplication.instance().installNativeEventFilter(self._filter)

    def _dispatch(self, hotkey_id: int):
        cb = self._callbacks.get(hotkey_id)
        if cb:
            cb()

    def register(self, hotkey: str, callback):
        if not hotkey or not IS_WINDOWS:
            return
        self.unregister(hotkey)
        try:
            mods, vk = parse_hotkey(hotkey)
            hotkey_id = self._next_id
            self._next_id += 1
            if not ctypes.windll.user32.RegisterHotKey(None, hotkey_id, mods | MOD_NOREPEAT, vk):
                raise OSError("sudah dipakai aplikasi lain")
            self._by_text[hotkey] = hotkey_id
            self._callbacks[hotkey_id] = callback
        except Exception as e:
            print(f"Gagal mendaftarkan hotkey '{hotkey}': {e}")

    def unregister(self, hotkey: str):
        hotkey_id = self._by_text.pop(hotkey, None)
        if hotkey_id is not None:
            self._callbacks.pop(hotkey_id, None)
            try:
                ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            except Exception:
                pass

    def unregister_all(self):
        for hotkey in list(self._by_text.keys()):
            self.unregister(hotkey)
