"""
config_manager.py
Menyimpan dan memuat konfigurasi tombol ke file JSON di folder yang sama
dengan aplikasi (portable, tanpa perlu instalasi/registry).
"""
import json
import os
import sys


def get_app_dir() -> str:
    """Folder tempat file .exe / script berada, supaya config.json ikut portable."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(get_app_dir(), "config.json")

DEFAULT_CONFIG = {
    "columns": 4,
    "buttons": []
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("columns", 4)
                data.setdefault("buttons", [])
                return data
        except Exception as e:
            print(f"Gagal membaca config.json, memakai default. Error: {e}")
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def new_button(button_id: str) -> dict:
    return {
        "id": button_id,
        "label": "Tombol Baru",
        "color": "#3a3f4b",
        # sound | volume_up | volume_down | volume_mute | volume_set
        "action_type": "sound",
        "sound_path": "",
        "sound_volume": 1.0,
        "volume_step": 0.05,
        "volume_level": 0.5,
        "hotkey": ""
    }
