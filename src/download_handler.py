"""
Unified Download Completion Handler

Provides centralized, extensible handling for completed downloads from
both gallery-dl and yt-dlp with a unified data format and pluggable output system.

This module serves as the central point for processing download completion events:
- Normalizes data format from different download engines
- Provides console output with consistent formatting
- Offers extensible architecture for future enhancements (database, webhooks, etc.)
- Handles both successful and failed download events
- Includes timestamp and source tracking

Functions:
    handle_download_completed(data, source): Main unified completion handler
    
Private Functions:
    _normalize_download_data(): Standardizes data format across sources
    _output_to_console(): Handles console output formatting
    _save_to_database(): Placeholder for future database integration
    _send_webhook(): Placeholder for future webhook notifications
    _save_to_file(): Placeholder for future file logging
    _save_as_json(): JSON file export utility

Expected Data Format:
    {
        'url': str,           # Direct download URL
        'filename': str,      # Downloaded filename
        'filepath': str,      # Full file path
        'original_url': str,  # Original webpage URL
        'title': str,         # Content title/description
        'success': bool,      # Download success status
        'error': str,         # Error message if failed
        'timestamp': str,     # ISO timestamp (auto-added)
        'source': str,        # Source engine identifier
    }

Author: MrArachnid
License: GPL-2.0
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


def handle_download_completed(data: Dict[str, Any], source: str = "unknown") -> None:
    """
    Unified handler for completed downloads
    
    Args:
        data: Dictionary containing download information
        source: Source of the download ("gallery-dl" or "yt-dlp")
    
    Expected data format:
    {
        'url': str,           # Direct download URL
        'filename': str,      # Filename of downloaded file
        'filepath': str,      # Full path to downloaded file
        'original_url': str,  # Original webpage URL (optional)
        'title': str,         # Title/description (optional)
        'success': bool,      # Whether download was successful
        'error': str,         # Error message if failed (optional)
        'timestamp': str,     # ISO timestamp (added automatically)
        'source': str,        # Source parser ("gallery-dl" or "yt-dlp")
    }
    """
    
    # Normalize and enrich data
    normalized_data = _normalize_download_data(data, source)
    
    # Current implementation: console output
    _output_to_console(normalized_data)
    
    # Future extensions can be added here:
    # _save_to_database(normalized_data)
    # _send_webhook(normalized_data)
    # _save_to_file(normalized_data)


def _normalize_download_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Normalize download data to consistent format"""
    
    normalized = {
        'url': data.get('url', 'unknown'),
        'filename': data.get('filename', 'unknown'),
        'filepath': data.get('filepath', 'unknown'),
        'original_url': data.get('original_url', data.get('webpage_url', data.get('url', 'unknown'))),
        'title': data.get('title', 'unknown'),
        'success': data.get('success', True),
        'error': data.get('error', None),
        'timestamp': datetime.now().isoformat(),
        'source': source
    }
    
    return normalized


def _output_to_console(data: Dict[str, Any]) -> None:
    """Output download completion to console"""
    
    source_tag = data['source'].upper()
    filename = data['filename']
    url = data['url']
    success = data['success']
    
    if success:
        print(f"[{source_tag}-COMPLETED] File: {filename}, URL: {url}")
    else:
        error_msg = data.get('error', 'Unknown error')
        print(f"[{source_tag}-FAILED] File: {filename}, URL: {url}, Error: {error_msg}")


# Future extension examples:

def _save_to_database(data: Dict[str, Any]) -> None:
    """Save download data to database (placeholder)"""
    # TODO: Implement database logging
    pass


def _send_webhook(data: Dict[str, Any]) -> None:
    """Send webhook notification (placeholder)"""
    # TODO: Implement webhook notifications
    pass


def _save_to_file(data: Dict[str, Any]) -> None:
    """Save download data to log file (placeholder)"""
    # TODO: Implement file logging
    pass


def _save_as_json(data: Dict[str, Any], filepath: str) -> None:
    """Save download data as JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {e}")


if __name__ == "__main__":
    # Test the handler
    test_data = {
        'url': 'https://example.com/image.jpg',
        'filename': 'test_image.jpg',
        'filepath': '/tmp/test_image.jpg',
        'original_url': 'https://example.com/gallery/123',
        'title': 'Test Image',
        'success': True
    }
    
    print("Testing download handler...")
    handle_download_completed(test_data, "gallery-dl")
    handle_download_completed({**test_data, 'success': False, 'error': 'Network timeout'}, "yt-dlp")