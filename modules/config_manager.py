"""
config_manager.py
Menyimpan/memuat konfigurasi ke config.json di folder yang sama dengan
aplikasi (portable). Mendukung banyak Profile — tiap profile punya set
tombol sendiri, bisa dipindah-pindah dari dropdown di header.
"""
import json
import os
import sys
import uuid


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(get_app_dir(), "config.json")


def new_profile(name: str) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "columns": 4, "buttons": []}


def _default_config() -> dict:
    profile = new_profile("Profile 1")
    return {"active_profile": profile["id"], "profiles": [profile]}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return _migrate(data)
        except Exception as e:
            print(f"Gagal membaca config.json, memakai default. Error: {e}")
    return _default_config()


def _migrate(data: dict) -> dict:
    """Config lama (flat: columns+buttons) diubah jadi 1 profile otomatis."""
    if "profiles" in data and data.get("profiles"):
        for p in data["profiles"]:
            p.setdefault("id", str(uuid.uuid4()))
            p.setdefault("name", "Profile")
            p.setdefault("columns", 4)
            p.setdefault("buttons", [])
        data.setdefault("active_profile", data["profiles"][0]["id"])
        return data
    if "buttons" in data:
        profile = new_profile("Profile 1")
        profile["columns"] = data.get("columns", 4)
        profile["buttons"] = data.get("buttons", [])
        return {"active_profile": profile["id"], "profiles": [profile]}
    return _default_config()


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_active_profile(config: dict) -> dict:
    for p in config["profiles"]:
        if p["id"] == config.get("active_profile"):
            return p
    return config["profiles"][0]


def new_button(button_id: str) -> dict:
    return {
        "id": button_id,
        "label": "Tombol Baru",
        "color": "#6470ff",
        "action_type": "sound",  # sound | app
        "sound_path": "",
        "sound_volume": 1.0,
        "sound_start_ms": 0,
        "sound_end_ms": None,   # None = putar sampai selesai
        "app_path": "",
        "app_args": "",
        "hotkey": ""
    }
