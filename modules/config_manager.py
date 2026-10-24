import json
import os

class ConfigManager:
    def __init__(self, filepath="config.json"):
        self.filepath = filepath
        self.settings = {
            "duration": 0,
            "profiles": [],
            "volume": 100,
            "last_used_profile": "Profile 1"
        }
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as file:
                self.settings = json.load(file)

    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as file:
            json.dump(self.settings, file, indent=4)

    def export_config(self, export_path):
        with open(export_path, 'w', encoding='utf-8') as file:
            json.dump(self.settings, file, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()