"""
ui/keyboard.py
---------------
Eye-controlled virtual keyboard page.

The keyboard is rendered as real QPushButtons in a grid.
Because the FaceTrackerWorker issues real PyAutoGUI clicks,
hovering the system cursor over any button and blinking will
trigger Qt's native button click — no special hit-testing needed.

Rows:
  1 2 3 4 5 6 7 8 9 0
  Q W E R T Y U I O P
  A S D F G H J K L BS
  Z X C V B N M . , CLR
  SPACE      ENTER   EXIT
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.speech_engine import SpeechEngine
from utils.logger import get_logger

log = get_logger(__name__)

# Palette
BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD = "#1c2128"
BG_KEY = "#21262d"
BG_KEY_SPECIAL = "#1f3045"
BG_KEY_DANGER = "#3d1f1f"
BG_KEY_SUCCESS = "#1f3d1f"
BG_KEY_ACCENT = "#1a3050"
ACCENT = "#00b4ff"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
BORDER = "#30363d"
SUCCESS = "#3fb950"
DANGER = "#f85149"

_KEY_STYLE = f"""
QPushButton {{
    background-color: {BG_KEY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    font-size: 16px;
    font-weight: 700;
    min-height: 56px;
    min-width: 54px;
}}
QPushButton:hover {{
    background-color: {ACCENT};
    color: #0d1117;
    border: 2px solid {ACCENT};
}}
QPushButton:pressed {{
    background-color: #0090cc;
}}
"""

_SPECIAL_STYLE = f"""
QPushButton {{
    background-color: {BG_KEY_SPECIAL};
    color: {ACCENT};
    border: 1px solid {ACCENT};
    border-radius: 8px;
    font-size: 14px;
    font-weight: 700;
    min-height: 56px;
}}
QPushButton:hover {{
    background-color: {ACCENT};
    color: #0d1117;
}}
"""

_DANGER_STYLE = f"""
QPushButton {{
    background-color: {BG_KEY_DANGER};
    color: {DANGER};
    border: 1px solid {DANGER};
    border-radius: 8px;
    font-size: 14px;
    font-weight: 700;
    min-height: 56px;
}}
QPushButton:hover {{
    background-color: {DANGER};
    color: white;
}}
"""

_SUCCESS_STYLE = f"""
QPushButton {{
    background-color: {BG_KEY_SUCCESS};
    color: {SUCCESS};
    border: 1px solid {SUCCESS};
    border-radius: 8px;
    font-size: 14px;
    font-weight: 700;
    min-height: 56px;
}}
QPushButton:hover {{
    background-color: {SUCCESS};
    color: white;
}}
"""


class KeyboardWidget(QWidget):
    """Eye-controlled virtual keyboard page."""

    KB_ROWS = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", "BS"],
        ["Z", "X", "C", "V", "B", "N", "M", ".", ",", "CLR"],
    ]
    BOTTOM_ROW = ["SPACE", "ENTER", "EXIT"]

    def __init__(self, speech: SpeechEngine, parent=None) -> None:
        super().__init__(parent)
        self._speech = speech
        self._text = ""
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        # Page title
        title = QLabel("⌨️  Eye-Controlled Keyboard")
        title.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:20px; font-weight:700;"
        )
        outer.addWidget(title)

        hint = QLabel("Hover cursor with head movement · Blink to select a key")
        hint.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        outer.addWidget(hint)

        # Text display area
        text_frame = QFrame()
        text_frame.setStyleSheet(
            f"background:{BG_CARD}; border:2px solid {ACCENT}; border-radius:10px;"
        )
        text_frame.setFixedHeight(70)
        text_layout = QHBoxLayout(text_frame)
        text_layout.setContentsMargins(16, 0, 16, 0)

        self._display = QLabel("| Start typing…")
        self._display.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:22px; font-weight:500; "
            f"border:none; background:transparent;"
        )
        self._display.setWordWrap(False)
        self._display.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(self._display)
        outer.addWidget(text_frame)

        # Speaking status
        self._speak_lbl = QLabel("")
        self._speak_lbl.setStyleSheet(f"color:{ACCENT}; font-size:12px; font-weight:600;")
        outer.addWidget(self._speak_lbl)
        self._speech.speaking_started.connect(lambda: self._speak_lbl.setText("🔊 Speaking…"))
        self._speech.speaking_finished.connect(lambda: self._speak_lbl.setText(""))

        # Keyboard grid
        grid = QGridLayout()
        grid.setSpacing(6)

        for row_idx, row in enumerate(self.KB_ROWS):
            for col_idx, key in enumerate(row):
                btn = self._make_key_btn(key)
                grid.addWidget(btn, row_idx, col_idx)

        # Bottom row
        btn_space = QPushButton("SPACE")
        btn_space.setStyleSheet(_SPECIAL_STYLE)
        btn_space.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_space.clicked.connect(lambda: self._key_press("SPACE"))

        btn_enter = QPushButton("ENTER  🔊")
        btn_enter.setStyleSheet(_SUCCESS_STYLE)
        btn_enter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_enter.clicked.connect(lambda: self._key_press("ENTER"))

        btn_exit = QPushButton("EXIT  ✕")
        btn_exit.setStyleSheet(_DANGER_STYLE)
        btn_exit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_exit.clicked.connect(lambda: self._key_press("EXIT"))

        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.setSpacing(6)
        bottom_row_layout.addWidget(btn_space, 5)
        bottom_row_layout.addWidget(btn_enter, 3)
        bottom_row_layout.addWidget(btn_exit, 2)

        outer.addLayout(grid)
        outer.addLayout(bottom_row_layout)
        outer.addStretch(1)

    def _make_key_btn(self, key: str) -> QPushButton:
        """Create one keyboard button."""
        btn = QPushButton(key)
        if key in ("BS", "CLR"):
            btn.setStyleSheet(_DANGER_STYLE)
        else:
            btn.setStyleSheet(_KEY_STYLE)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda checked=False, k=key: self._key_press(k))
        return btn

    # ── key handling ─────────────────────────────────────────────

    def _key_press(self, key: str) -> None:
        if key == "BS":
            self._text = self._text[:-1]
        elif key == "CLR":
            self._text = ""
        elif key == "SPACE":
            self._text += " "
        elif key == "ENTER":
            if self._text.strip():
                self._speech.speak(self._text)
                log.info("Keyboard TTS: %r", self._text)
        elif key == "EXIT":
            # Navigate back to dashboard — find parent MainWindow
            self._go_to_dashboard()
        else:
            self._text += key

        self._update_display()

    def _update_display(self) -> None:
        display_text = self._text if self._text else ""
        # Truncate from left if too long for display
        if len(display_text) > 40:
            display_text = "…" + display_text[-38:]
        self._display.setText(display_text + "|")

    def _go_to_dashboard(self) -> None:
        """Navigate to dashboard (page 0) via the parent MainWindow."""
        # Walk up the widget hierarchy to find MainWindow
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_navigate"):
                parent._navigate(0)
                return
            parent = parent.parent()
