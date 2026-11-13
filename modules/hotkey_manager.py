"""
hotkey_manager.py
Mendaftarkan hotkey global menggunakan library `keyboard`.

Kenapa ini bisa "terintegrasi" dengan DumbPad:
DumbPad menjalankan firmware QMK dan terbaca oleh Windows sebagai keyboard
USB HID biasa. Jadi setiap tombol fisik di DumbPad = mengirim kode tombol
tertentu (misalnya F13, F14, atau tombol lain yang kamu program di keymap
QMK-nya). Aplikasi ini mendengarkan kode tombol tersebut secara global
(walau window sedang tidak fokus) dan menjalankan aksi yang sudah diatur.

Saran: program keymap DumbPad-mu memakai tombol F13-F24 (rentang yang jarang
dipakai aplikasi lain) supaya tidak bentrok dengan shortcut aplikasi lain.
"""
import keyboard


class HotkeyManager:
    def __init__(self):
        self._registered = {}  # hotkey_str -> handle dari library keyboard

    def register(self, hotkey: str, callback):
        if not hotkey:
            return
        self.unregister(hotkey)
        try:
            handle = keyboard.add_hotkey(hotkey, callback)
            self._registered[hotkey] = handle
        except Exception as e:
            print(f"Gagal mendaftarkan hotkey '{hotkey}': {e}")

    def unregister(self, hotkey: str):
        handle = self._registered.pop(hotkey, None)
        if handle is not None:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass

    def unregister_all(self):
        for hotkey in list(self._registered.keys()):
            self.unregister(hotkey)

    @staticmethod
    def capture_next_key(callback):
        """
        Menunggu SATU tombol berikutnya ditekan (dari keyboard biasa ATAU dari
        DumbPad, karena keduanya sama-sama terbaca sebagai keyboard event),
        lalu memanggil callback(nama_tombol). Dipakai di dialog konfigurasi
        supaya user tinggal tekan tombol di DumbPad untuk merekam hotkey-nya.
        """
        def _on_event(event):
            if event.event_type == keyboard.KEY_DOWN:
                keyboard.unhook(_on_event)
                callback(event.name)

        keyboard.hook(_on_event)
