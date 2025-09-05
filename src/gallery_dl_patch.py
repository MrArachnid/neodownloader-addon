"""
Gallery-dl Monkey Patch Module

Provides monkey patching functionality for gallery-dl to add custom
download completion tracking and stop functionality.

This module patches the gallery-dl DownloadJob class to:
- Add global stop flag support with StopExtraction exceptions
- Intercept download completion events for unified handling
- Provide custom download completion callbacks
- Enable graceful stopping of gallery-dl operations

Classes:
    CustomDownloadJob: Patched DownloadJob with stop support and completion tracking

Functions:
    set_stop_flag(value): Set global gallery-dl stop flag
    get_stop_flag(): Get current gallery-dl stop flag state
    apply_patch(): Apply the monkey patch to gallery-dl
    remove_patch(): Remove the monkey patch and restore original

Author: MrArachnid
License: GPL-2.0
"""

import gallery_dl.job
from .download_handler import handle_download_completed

# Global flag to stop all downloads
_STOP_ALL_DOWNLOADS = False

def set_stop_flag(value):
    """Set global stop flag"""
    global _STOP_ALL_DOWNLOADS
    _STOP_ALL_DOWNLOADS = value
    if value:
        print("[STOP] Global download stop flag set")

def get_stop_flag():
    """Get stop flag state"""
    global _STOP_ALL_DOWNLOADS
    return _STOP_ALL_DOWNLOADS


class CustomDownloadJob(gallery_dl.job.DownloadJob):
    """Custom DownloadJob with download-completed hook"""
    
    def __init__(self, url, parent=None):
        super().__init__(url, parent)
        # print(f"[DEBUG] CustomDownloadJob created for URL: {url}")
    
    def handle_url(self, url, kwdict):
        """
        Overridden handle_url:
        1. Checks stop flag
        2. Calls original function
        3. Calls custom download-completed hook
        """
        
        # Check stop flag before starting download
        if get_stop_flag():
            print(f"[STOP] Stopping data extraction: {url}")
            from gallery_dl import exception
            raise exception.StopExtraction()
        
        # Save data before processing
        download_data = {
            'url': url,
            'original_url': kwdict.get('webpage_url', url),
            'filename': None,
            'filepath': None,
            'success': False,
            'error': None,
            'kwdict': kwdict.copy()
        }
        
        try:
            # Check stop flag again during processing
            if get_stop_flag():
                print(f"[STOP] Stopping processing: {url}")
                from gallery_dl import exception
                raise exception.StopExtraction()
            
            # Call original handle_url
            result = super().handle_url(url, kwdict)
            
            # Get file info after processing
            if hasattr(self, 'pathfmt') and self.pathfmt:
                download_data['filename'] = self.pathfmt.filename
                download_data['filepath'] = str(self.pathfmt.path) if self.pathfmt.path else None
            
            download_data['success'] = True
            
            # Call custom download-completed hook
            self._call_download_completed(download_data)
            
            return result
            
        except Exception as e:
            download_data['success'] = False
            download_data['error'] = str(e)
            
            # Call hook even on error
            self._call_download_completed(download_data)
            
            raise
    
    def _call_download_completed(self, data):
        """Calls unified download completion handler"""
        handle_download_completed(data, source="gallery-dl")
    
    # Stub other hooks for now
    def handle_directory(self, kwdict):
        """Stub for handle_directory"""
        return super().handle_directory(kwdict)
    
    def handle_queue(self, url, kwdict):
        """Overridden handle_queue with stop flag check"""
        # Check stop flag before queuing
        if get_stop_flag():
            print(f"[STOP] Stopping queue addition: {url}")
            from gallery_dl import exception
            raise exception.StopExtraction()
        
        return super().handle_queue(url, kwdict)


def apply_patch():
    """Applies monkey patch for DownloadJob"""
    # Save reference to original class
    gallery_dl.job._OriginalDownloadJob = gallery_dl.job.DownloadJob
    
    # Replace with our custom class
    gallery_dl.job.DownloadJob = CustomDownloadJob
    
    print("Gallery-dl patch applied: DownloadJob replaced with CustomDownloadJob")
    print(f"Current DownloadJob class: {gallery_dl.job.DownloadJob}")
    print(f"Original DownloadJob class: {gallery_dl.job._OriginalDownloadJob}")


def remove_patch():
    """Removes monkey patch"""
    if hasattr(gallery_dl.job, '_OriginalDownloadJob'):
        gallery_dl.job.DownloadJob = gallery_dl.job._OriginalDownloadJob
        delattr(gallery_dl.job, '_OriginalDownloadJob')
        print("Gallery-dl patch removed: Original DownloadJob restored")


if __name__ == "__main__":
    # Test patch
    apply_patch()
    
    # Test code can be added here
    print("Patch is ready to use!")
    print("Import this module and call apply_patch() before using gallery-dl")