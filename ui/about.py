"""
ui/about.py
------------
About page — static information about the application.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame

ACCENT = "#00b4ff"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
BG_CARD = "#1c2128"
BORDER = "#30363d"

_ABOUT_HTML = """
<div style='font-family: Segoe UI, Inter, sans-serif; color: #e6edf3;'>

<h1 style='color: #00b4ff; letter-spacing: 3px; font-size: 28px;'>NEUROVISION</h1>
<p style='color: #8b949e; font-size: 13px; margin-top: -8px;'>
    Eye-Controlled Assistive Communication System
</p>

<hr style='border: 1px solid #30363d; margin: 16px 0;'/>

<p style='font-size: 13px; line-height: 1.7;'>
NeuroVision enables individuals with limited motor control to communicate and interact
with a computer using only their eyes.
</p>

<h3 style='color: #00b4ff;'>How It Works</h3>
<ul style='font-size: 13px; line-height: 1.9; color: #8b949e;'>
  <li><b style='color:#e6edf3;'>Head movement</b> → Mouse cursor movement</li>
  <li><b style='color:#e6edf3;'>Blink</b> → Mouse click (Eye Aspect Ratio detection)</li>
  <li><b style='color:#e6edf3;'>Quick Phrases</b> → Instant text-to-speech</li>
  <li><b style='color:#e6edf3;'>Virtual Keyboard</b> → Free-form typing &amp; speech</li>
</ul>

<h3 style='color: #00b4ff;'>Technology Stack</h3>
<ul style='font-size: 13px; line-height: 1.9; color: #8b949e;'>
  <li>PySide6 — Desktop GUI</li>
  <li>MediaPipe Face Landmarker — Real-time facial landmarks</li>
  <li>OpenCV — Camera capture &amp; image processing</li>
  <li>PyAutoGUI — System mouse control</li>
  <li>pyttsx3 — Offline text-to-speech</li>
</ul>

<h3 style='color: #00b4ff;'>Keyboard Shortcuts</h3>
<ul style='font-size: 13px; line-height: 1.9; color: #8b949e;'>
  <li><b style='color:#e6edf3;'>ESC</b> — Emergency stop (halts all tracking)</li>
</ul>

<h3 style='color: #00b4ff;'>Logs</h3>
<p style='font-size: 12px; color: #8b949e;'>
    Application logs are written to: <code style='color:#00b4ff;'>~/.neurovision/app.log</code>
</p>

<hr style='border: 1px solid #30363d; margin: 16px 0;'/>

<p style='font-size: 11px; color: #8b949e;'>
    Version 2.0 &nbsp;·&nbsp; Built with ❤️ for accessibility
</p>

</div>
"""


class AboutWidget(QWidget):
    """Simple about/info page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)

        card = QFrame()
        card.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:14px; padding:24px;"
        )
        card_layout = QVBoxLayout(card)

        lbl = QLabel()
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setText(_ABOUT_HTML)
        lbl.setWordWrap(True)
        lbl.setOpenExternalLinks(False)
        card_layout.addWidget(lbl)
        card_layout.addStretch(1)

        layout.addWidget(card)
        layout.addStretch(1)
