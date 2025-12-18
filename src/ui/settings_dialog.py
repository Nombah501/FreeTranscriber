from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QCheckBox, QSpinBox, QTabWidget, QWidget, QPushButton, QSlider
)
from PyQt6.QtCore import Qt
import sounddevice as sd

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("FreeTranscriber Settings")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #333;
                color: #aaa;
                padding: 8px 12px;
                border: 1px solid #444;
            }
            QTabBar::tab:selected {
                background: #444;
                color: #fff;
            }
            QComboBox, QSpinBox {
                background: #333;
                color: #fff;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_general_tab(), "General")
        self.tabs.addTab(self.create_audio_tab(), "Audio")
        self.tabs.addTab(self.create_ai_tab(), "AI Model")
        
        layout.addWidget(self.tabs)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: #555; color: white; padding: 6px 12px; border: none;")
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Opacity Slider
        layout.addWidget(QLabel("Idle Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.config.get("idle_opacity") * 100))
        self.opacity_slider.valueChanged.connect(
            lambda v: self.config.set("idle_opacity", v / 100.0)
        )
        layout.addWidget(self.opacity_slider)

        # Checkboxes
        self.top_check = QCheckBox("Always on Top")
        self.top_check.setChecked(self.config.get("always_on_top"))
        self.top_check.toggled.connect(lambda v: self.config.set("always_on_top", v))
        self.top_check.setStyleSheet("color: white;")
        layout.addWidget(self.top_check)

        self.sounds_check = QCheckBox("Play Sounds")
        self.sounds_check.setChecked(self.config.get("use_sounds"))
        self.sounds_check.toggled.connect(lambda v: self.config.set("use_sounds", v))
        self.sounds_check.setStyleSheet("color: white;")
        layout.addWidget(self.sounds_check)

        # Reset Position Button
        layout.addWidget(QLabel("Widget Position:"))
        reset_position_btn = QPushButton("Reset Position to Default")
        reset_position_btn.setStyleSheet(
            "background: #555; color: white; padding: 8px; border: none; border-radius: 4px;"
        )
        reset_position_btn.clicked.connect(self.on_reset_position)
        layout.addWidget(reset_position_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_reset_position(self):
        """Reset floating widget position to center of primary screen"""
        if self.parent():
            self.parent().reset_position_to_default()

    def create_audio_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Input Device:"))
        self.device_combo = QComboBox()
        
        # Populate devices
        devices = sd.query_devices()
        current_device_id = self.config.get("input_device_id")
        
        default_index = 0
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = f"{dev['name']} ({dev['hostapi']})"
                self.device_combo.addItem(name, i) # Store index as data
                if i == current_device_id:
                    default_index = self.device_combo.count() - 1
        
        self.device_combo.setCurrentIndex(default_index)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        layout.addWidget(self.device_combo)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_device_changed(self, index):
        device_id = self.device_combo.currentData()
        self.config.set("input_device_id", device_id)

    def create_ai_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Model Size:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText(self.config.get("model_size"))
        self.model_combo.currentTextChanged.connect(
            lambda v: self.config.set("model_size", v)
        )
        layout.addWidget(self.model_combo)
        
        layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ru", "en", "auto"])
        self.lang_combo.setCurrentText(self.config.get("language"))
        self.lang_combo.currentTextChanged.connect(
            lambda v: self.config.set("language", v)
        )
        layout.addWidget(self.lang_combo)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
