"""
main.py
--------
NeuroDrishti — Eye-Controlled Assistive Communication System
Entry point and startup sequence.

Startup order:
  1. Load configuration
  2. Check / download MediaPipe model
  3. Initialise SpeechEngine (TTS)
  4. Construct FaceTrackerWorker (QThread)
  5. Show MainWindow
  6. Start the tracker thread (camera opens inside the thread)
  7. Enter Qt event loop
"""

import sys
import os

from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont

from utils.logger import get_logger
from utils.config import Config
from core.camera import is_model_available, download_model
from core.face_tracker import FaceTrackerWorker
from core.speech_engine import SpeechEngine
from ui.main_window import MainWindow

log = get_logger("main")


def _ensure_model(app: QApplication) -> bool:
    """
    Check for the MediaPipe model. If absent, show a progress dialog and
    download it. Returns True on success, False on failure.
    """
    if is_model_available():
        log.info("Model found — skipping download")
        return True

    log.info("Model not found — starting download")

    progress = QProgressDialog(
        "Downloading MediaPipe Face Landmarker model…\n"
        "This is a one-time download (~3.5 MB). Please wait.",
        "Cancel",
        0,
        100,
    )
    progress.setWindowTitle("NeuroDrishti — First Run Setup")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumWidth(460)
    progress.setValue(0)
    progress.show()
    app.processEvents()

    cancelled = [False]

    def on_progress(downloaded: int, total: int) -> None:
        if progress.wasCanceled():
            cancelled[0] = True
            return
        if total > 0:
            pct = int(min(downloaded / total * 100, 100))
        else:
            # Unknown total — pulse
            pct = min(progress.value() + 1, 99)
        progress.setValue(pct)
        app.processEvents()

    success = download_model(progress_callback=on_progress)
    progress.close()

    if cancelled[0]:
        QMessageBox.warning(
            None,
            "Download Cancelled",
            "The model download was cancelled.\n"
            "NeuroDrishti cannot run without the face tracking model.",
        )
        return False

    if not success:
        QMessageBox.critical(
            None,
            "Download Failed",
            "Failed to download the face tracking model.\n\n"
            "Please check your internet connection and restart the application.\n"
            f"Log file: ~/.neurodrishti/app.log",
        )
        return False

    progress.setValue(100)
    log.info("Model download complete")
    return True


def main() -> int:
    # ── Qt application ──────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("NeuroDrishti")
    app.setApplicationDisplayName("NeuroDrishti")
    app.setApplicationVersion("2.0")

    # Global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Configuration ───────────────────────────────────────────
    log.info("NeuroDrishti starting — version 2.0")
    config = Config()
    log.info("Configuration loaded")

    # ── Model check / download ──────────────────────────────────
    if not _ensure_model(app):
        return 1

    # ── Speech engine ───────────────────────────────────────────
    try:
        speech = SpeechEngine()
        speech.set_rate(config.get("speech_rate", 150))
        speech.set_volume(config.get("speech_volume", 1.0))
        speech.set_voice_by_index(config.get("speech_voice_index", 0))
        log.info("Speech engine initialised")
    except Exception as exc:
        log.error("Speech engine failed: %s", exc)
        QMessageBox.warning(
            None,
            "Speech Warning",
            f"Text-to-speech could not be initialised:\n{exc}\n\n"
            "The application will run without speech.",
        )
        speech = SpeechEngine()  # still construct so the UI doesn't crash

    # ── Face tracker (QThread) ──────────────────────────────────
    tracker = FaceTrackerWorker(config)

    # ── Main window ─────────────────────────────────────────────
    window = MainWindow(config, tracker, speech)
    window.show()

    # ── Start tracker thread ────────────────────────────────────
    # The camera opens inside the thread; any error is reported via signal
    tracker.start()
    log.info("Tracker thread started")

    # ── Event loop ───────────────────────────────────────────────
    exit_code = app.exec()
    log.info("Application exited with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())