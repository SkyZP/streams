"""
audio_manager.py
Mengelola pemutaran sound effect dari file di komputer user.
Mendukung beberapa suara diputar bersamaan (overlap), seperti Stream Deck asli,
dengan membuat QMediaPlayer baru tiap kali tombol ditekan dan membersihkannya
otomatis setelah selesai.
"""
from PySide6.QtCore import QUrl, QObject
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioManager(QObject):
    def __init__(self):
        super().__init__()
        self._active = []  # simpan referensi (player, output) supaya tidak di-GC saat masih main

    def play(self, file_path: str, volume: float = 1.0):
        if not file_path:
            return

        player = QMediaPlayer()
        output = QAudioOutput()
        output.setVolume(max(0.0, min(1.0, volume)))
        player.setAudioOutput(output)
        player.setSource(QUrl.fromLocalFile(file_path))

        entry = (player, output)
        self._active.append(entry)

        def _cleanup(status):
            if status in (
                QMediaPlayer.MediaStatus.EndOfMedia,
                QMediaPlayer.MediaStatus.InvalidMedia,
            ):
                if entry in self._active:
                    self._active.remove(entry)
                player.deleteLater()
                output.deleteLater()

        player.mediaStatusChanged.connect(_cleanup)
        player.play()

    def stop_all(self):
        for player, _ in list(self._active):
            player.stop()
        self._active.clear()
