"""
ui/home_automation.py
---------------------
Home Automation Control module
"""

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QSizePolicy
)

from utils.logger import get_logger

log = get_logger(__name__)

ESP_IP = "http://192.168.4.2"
DWELL_TIME = 700 # ms

class ApplianceCard(QPushButton):
    def __init__(self, name, on_endpoint, off_endpoint, parent=None):
        super().__init__(parent)
        self._name = name
        self._on_endpoint = on_endpoint
        self._off_endpoint = off_endpoint
        self._is_on = False
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(180)
        
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(DWELL_TIME)
        self._hover_timer.timeout.connect(self.toggle_state)
        
        self.parent_widget = parent
        self._refresh_style()

    def _refresh_style(self):
        state_text = "ON" if self._is_on else "OFF"
        color = "#2ED573" if self._is_on else "#A0B2C6"
        bg_color = "rgba(46, 213, 115, 0.15)" if self._is_on else "rgba(255, 255, 255, 0.05)"
        
        self.setText(f"{self._name}\n\n{state_text}")
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {color};
                border: 2px solid {color};
                border-radius: 16px;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 210, 255, 0.15);
                border: 2px solid #00D2FF;
                color: #00D2FF;
            }}
        """)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hover_timer.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover_timer.stop()

    def toggle_state(self):
        self._is_on = not self._is_on
        self._refresh_style()
        endpoint = self._on_endpoint if self._is_on else self._off_endpoint
        if self.parent_widget:
            self.parent_widget.send_command(endpoint)


class HomeAutomationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._net_manager = QNetworkAccessManager(self)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("Home Automation")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        self.card_light = ApplianceCard("💡 Room Light", "/home/light_on", "/home/light_off", self)
        self.card_fan = ApplianceCard("🌀 Ceiling Fan", "/home/fan_on", "/home/fan_off", self)
        self.card_bed = ApplianceCard("🛏️ Bed Adjust", "/home/bed_up", "/home/bed_down", self)
        
        grid.addWidget(self.card_light, 0, 0)
        grid.addWidget(self.card_fan, 0, 1)
        grid.addWidget(self.card_bed, 1, 0)
        
        layout.addLayout(grid)
        layout.addStretch(1)

    def send_command(self, endpoint):
        req = QNetworkRequest(QUrl(f"{ESP_IP}{endpoint}"))
        self._net_manager.get(req)
        log.info(f"Home Automation command sent: {endpoint}")
