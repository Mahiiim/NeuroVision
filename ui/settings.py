"""
ui/settings.py
---------------
Settings page — all user-configurable parameters grouped by category.

Changes are applied immediately (hot-reloaded into the tracker) and
persisted to JSON when the user clicks Apply.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QGroupBox,
)

from core.face_tracker import FaceTrackerWorker
from core.camera import CameraManager
from core.speech_engine import SpeechEngine
from utils.config import Config
from utils.logger import get_logger

log = get_logger(__name__)

BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD = "#1c2128"
ACCENT = "#00b4ff"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED = "#8b949e"
BORDER = "#30363d"
SUCCESS = "#3fb950"
DANGER = "#f85149"

_GROUP_STYLE = f"""
QGroupBox {{
    color: {ACCENT};
    font-size: 13px;
    font-weight: 700;
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px;
    background: {BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 12px;
}}
QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 28px;
    font-size: 12px;
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 3px;
}}
QCheckBox {{
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
"""

_BTN_APPLY = f"""
QPushButton {{
    background: {ACCENT};
    color: #0d1117;
    border: none;
    border-radius: 8px;
    padding: 10px 32px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton:hover {{ background: #33c6ff; }}
"""

_BTN_RESET = f"""
QPushButton {{
    background: {BG_PANEL};
    color: {DANGER};
    border: 1px solid {DANGER};
    border-radius: 8px;
    padding: 10px 32px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{ background: {DANGER}; color: white; }}
"""


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:12px;")
    return lbl


class SettingsWidget(QWidget):
    """Full settings page with grouped controls."""

    def __init__(
        self,
        config: Config,
        tracker: FaceTrackerWorker,
        speech: SpeechEngine,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._tracker = tracker
        self._speech = speech
        self._controls: dict[str, Any] = {}
        self._build_ui()

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{BG_DARK}; }}")

        inner = QWidget()
        inner.setStyleSheet(_GROUP_STYLE)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️  Settings")
        title.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:20px; font-weight:700; background:transparent;"
        )
        layout.addWidget(title)

        layout.addWidget(self._build_eye_group())
        layout.addWidget(self._build_camera_group())
        layout.addWidget(self._build_speech_group())
        layout.addWidget(self._build_interface_group())
        layout.addStretch(1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_apply = QPushButton("✓  Apply")
        btn_apply.setStyleSheet(_BTN_APPLY)
        btn_apply.clicked.connect(self._apply)

        btn_reset = QPushButton("↺  Reset to Defaults")
        btn_reset.setStyleSheet(_BTN_RESET)
        btn_reset.clicked.connect(self._reset)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color:{SUCCESS}; font-size:12px;")

        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_reset)
        btn_row.addWidget(self._status_lbl)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    # ── groups ───────────────────────────────────────────────────

    def _build_eye_group(self) -> QGroupBox:
        grp = QGroupBox("👁️  Eye Tracking")
        g = QGridLayout(grp)
        g.setSpacing(10)
        g.setColumnMinimumWidth(0, 180)

        self._add_dspin(g, 0, "Blink Threshold", "blink_threshold", 0.05, 0.50, 3, 0.01)
        self._add_dspin(g, 1, "Click Cooldown (s)", "click_cooldown", 0.2, 5.0, 2, 0.1)
        self._add_dspin(g, 2, "Smoothing Min Alpha", "smoothing_alpha_min", 0.01, 0.50, 2, 0.01)
        self._add_dspin(g, 3, "Smoothing Max Alpha", "smoothing_alpha_max", 0.05, 1.0, 2, 0.05)
        self._add_dspin(g, 4, "Sensitivity X", "sensitivity_x", 0.5, 5.0, 2, 0.1)
        self._add_dspin(g, 5, "Sensitivity Y", "sensitivity_y", 0.5, 5.0, 2, 0.1)
        return grp

    def _build_camera_group(self) -> QGroupBox:
        grp = QGroupBox("📷  Camera")
        g = QGridLayout(grp)
        g.setSpacing(10)
        g.setColumnMinimumWidth(0, 180)

        # Camera index dropdown
        g.addWidget(_label("Camera"), 0, 0)
        cam_combo = QComboBox()
        available = CameraManager.list_cameras()
        for idx in available:
            cam_combo.addItem(f"Camera {idx}", idx)
        current = self._config.get("camera_index", 0)
        cam_combo.setCurrentIndex(max(0, available.index(current)) if current in available else 0)
        g.addWidget(cam_combo, 0, 1)
        self._controls["camera_index"] = cam_combo

        self._add_spin(g, 1, "Width (px)", "camera_width", 320, 1920, 1)
        self._add_spin(g, 2, "Height (px)", "camera_height", 240, 1080, 1)
        return grp

    def _build_speech_group(self) -> QGroupBox:
        grp = QGroupBox("🔊  Speech")
        g = QGridLayout(grp)
        g.setSpacing(10)
        g.setColumnMinimumWidth(0, 180)

        g.addWidget(_label("Voice"), 0, 0)
        voice_combo = QComboBox()
        for name in self._speech.voice_names:
            voice_combo.addItem(name)
        voice_idx = self._config.get("speech_voice_index", 0)
        voice_combo.setCurrentIndex(min(voice_idx, voice_combo.count() - 1))
        g.addWidget(voice_combo, 0, 1)
        self._controls["speech_voice_index"] = voice_combo

        self._add_spin(g, 1, "Speed (WPM)", "speech_rate", 80, 300, 10)
        self._add_dspin(g, 2, "Volume", "speech_volume", 0.0, 1.0, 2, 0.05)
        return grp

    def _build_interface_group(self) -> QGroupBox:
        grp = QGroupBox("🖥️  Interface")
        g = QGridLayout(grp)
        g.setSpacing(10)
        g.setColumnMinimumWidth(0, 180)

        g.addWidget(_label("Show Landmarks"), 0, 0)
        chk_lm = QCheckBox()
        chk_lm.setChecked(self._config.get("show_landmarks", True))
        g.addWidget(chk_lm, 0, 1)
        self._controls["show_landmarks"] = chk_lm

        g.addWidget(_label("Show Tracking Info"), 1, 0)
        chk_ti = QCheckBox()
        chk_ti.setChecked(self._config.get("show_tracking_info", True))
        g.addWidget(chk_ti, 1, 1)
        self._controls["show_tracking_info"] = chk_ti

        return grp

    # ── helper builders ──────────────────────────────────────────

    def _add_dspin(
        self,
        grid: QGridLayout,
        row: int,
        label: str,
        key: str,
        min_val: float,
        max_val: float,
        decimals: int,
        step: float,
    ) -> None:
        grid.addWidget(_label(label), row, 0)
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setValue(self._config.get(key, 0.0))
        grid.addWidget(spin, row, 1)
        self._controls[key] = spin

    def _add_spin(
        self,
        grid: QGridLayout,
        row: int,
        label: str,
        key: str,
        min_val: int,
        max_val: int,
        step: int,
    ) -> None:
        grid.addWidget(_label(label), row, 0)
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setValue(int(self._config.get(key, 0)))
        grid.addWidget(spin, row, 1)
        self._controls[key] = spin

    # ── apply / reset ────────────────────────────────────────────

    def _apply(self) -> None:
        """Read all controls and push values into config + tracker."""
        for key, widget in self._controls.items():
            if isinstance(widget, (QDoubleSpinBox,)):
                self._config.set(key, widget.value())
            elif isinstance(widget, QSpinBox):
                self._config.set(key, widget.value())
            elif isinstance(widget, QComboBox):
                if key == "camera_index":
                    self._config.set(key, widget.currentData())
                elif key == "speech_voice_index":
                    self._config.set(key, widget.currentIndex())
                    self._speech.set_voice_by_index(widget.currentIndex())
                else:
                    self._config.set(key, widget.currentText())
            elif isinstance(widget, QCheckBox):
                self._config.set(key, widget.isChecked())

        # Apply speech settings immediately
        self._speech.set_rate(self._config.get("speech_rate", 150))
        self._speech.set_volume(self._config.get("speech_volume", 1.0))

        # Hot-reload tracker config
        self._tracker.update_config(self._config)
        self._tracker.set_show_landmarks(self._config.get("show_landmarks", True))

        self._config.save()
        self._status_lbl.setText("✓ Settings saved")
        log.info("Settings applied and saved")

    def _reset(self) -> None:
        self._config.reset_to_defaults()
        # Reload controls with new values
        for key, widget in self._controls.items():
            val = self._config.get(key)
            if val is None:
                continue
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(val))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(val))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))
        self._status_lbl.setText("↺ Defaults restored")
        log.info("Settings reset to defaults")
