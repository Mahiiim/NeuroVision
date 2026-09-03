"""
ui/wheelchair.py
----------------
Wheelchair Drive Control module
"""

from PySide6.QtCore import Qt, QTimer, QUrl, Signal, Property
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy
)
import json

from utils.logger import get_logger

log = get_logger(__name__)

# Constants
ESP_IP = "http://192.168.4.1"
POLL_INTERVAL = 130 # ms

class DriveButton(QPushButton):
    def __init__(self, text, command, parent=None):
        super().__init__(text, parent)
        self._command = command
        self._is_stop = (command == "/S")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(120)
        
        self.parent_widget = parent
        
        if self._is_stop:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #E63946;
                    color: white;
                    border-radius: 20px;
                    font-size: 28px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #00D2FF;
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    font-size: 24px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(0, 210, 255, 0.15);
                    border: 2px solid #00D2FF;
                }
            """)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.parent_widget:
            if self._is_stop:
                self.parent_widget.trigger_stop()
            else:
                self.parent_widget.start_drive(self._command)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.parent_widget and not self._is_stop:
            self.parent_widget.trigger_stop()


class WheelchairWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._net_manager = QNetworkAccessManager(self)
        self._current_command = None
        self._drive_timer = QTimer(self)
        self._drive_timer.setInterval(POLL_INTERVAL)
        self._drive_timer.timeout.connect(self._send_drive_pulse)
        
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.setInterval(1000)
        self._telemetry_timer.timeout.connect(self._fetch_telemetry)
        
        self._build_ui()
        self._telemetry_timer.start()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Telemetry Card
        tel_card = QFrame()
        tel_card.setStyleSheet("background: #1c2128; border-radius: 12px;")
        tel_layout = QHBoxLayout(tel_card)
        
        self._front_lbl = QLabel("Front: -- cm")
        self._front_lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self._front_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._rear_lbl = QLabel("Rear: -- cm")
        self._rear_lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self._rear_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tel_layout.addWidget(self._front_lbl)
        tel_layout.addWidget(self._rear_lbl)
        layout.addWidget(tel_card)
        
        # Drive Controls Grid
        grid = QGridLayout()
        grid.setSpacing(16)
        
        self.btn_f = DriveButton("⬆ FORWARD", "/F", self)
        self.btn_l = DriveButton("⬅ LEFT", "/L", self)
        self.btn_s = DriveButton("🛑 STOP", "/S", self)
        self.btn_r = DriveButton("➡ RIGHT", "/R", self)
        self.btn_b = DriveButton("⬇ BACKWARD", "/B", self)
        
        grid.addWidget(self.btn_f, 0, 1)
        grid.addWidget(self.btn_l, 1, 0)
        grid.addWidget(self.btn_s, 1, 1)
        grid.addWidget(self.btn_r, 1, 2)
        grid.addWidget(self.btn_b, 2, 1)
        
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)
        
        layout.addLayout(grid, 1)

    def start_drive(self, command):
        self._current_command = command
        self._drive_timer.start()
        self._send_drive_pulse()

    def trigger_stop(self):
        self._drive_timer.stop()
        self._current_command = None
        self._send_request("/S")
        log.info("Wheelchair STOP sent")

    def _send_drive_pulse(self):
        if self._current_command:
            self._send_request(self._current_command)

    def _send_request(self, endpoint):
        req = QNetworkRequest(QUrl(f"{ESP_IP}{endpoint}"))
        self._net_manager.get(req)
        
    def _fetch_telemetry(self):
        req = QNetworkRequest(QUrl(f"{ESP_IP}/status"))
        reply = self._net_manager.get(req)
        reply.finished.connect(lambda r=reply: self._on_telemetry(r))

    def _on_telemetry(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            try:
                data = json.loads(reply.readAll().data().decode())
                front = data.get("front", -1)
                rear = data.get("rear", -1)
                
                self._update_sensor_lbl(self._front_lbl, "Front", front)
                self._update_sensor_lbl(self._rear_lbl, "Rear", rear)
            except Exception as e:
                pass
        reply.deleteLater()
        
    def _update_sensor_lbl(self, lbl, prefix, val):
        if val < 0:
            lbl.setText(f"{prefix}: -- cm")
            lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
            return
            
        lbl.setText(f"{prefix}: {val} cm")
        if val < 35:
            lbl.setStyleSheet("color: #FF4757; font-size: 20px; font-weight: bold;")
        elif val <= 80:
            lbl.setStyleSheet("color: #FFA502; font-size: 20px; font-weight: bold;")
        else:
            lbl.setStyleSheet("color: #2ED573; font-size: 20px; font-weight: bold;")

