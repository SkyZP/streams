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


DEFAULT_SETTINGS = {
    "master_volume": 1.0,      # pengali volume untuk semua suara (0.0 - 1.0)
    "animate_background": True,
}


def _is_writable_dir(path: str) -> bool:
    try:
        probe = os.path.join(path, ".streampad_write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False


def _resolve_config_path() -> str:
    """
    config.json disimpan di sebelah aplikasi (portable). Kalau foldernya tidak
    bisa ditulis (misal .exe dijalankan langsung dari dalam file .zip atau
    folder read-only), otomatis pindah ke %APPDATA%\\StreamPad supaya
    pengaturan tetap tersimpan.
    """
    app_dir = get_app_dir()
    local = os.path.join(app_dir, "config.json")
    if _is_writable_dir(app_dir):
        return local
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    fallback_dir = os.path.join(base, "StreamPad")
    os.makedirs(fallback_dir, exist_ok=True)
    return os.path.join(fallback_dir, "config.json")


CONFIG_PATH = _resolve_config_path()


def new_profile(name: str) -> dict:
    return {"id": str(uuid.uuid4()), "name": name, "columns": 4, "buttons": []}


def _default_config() -> dict:
    profile = new_profile("Profile 1")
    return {"active_profile": profile["id"], "profiles": [profile],
            "settings": dict(DEFAULT_SETTINGS)}


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
        settings = dict(DEFAULT_SETTINGS)
        settings.update(data.get("settings") or {})
        data["settings"] = settings
        return data
    if "buttons" in data:
        profile = new_profile("Profile 1")
        profile["columns"] = data.get("columns", 4)
        profile["buttons"] = data.get("buttons", [])
        return {"active_profile": profile["id"], "profiles": [profile],
                "settings": dict(DEFAULT_SETTINGS)}
    return _default_config()


def save_config(config: dict) -> bool:
    """Simpan ke config.json. Mengembalikan True kalau berhasil."""
    try:
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        os.replace(tmp, CONFIG_PATH)
        return True
    except Exception as e:
        print(f"Gagal menyimpan config: {e}")
        return False


def export_config(config: dict, path: str):
    """Tulis salinan config ke file pilihan user (misal config.json di Desktop)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def import_config(path: str) -> dict:
    """Baca config.json dari file lain. Melempar Exception kalau formatnya salah."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not ("profiles" in data or "buttons" in data):
        raise ValueError("File ini bukan config StreamPad yang valid.")
    return _migrate(data)


def get_active_profile(config: dict) -> dict:
    for p in config["profiles"]:
        if p["id"] == config.get("active_profile"):
            return p
    return config["profiles"][0]


def new_button(button_id: str) -> dict:
    return {
        "id": button_id,
        "label": "Tombol Baru",
        "color": "#ffffff",
        "action_type": "sound",  # sound | app
        "sound_path": "",
        "sound_volume": 1.0,
        "sound_start_ms": 0,
        "sound_end_ms": None,   # None = putar sampai selesai
        "app_path": "",
        "app_args": "",
        "hotkey": ""
    }
