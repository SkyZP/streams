from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFileDialog
from modules.config_manager import ConfigManager

class ActionButtons(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.btn_jalankan = QPushButton("▶ Jalankan")
        self.btn_jalankan.setMinimumSize(130, 40)
        self.btn_jalankan.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.btn_edit = QPushButton("✏ Edit")
        self.btn_edit.setMinimumSize(130, 40)
        self.btn_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.btn_export = QPushButton("💾 Export Config")
        self.btn_export.setMinimumSize(140, 40)
        self.btn_export.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_export.clicked.connect(self.handle_export)

        self.layout.addWidget(self.btn_jalankan)
        self.layout.addWidget(self.btn_edit)
        self.layout.addWidget(self.btn_export)
        self.layout.addStretch()

    def handle_export(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Konfigurasi",
            "config_backup.json",
            "JSON Files (*.json)"
        )
        if file_path:
            self.config_manager.export_config(file_path)