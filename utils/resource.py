"""
utils/resource.py
-----------------
Resolves absolute paths for resources, working correctly in both
development (running from source) and production (PyInstaller bundle).
"""

import os
import sys


def resource_path(relative_path: str) -> str:
    """
    Return the absolute path to a resource file.

    When running as a PyInstaller bundle, resources are extracted to a
    temporary folder stored in `sys._MEIPASS`. In development mode, paths
    are resolved relative to the project root (one level above this file).
    """
    try:
        # PyInstaller sets _MEIPASS at runtime
        base_path: str = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # Running from source: project root is the parent of utils/
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)
