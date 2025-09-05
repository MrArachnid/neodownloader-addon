"""
NeoDownloader Addon - Engine Extension Module

REST API addon that extends NeoDownloader's capabilities by integrating gallery-dl 
and yt-dlp engines. Provides unified interface and async queue management to support 
1000+ additional websites beyond NeoDownloader's native functionality.
"""

__version__ = "1.0.0"
__author__ = "MrArachnid"
__description__ = "Engine extension addon for NeoDownloader - integrates gallery-dl and yt-dlp for 1000+ additional websites"

from .neodownloader_addon import NeoDownloaderAddon
from .download_handler import handle_download_completed

__all__ = [
    "NeoDownloaderAddon",
    "handle_download_completed"
]