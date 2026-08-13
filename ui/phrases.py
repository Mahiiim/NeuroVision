"""
ui/phrases.py
--------------
Quick Phrases page.

Displays large, accessible buttons for pre-configured phrases.
Head movement positions the cursor; blink triggers the button click
via PyAutoGUI (same mechanism as the keyboard).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
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
from utils.config import Config
from utils.logger import get_logger

log = get_logger(__name__)

BG_CARD = "#1c2128"
BG_PHRASE_BTN = "#1a2d42"
ACCENT = "#00b4ff"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
BORDER = "#30363d"
SUCCESS = "#3fb950"

_PHRASE_STYLE = f"""
QPushButton {{
    background-color: {BG_PHRASE_BTN};
    color: {TEXT_PRIMARY};
    border: 2px solid #264a6e;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
    padding: 18px 12px;
    min-height: 70px;
    text-align: center;
}}
QPushButton:hover {{
    background-color: {ACCENT};
    color: #0d1117;
    border: 2px solid {ACCENT};
    font-weight: 800;
}}
QPushButton:pressed {{
    background-color: #0090cc;
}}
"""


class PhrasesWidget(QWidget):
    """Quick Phrases page."""

    def __init__(self, config: Config, speech: SpeechEngine, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._speech = speech
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(16)

        # Title
        title = QLabel("💬  Quick Phrases")
        title.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:20px; font-weight:700;"
        )
        outer.addWidget(title)

        hint = QLabel(
            "Hover over a phrase button with head movement, then blink to speak it."
        )
        hint.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
        outer.addWidget(hint)

        # Speaking indicator
        self._speak_lbl = QLabel("")
        self._speak_lbl.setStyleSheet(
            f"color:{ACCENT}; font-size:13px; font-weight:700;"
        )
        outer.addWidget(self._speak_lbl)
        self._speech.speaking_started.connect(
            lambda: self._speak_lbl.setText("🔊  Speaking…")
        )
        self._speech.speaking_finished.connect(
            lambda: self._speak_lbl.setText("")
        )

        # Phrase buttons grid (2 columns)
        phrases: list[str] = self._config.get("phrases", [])
        grid = QGridLayout()
        grid.setSpacing(12)

        for i, phrase in enumerate(phrases):
            btn = QPushButton(phrase)
            btn.setStyleSheet(_PHRASE_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.clicked.connect(lambda checked=False, p=phrase: self._speak(p))
            row, col = divmod(i, 2)
            grid.addWidget(btn, row, col)

        outer.addLayout(grid, 1)

        # Last spoken label
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};")
        outer.addWidget(sep)

        row_last = QHBoxLayout()
        row_last.addWidget(QLabel("Last spoken:").setStyleSheet if False else QLabel("Last spoken:"))
        self._last_lbl = QLabel("—")
        self._last_lbl.setStyleSheet(f"color:{ACCENT}; font-weight:600;")
        row_last.addWidget(self._last_lbl)
        row_last.addStretch(1)
        outer.addLayout(row_last)

    def _speak(self, phrase: str) -> None:
        log.info("Quick phrase: %r", phrase)
        self._last_lbl.setText(f'"{phrase}"')
        self._speech.speak(phrase)
