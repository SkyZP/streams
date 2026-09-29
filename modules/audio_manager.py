"""
audio_manager.py
Mengelola pemutaran sound effect dari file di komputer user, termasuk
memutar hanya sebagian (trim/potong) sesuai start_ms & end_ms yang diatur
di dialog konfigurasi tombol.

Mendukung beberapa suara diputar bersamaan (overlap), seperti Stream Deck
asli, dengan membuat QMediaPlayer baru tiap kali tombol ditekan dan
membersihkannya otomatis setelah selesai.
"""
from PySide6.QtCore import QUrl, QObject, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioManager(QObject):
    def __init__(self):
        super().__init__()
        self._active = []  # simpan referensi entry supaya tidak di-GC saat masih main

    def play(self, file_path: str, volume: float = 1.0, start_ms: int = 0, end_ms=None):
        """
        Putar file_path dari posisi start_ms (default awal) sampai end_ms
        (dalam milidetik). Kalau end_ms None/0/<=start_ms, diputar sampai
        selesai secara natural.
        """
        if not file_path:
            return

        player = QMediaPlayer()
        output = QAudioOutput()
        output.setVolume(max(0.0, min(1.0, volume)))
        player.setAudioOutput(output)

        entry = {"player": player, "output": output, "done": False, "started": False}
        self._active.append(entry)

        def cleanup():
            if entry["done"]:
                return
            entry["done"] = True
            if entry in self._active:
                self._active.remove(entry)
            player.stop()
            player.deleteLater()
            output.deleteLater()

        def on_status(status):
            if status == QMediaPlayer.MediaStatus.LoadedMedia and not entry["started"]:
                entry["started"] = True
                if start_ms and start_ms > 0:
                    player.setPosition(int(start_ms))
                player.play()
                if end_ms and end_ms > start_ms:
                    QTimer.singleShot(int(end_ms - start_ms), cleanup)
            elif status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
                cleanup()

        player.mediaStatusChanged.connect(on_status)
        player.setSource(QUrl.fromLocalFile(file_path))

    def stop_all(self):
        for entry in list(self._active):
            entry["player"].stop()
        self._active.clear()
