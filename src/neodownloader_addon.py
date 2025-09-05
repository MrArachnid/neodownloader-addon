"""
NeoDownloader Addon - Core Download Engine

Universal media downloading engine that combines gallery-dl and yt-dlp
into a unified interface with smart tool detection and async processing.

This module provides the main NeoDownloaderAddon class which:
- Automatically detects the best download tool for each URL
- Manages priority domains for different platforms
- Handles async download processing with stop/resume functionality
- Provides unified completion callbacks through download_handler

Classes:
    NeoDownloaderAddon: Main addon class with unified download interface
    YtDlpStopException: Exception for graceful yt-dlp stopping

Functions:
    set_ytdlp_stop_flag(value): Set global yt-dlp stop flag
    get_ytdlp_stop_flag(): Get current yt-dlp stop flag state

Author: MrArachnid
License: GPL-2.0
"""

import asyncio
import os
import yt_dlp
import gallery_dl
from gallery_dl import config, extractor, job
from urllib.parse import urlparse
from typing import Optional, Dict
import tempfile
from .gallery_dl_patch import apply_patch
from .download_handler import handle_download_completed

# Apply gallery-dl patch on import
apply_patch()

# Global flags to stop downloads
_STOP_YT_DLP = False

def set_ytdlp_stop_flag(value):
    """Set global yt-dlp stop flag"""
    global _STOP_YT_DLP
    _STOP_YT_DLP = value
    if value:
        print("[STOP] yt-dlp stop flag set")

def get_ytdlp_stop_flag():
    """Get yt-dlp stop flag state"""
    global _STOP_YT_DLP
    return _STOP_YT_DLP

class YtDlpStopException(Exception):
    """Exception for stopping yt-dlp"""
    pass

class NeoDownloaderAddon:
    def __init__(self):
        # Priority domains for gallery-dl
        self.gallery_dl_priority = [
            'instagram.com',
            'twitter.com',
            'x.com',
            'artstation.com',
            'deviantart.com',
            'pixiv.net',
            'imgur.com',
            'reddit.com',
            'tumblr.com',
            'pinterest.com'
        ]
        
        # Priority domains for yt-dlp
        self.ytdlp_priority = [
            'youtube.com',
            'youtu.be', 
            'vimeo.com',
            'twitch.tv',
            'tiktok.com'
        ]
    
    def extract_domain(self, url: str) -> str:
        """Extracts domain from URL"""
        try:
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    async def detect_best_tool(self, url: str) -> Dict:
        """Determines the best tool for processing URL"""
        
        domain = self.extract_domain(url)
        
        # For video platforms use yt-dlp directly
        if any(d in domain for d in ['youtube.', 'youtu.be', 'vimeo.', 'twitch.']):
            return {'tool': 'yt-dlp', 'confidence': 1.0, 'reason': 'video platform'}
        
        # For art platforms use gallery-dl directly  
        if any(d in domain for d in ['artstation.', 'pixiv.', 'deviantart.']):
            return {'tool': 'gallery-dl', 'confidence': 1.0, 'reason': 'art platform'}
        
        # For mixed platforms - check both
        gallery_support = await self.check_gallery_dl_support(url)
        ytdlp_support = await self.check_ytdlp_support(url)
        
        if gallery_support and not ytdlp_support:
            return {'tool': 'gallery-dl', 'confidence': 0.8, 'reason': 'gallery-dl only'}
        elif ytdlp_support and not gallery_support:
            return {'tool': 'yt-dlp', 'confidence': 0.8, 'reason': 'yt-dlp only'}
        elif gallery_support and ytdlp_support:
            # Both support - choose by domain priority
            if any(d in domain for d in self.gallery_dl_priority):
                return {'tool': 'gallery-dl', 'confidence': 0.9, 'reason': 'both support, gallery-dl priority'}
            else:
                return {'tool': 'yt-dlp', 'confidence': 0.9, 'reason': 'both support, yt-dlp priority'}
        else:
            return {'tool': None, 'confidence': 0, 'reason': 'not supported'}
    
    async def check_gallery_dl_support(self, url: str) -> bool:
        """Check gallery-dl support"""
        try:
            # Use gallery-dl API to check support
            def check_support():
                try:
                    ex = extractor.find(url)
                    return ex is not None
                except:
                    return False
            
            result = await asyncio.get_event_loop().run_in_executor(None, check_support)
            return result
        except:
            return False
    
    async def check_ytdlp_support(self, url: str) -> bool:
        """Check yt-dlp support"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ydl.extract_info(url, download=False, process=False)
                )
                return True
        except:
            return False
    
    async def parse(self, url: str):
        """Main parsing method"""
        
        print(f"[PARSER] Starting to parse: {url}")
        
        # Determine the best tool
        detection = await self.detect_best_tool(url)
        
        print(f"[PARSER] Selected tool: {detection['tool']} (confidence: {detection['confidence']}, reason: {detection.get('reason', 'N/A')})")
        
        if detection['tool'] == 'gallery-dl':
            await self.parse_with_gallery_dl(url)
        elif detection['tool'] == 'yt-dlp':
            await self.parse_with_ytdlp(url)
        else:
            raise Exception(f"URL not supported by media parsers: {url}")
    
    async def parse_with_gallery_dl(self, url: str):
        """Parsing via gallery-dl"""
        print(f"[GALLERY-DL] Processing: {url}")
        
        def gallery_dl_process():
            try:
                # Create temporary directory for download
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Configure gallery-dl settings
                    config.clear()
                    config.load()
                    config.set((), "base-directory", temp_dir)
                    
                    # Create custom event handler
                    downloaded_files = []
                    
                    def prepare_hook(pathfmt):
                        print(f"[PREPARE] Preparing download: {pathfmt.kwdict.get('url', 'unknown')}")
                    
                    def prepare_after_hook(pathfmt):
                        print(f"[PREPARE_AFTER] After preparation: {pathfmt.kwdict.get('url', 'unknown')}")
                    
                    def error_hook(pathfmt):
                        print(f"[ERROR] Download error: {pathfmt.kwdict.get('url', 'unknown')}")
                    
                    def file_hook(pathfmt):
                        file_path = str(pathfmt.path) if pathfmt.path else "unknown"
                        direct_url = pathfmt.kwdict.get("url", pathfmt.kwdict.get("_http_url", "unknown"))
                        filename = pathfmt.filename or pathfmt.kwdict.get("filename", "unknown")
                        
                        print(f"[FILE] File processed: {file_path}")
                        print(f"[FILE_URL] Direct: {direct_url}")
                        print(f"[FILE_NAME] {filename}")
                        # print(f"[FILE_KWDICT] Keys: {list(pathfmt.kwdict.keys())}")
                        print("[FILE_KWDICT]", pathfmt.kwdict)
                        
                        downloaded_files.append({
                            'path': file_path,
                            'url': direct_url,
                            'filename': filename
                        })
                    
                    def after_hook(pathfmt):
                        file_path = str(pathfmt.path) if pathfmt.path else "unknown"
                        direct_url = pathfmt.kwdict.get("url", pathfmt.kwdict.get("_http_url", "unknown"))
                        filename = pathfmt.filename or pathfmt.kwdict.get("filename", "unknown")
                        
                        print(f"[AFTER] After successful download: {file_path}")
                        print(f"[AFTER_URL] Direct: {direct_url}")
                        print(f"[AFTER_NAME] {filename}")
                    
                    def post_hook(pathfmt):
                        print(f"[POST] Directory processing: {pathfmt.directory if hasattr(pathfmt, 'directory') else 'unknown'}")
                    
                    def post_after_hook(pathfmt):
                        print(f"[POST_AFTER] After directory processing: {pathfmt.directory if hasattr(pathfmt, 'directory') else 'unknown'}")
                    
                    def skip_hook(pathfmt):
                        print(f"[SKIP] File skipped: {pathfmt.path}")
                    
                    def finalize_hook(pathfmt):
                        print(f"[FINALIZE] Job finalization: {pathfmt.path if pathfmt.path else 'job complete'}")
                    
                    def finalize_error_hook(pathfmt):
                        print(f"[FINALIZE_ERROR] Job finalization with error: {pathfmt.path if pathfmt.path else 'job error'}")
                    
                    def finalize_success_hook(pathfmt):
                        print(f"[FINALIZE_SUCCESS] Job finalization success: {pathfmt.path if pathfmt.path else 'job success'}")
                    
                    def init_hook(pathfmt):
                        print(f"[INIT] Initialization: {pathfmt.directory if hasattr(pathfmt, 'directory') else 'starting'}")
                    
                    # Create download task (hook now built into CustomDownloadJob)
                    download_job = job.DownloadJob(url)
                    
                    # Start download
                    download_job.run()
                    
                    print(f"[GALLERY-DL] Completed processing.")
                            
            except Exception as e:
                print(f"[ERROR] Gallery-dl failed: {e}")
                raise
        
        # Run gallery-dl in separate thread
        await asyncio.get_event_loop().run_in_executor(None, gallery_dl_process)
    
    async def parse_with_ytdlp(self, url: str):
        """Parsing via yt-dlp"""
        print(f"[YT-DLP] Processing: {url}")
        
        def progress_hook(d):
            # Check stop flag on each progress update
            if get_ytdlp_stop_flag():
                print(f"[STOP] Stopping yt-dlp download: {d.get('filename', 'unknown')}")
                raise YtDlpStopException("User requested stop")
                
            if d['status'] == 'downloading':
                filename = d.get('filename', 'unknown')
                print(f"[YT-DLP DOWNLOADING] File: {filename}")
                if 'webpage_url' in d:
                    print(f"[YT-DLP URL] Source: {d['webpage_url']}")
            elif d['status'] == 'finished':
                filename = d.get('filename', 'unknown')
                print(f"[YT-DLP DOWNLOADED] File: {filename}")
            elif d['status'] == 'error':
                print(f"[YT-DLP ERROR] {d.get('filename', 'unknown')}")
        
        def post_hook(filepath):
            """Hook after download completion and basic post-processing"""
            if get_ytdlp_stop_flag():
                print("[STOP] Stopping yt-dlp post-processing")
                raise YtDlpStopException("User requested stop")
                
            # yt-dlp passes file path as string
            # Collect completed download data
            download_data = {
                'url': url,
                'filename': os.path.basename(filepath) if filepath else 'unknown',
                'filepath': filepath if filepath else 'unknown',
                'title': 'unknown',  # No access to info_dict in post_hook
                'success': True,
                'error': None,
                'info_dict': {}
            }
            
            self._call_ytdlp_download_completed(download_data)
        
        def error_hook(d):
            """Hook for error handling"""
            error_msg = str(d.get('error', 'Unknown error'))
            download_data = {
                'url': url,
                'filename': d.get('filename', 'unknown'),
                'filepath': None,
                'title': 'unknown',
                'success': False,
                'error': error_msg,
                'info_dict': {}
            }
            
            self._call_ytdlp_download_completed(download_data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'post_hooks': [post_hook],
                'postprocessor_hooks': [],  # Can add later for conversion tracking
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    await asyncio.get_event_loop().run_in_executor(
                        None, lambda: ydl.download([url])
                    )
            except YtDlpStopException:
                print("[YT-DLP] Download stopped by user")
            except Exception as e:
                # Call error_hook manually for unhandled errors
                error_hook({
                    'filename': 'unknown',
                    'error': e
                })
                raise
    
    def _call_ytdlp_download_completed(self, data):
        """yt-dlp download completion handler"""
        handle_download_completed(data, source="yt-dlp")