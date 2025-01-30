"""
Package for interfacing with version control systems
"""

from .addon import VERSION_CONTROL_ADDON_DIR
from .addon import VersionControlAddon
from .tray_addon import VersionControlTray

__all__ = (
    "VersionControlAddon",
    "VersionControlTray",
    "VERSION_CONTROL_ADDON_DIR",
)
