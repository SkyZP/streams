"""
volume_manager.py
Kontrol volume master Windows menggunakan pycaw (membungkus Core Audio API).
Hanya berjalan di Windows.
"""
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class VolumeManager:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def get_volume(self) -> float:
        """Volume dalam skala 0.0 - 1.0"""
        return self.volume.GetMasterVolumeLevelScalar()

    def set_volume(self, value: float):
        value = max(0.0, min(1.0, value))
        self.volume.SetMasterVolumeLevelScalar(value, None)

    def change_volume(self, delta: float):
        self.set_volume(self.get_volume() + delta)

    def is_muted(self) -> bool:
        return bool(self.volume.GetMute())

    def set_mute(self, mute: bool):
        self.volume.SetMute(1 if mute else 0, None)

    def toggle_mute(self):
        self.set_mute(not self.is_muted())
