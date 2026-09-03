"""
ui/home_automation.py
---------------------
Home Automation Control module
"""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QSizePolicy
)

from core.speech_engine import SpeechEngine
from utils.logger import get_logger

log = get_logger(__name__)

ESP_IP = "http://192.168.4.2"

class BlinkCommandButton(QPushButton):
    def __init__(self, name, endpoint, speech: SpeechEngine, spoken_text="", color="#00D2FF", bg_color="rgba(0, 210, 255, 0.15)", parent=None):
        super().__init__(parent)
        self._name = name
        self._endpoint = endpoint
        self._speech = speech
        self._spoken_text = spoken_text
        self._color = color
        self._bg_color = bg_color
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(120)
        
        self.parent_widget = parent
        self._refresh_style()
        self.clicked.connect(self.trigger_command)

    def _refresh_style(self):
        self.setText(self._name)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg_color};
                color: {self._color};
                border: 2px solid {self._color};
                border-radius: 16px;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid #FFFFFF;
                color: #FFFFFF;
            }}
        """)

    def trigger_command(self):
        if self._spoken_text and self._speech:
            self._speech.speak(self._spoken_text)
        if self.parent_widget:
            self.parent_widget.send_command(self._endpoint)


class HomeAutomationWidget(QWidget):
    def __init__(self, speech: SpeechEngine, parent=None):
        super().__init__(parent)
        self._speech = speech
        self._net_manager = QNetworkAccessManager(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("Home Automation")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        instructions = QLabel("How to use: Move your cursor by pointing your nose. Look at a button below and deliberately BLINK to activate it.")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #A0B2C6; font-size: 20px; margin-bottom: 20px;")
        layout.addWidget(instructions)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        self.btn_light_on = BlinkCommandButton("💡 Light ON", "/home/light_on", self._speech, "Light on", color="#2ED573", bg_color="rgba(46, 213, 115, 0.15)", parent=self)
        self.btn_light_off = BlinkCommandButton("💡 Light OFF", "/home/light_off", self._speech, "Light off", color="#FF4757", bg_color="rgba(255, 71, 87, 0.15)", parent=self)
        
        self.btn_fan_on = BlinkCommandButton("🌀 Fan ON", "/home/fan_on", self._speech, "Fan on", color="#2ED573", bg_color="rgba(46, 213, 115, 0.15)", parent=self)
        self.btn_fan_off = BlinkCommandButton("🌀 Fan OFF", "/home/fan_off", self._speech, "Fan off", color="#FF4757", bg_color="rgba(255, 71, 87, 0.15)", parent=self)
        
        grid.addWidget(self.btn_light_on, 0, 0)
        grid.addWidget(self.btn_light_off, 0, 1)
        grid.addWidget(self.btn_fan_on, 1, 0)
        grid.addWidget(self.btn_fan_off, 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch(1)

    def send_command(self, endpoint):
        req = QNetworkRequest(QUrl(f"{ESP_IP}{endpoint}"))
        self._net_manager.get(req)
        log.info(f"Home Automation command sent: {endpoint}")
