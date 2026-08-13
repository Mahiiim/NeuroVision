"""
core/speech_engine.py
----------------------
Text-to-speech via pyttsx3, running in a background daemon thread so the
GUI is never blocked.

Emits Qt signals via SpeechEngine (QObject) so the UI can react to
speaking-started / speaking-finished events.
"""

from __future__ import annotations

import threading
from typing import Optional

import pyttsx3
from PySide6.QtCore import QObject, Signal

from utils.logger import get_logger

log = get_logger(__name__)


class SpeechEngine(QObject):
    """
    Thread-safe pyttsx3 wrapper.

    Signals
    -------
    speaking_started  — emitted just before TTS begins
    speaking_finished — emitted when TTS finishes (or fails)
    """

    speaking_started = Signal()
    speaking_finished = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()
        self._busy = False
        self._rate: int = 150
        self._volume: float = 1.0
        self._voice_id: Optional[str] = None
        self._voices: list[str] = []
        self._fetch_voices()

    # ── public API ──────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Speak *text* in a background thread. No-op if already speaking."""
        text = text.strip()
        if not text:
            return
        with self._lock:
            if self._busy:
                log.debug("TTS busy — ignoring: %r", text)
                return
            self._busy = True

        self.speaking_started.emit()
        thread = threading.Thread(target=self._speak_worker, args=(text,), daemon=True)
        thread.start()

    def stop(self) -> None:
        """
        Request the current speech to stop.
        Note: pyttsx3 does not support mid-utterance interruption cleanly,
        so this simply marks the engine as not busy and the next utterance
        will be discarded until the current one finishes naturally.
        """
        with self._lock:
            self._busy = False
        log.info("TTS stop requested")

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._busy

    def set_rate(self, rate: int) -> None:
        """Set words-per-minute rate (default 150)."""
        self._rate = rate

    def set_volume(self, volume: float) -> None:
        """Set volume 0.0–1.0 (default 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def set_voice_by_index(self, index: int) -> None:
        """Select a voice by its index in :attr:`voice_names`."""
        voices = self._get_raw_voices()
        if 0 <= index < len(voices):
            self._voice_id = voices[index].id
            log.info("Voice set to: %s", voices[index].name)

    @property
    def voice_names(self) -> list[str]:
        """Human-readable list of available voice names."""
        return list(self._voices)

    # ── private ─────────────────────────────────────────────────

    def _fetch_voices(self) -> None:
        try:
            engine = pyttsx3.init()
            self._voices = [v.name for v in engine.getProperty("voices")]
            engine.stop()
            log.info("TTS voices available: %d", len(self._voices))
        except Exception as exc:
            log.warning("Could not enumerate TTS voices: %s", exc)
            self._voices = ["Default"]

    def _get_raw_voices(self) -> list:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            return voices or []
        except Exception:
            return []

    def _speak_worker(self, text: str) -> None:
        """Run in a background thread. Initialises a fresh pyttsx3 instance each call."""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            if self._voice_id:
                engine.setProperty("voice", self._voice_id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            log.debug("TTS finished: %r", text)
        except Exception as exc:
            log.error("TTS error: %s", exc)
        finally:
            with self._lock:
                self._busy = False
            self.speaking_finished.emit()
