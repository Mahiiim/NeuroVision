"""
utils/config.py
---------------
JSON-backed configuration system.

All user-adjustable settings live here. On first launch the defaults are
written to ~/.neurovision/config.json; subsequent launches load from that
file, so settings persist across sessions.

Usage:
    from utils.config import Config
    cfg = Config()
    cfg.get("blink_threshold")   # -> 0.20
    cfg.set("blink_threshold", 0.18)
    cfg.save()
"""

import json
import os
from typing import Any

from utils.logger import get_logger

log = get_logger(__name__)

# Where the config file lives
_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".neurovision")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")

# ──────────────────────────────────────────────────────────────
#  Default values — every key that the application may read/write
# ──────────────────────────────────────────────────────────────
DEFAULTS: dict[str, Any] = {
    # Eye-tracking
    "blink_threshold": 0.20,
    "click_cooldown": 1.0,
    "smoothing_alpha_min": 0.05,
    "smoothing_alpha_max": 0.25,
    "sensitivity_x": 1.0,
    "sensitivity_y": 1.0,
    # Camera
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    # Cursor range (normalised nose coords that map to full screen edges)
    "range_x_min": 0.38,
    "range_x_max": 0.62,
    "range_y_min": 0.38,
    "range_y_max": 0.62,
    # Speech
    "speech_rate": 150,
    "speech_volume": 1.0,
    "speech_voice_index": 0,
    # Interface
    "dark_mode": True,
    "show_landmarks": False,
    "show_tracking_info": True,
    # Quick phrases
    "phrases": [
        "I need help",
        "Yes",
        "No",
        "Thank you",
        "Water please",
        "Food please",
        "Toilet",
    ],
}


class Config:
    """
    Singleton-style configuration manager.

    Loads from disk on construction and writes back on :meth:`save`.
    """

    def __init__(self) -> None:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load()

    # ── public API ──────────────────────────────────────────────

    def get(self, key: str, fallback: Any = None) -> Any:
        """Return the value for *key*, or *fallback* if not found."""
        return self._data.get(key, fallback)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* in memory (does not auto-save)."""
        self._data[key] = value

    def save(self) -> None:
        """Persist current settings to disk."""
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            log.debug("Config saved to %s", _CONFIG_FILE)
        except OSError as exc:
            log.error("Failed to save config: %s", exc)

    def reset_to_defaults(self) -> None:
        """Overwrite in-memory data with factory defaults and save."""
        self._data = dict(DEFAULTS)
        self.save()
        log.info("Config reset to defaults")

    def all(self) -> dict[str, Any]:
        """Return a shallow copy of the current config dict."""
        return dict(self._data)

    # ── private ─────────────────────────────────────────────────

    def _load(self) -> None:
        if not os.path.exists(_CONFIG_FILE):
            log.info("No config file found — using defaults")
            self.save()
            return
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as fh:
                stored: dict[str, Any] = json.load(fh)
            # Merge: stored values override defaults, missing keys get defaults
            self._data.update(stored)
            log.debug("Config loaded from %s", _CONFIG_FILE)
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Could not load config (%s) — using defaults", exc)
