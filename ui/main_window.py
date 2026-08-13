"""
ui/main_window.py
------------------
Root QMainWindow for NeuroDrishti.

Layout
------
  ┌─────────────────────────────────────────────────────┐
  │  Header: title + subtitle + status pills            │
  ├──────────┬──────────────────────────────────────────┤
  │ Sidebar  │  QStackedWidget (page area)              │
  │  nav     │                                          │
  │  buttons │                                          │
  ├──────────┴──────────────────────────────────────────┤
  │  Emergency Stop bar (always visible)                │
  └─────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from core.face_tracker import FaceTrackerWorker
from core.speech_engine import SpeechEngine
from ui.about import AboutWidget
from ui.dashboard import DashboardWidget
from ui.keyboard import KeyboardWidget
from ui.phrases import PhrasesWidget
from ui.settings import SettingsWidget
from utils.config import Config
from utils.logger import get_logger

log = get_logger(__name__)

# ── Colour palette ────────────────────────────────────────────
BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_SIDEBAR = "#0d1117"
ACCENT = "#00b4ff"
ACCENT_HOVER = "#33c6ff"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
BORDER = "#30363d"
SUCCESS = "#3fb950"
WARNING = "#d29922"
DANGER = "#f85149"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Inter', sans-serif;
}}
QFrame#sidebar {{
    background-color: {BG_SIDEBAR};
    border-right: 1px solid {BORDER};
}}
QPushButton#navBtn {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: none;
    border-left: 3px solid transparent;
    padding: 14px 20px;
    font-size: 13px;
    text-align: left;
    font-weight: 500;
}}
QPushButton#navBtn:hover {{
    background-color: rgba(0, 180, 255, 0.08);
    color: {TEXT_PRIMARY};
}}
QPushButton#navBtn[active="true"] {{
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    background-color: rgba(0, 180, 255, 0.12);
    font-weight: 700;
}}
QPushButton#emergencyBtn {{
    background-color: {DANGER};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 30px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QPushButton#emergencyBtn:hover {{
    background-color: #ff6b6b;
}}
QFrame#header {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}
QLabel#appTitle {{
    font-size: 22px;
    font-weight: 800;
    color: {ACCENT};
    letter-spacing: 2px;
}}
QLabel#appSubtitle {{
    font-size: 11px;
    color: {TEXT_MUTED};
    letter-spacing: 0.5px;
}}
"""


class StatusPill(QLabel):
    """A small coloured pill label for header status indicators."""

    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self._label = label
        self._ok = False
        self._refresh()
        self.setFixedHeight(24)
        self.setContentsMargins(10, 2, 10, 2)

    def set_ok(self, ok: bool, text: str = "") -> None:
        self._ok = ok
        self._text = text
        self._refresh()

    def _refresh(self) -> None:
        text = getattr(self, "_text", "")
        color = SUCCESS if self._ok else DANGER
        display = text if text else ("●" if self._ok else "○")
        self.setText(f"  {self._label}: {display}  ")
        self.setStyleSheet(
            f"background-color: rgba({'63,185,80' if self._ok else '248,81,73'}, 0.15);"
            f"color: {color};"
            f"border: 1px solid {color};"
            f"border-radius: 12px;"
            f"font-size: 11px; font-weight: 600;"
        )


class MainWindow(QMainWindow):
    """Root application window."""

    # Page indices in the QStackedWidget
    PAGE_DASHBOARD = 0
    PAGE_KEYBOARD = 1
    PAGE_PHRASES = 2
    PAGE_SETTINGS = 3
    PAGE_ABOUT = 4

    def __init__(self, config: Config, tracker: FaceTrackerWorker, speech: SpeechEngine) -> None:
        super().__init__()
        self._config = config
        self._tracker = tracker
        self._speech = speech

        self.setWindowTitle("NeuroDrishti — Eye-Controlled Assistive System")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._wire_tracker()

        # ESC = emergency stop
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self._emergency_stop)

        log.info("MainWindow initialised")

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        outer.addWidget(self._build_header())

        # Body (sidebar + pages)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_pages(), 1)
        outer.addLayout(body, 1)

        # Emergency stop bar
        outer.addWidget(self._build_emergency_bar())

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("header")
        frame.setFixedHeight(68)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 0, 24, 0)

        # Title block
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("NEURO DRISTI")
        title.setObjectName("appTitle")
        subtitle = QLabel("Eye-Controlled Assistive Communication System")
        subtitle.setObjectName("appSubtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        layout.addLayout(title_block)
        layout.addStretch(1)

        # Status pills
        self._pill_camera = StatusPill("Camera")
        self._pill_face = StatusPill("Face")
        self._pill_tracking = StatusPill("Tracking")
        self._pill_voice = StatusPill("Voice")

        for pill in (self._pill_camera, self._pill_face, self._pill_tracking, self._pill_voice):
            layout.addWidget(pill)
            layout.addSpacing(6)

        return frame

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(190)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)

        nav_items = [
            ("🏠  Dashboard", self.PAGE_DASHBOARD),
            ("⌨️  Eye Keyboard", self.PAGE_KEYBOARD),
            ("💬  Quick Phrases", self.PAGE_PHRASES),
            ("⚙️  Settings", self.PAGE_SETTINGS),
            ("ℹ️  About", self.PAGE_ABOUT),
        ]
        self._nav_buttons: dict[int, QPushButton] = {}
        for label, page_idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCheckable(False)
            btn.setProperty("active", "false")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, p=page_idx: self._navigate(p))
            layout.addWidget(btn)
            self._nav_buttons[page_idx] = btn

        layout.addStretch(1)
        return frame

    def _build_pages(self) -> QStackedWidget:
        self._pages = QStackedWidget()

        self._dashboard = DashboardWidget(self._config, self._tracker, self._speech)
        self._keyboard = KeyboardWidget(self._speech)
        self._phrases = PhrasesWidget(self._config, self._speech)
        self._settings = SettingsWidget(self._config, self._tracker, self._speech)
        self._about = AboutWidget()

        self._pages.addWidget(self._dashboard)   # 0
        self._pages.addWidget(self._keyboard)    # 1
        self._pages.addWidget(self._phrases)     # 2
        self._pages.addWidget(self._settings)    # 3
        self._pages.addWidget(self._about)       # 4

        self._navigate(self.PAGE_DASHBOARD)
        return self._pages

    def _build_emergency_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background-color: {BG_PANEL}; border-top: 1px solid {BORDER};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 6, 24, 6)

        hint = QLabel("ESC — Emergency Stop  |  Stops all mouse control immediately")
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(hint, 1)

        self._btn_emergency = QPushButton("🛑  EMERGENCY STOP")
        self._btn_emergency.setObjectName("emergencyBtn")
        self._btn_emergency.setFixedHeight(36)
        self._btn_emergency.clicked.connect(self._emergency_stop)
        layout.addWidget(self._btn_emergency)

        return bar

    # ── signal wiring ────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Speech status → Voice pill
        self._speech.speaking_started.connect(
            lambda: self._pill_voice.set_ok(True, "Speaking…")
        )
        self._speech.speaking_finished.connect(
            lambda: self._pill_voice.set_ok(True, "Ready")
        )

    def _wire_tracker(self) -> None:
        """Connect tracker signals to header status pills and pages."""
        self._tracker.face_detected.connect(
            lambda ok: self._pill_face.set_ok(ok, "Detected" if ok else "Not Detected")
        )
        self._tracker.tracking_error.connect(self._on_tracking_error)

        # Camera pill — set to connected once thread starts
        self._pill_camera.set_ok(True, "Connected")
        self._pill_tracking.set_ok(False, "OFF")

        # Dashboard signals
        self._dashboard.tracking_started.connect(
            lambda: self._pill_tracking.set_ok(True, "ON")
        )
        self._dashboard.tracking_stopped.connect(
            lambda: self._pill_tracking.set_ok(False, "OFF")
        )

    # ── navigation ───────────────────────────────────────────────

    def _navigate(self, page_idx: int) -> None:
        self._pages.setCurrentIndex(page_idx)
        for idx, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if idx == page_idx else "false")
            # Force style refresh
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        log.debug("Navigated to page %d", page_idx)

    # ── emergency stop ────────────────────────────────────────────

    def _emergency_stop(self) -> None:
        self._tracker.emergency_stop()
        self._dashboard.on_external_stop()
        self._pill_tracking.set_ok(False, "STOPPED")
        log.warning("Emergency stop triggered from MainWindow")

    def _on_tracking_error(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        self._pill_camera.set_ok(False, "Error")
        QMessageBox.critical(self, "Tracking Error", message)

    # ── cleanup ──────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        log.info("Application closing")
        self._tracker.stop_tracking()
        self._tracker.stop_thread()
        self._tracker.wait(3000)
        self._config.save()
        event.accept()
