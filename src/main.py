#!/usr/bin/env python3
"""
NeoDownloader Addon - Main FastAPI Server

A universal media downloading addon for NeoDownloader project.
Provides REST API endpoints for queue management and download control.

Features:
- Async queue-based processing
- Unified gallery-dl and yt-dlp integration  
- Real-time download progress tracking
- Stop/resume functionality
- Web interface for testing

Author: MrArachnid
License: GPL-2.0
Repository: https://github.com/MrArachnid/neodownloader-addon
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from .neodownloader_addon import NeoDownloaderAddon
import os
from .gallery_dl_patch import set_stop_flag
from .neodownloader_addon import set_ytdlp_stop_flag

app = FastAPI(title="NeoDownloader Addon", version="1.0.0")
parser = NeoDownloaderAddon()

# Global queue manager
class QueueManager:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_processing = False
        self.should_stop = False
        self.current_task = None
        
    async def add_url(self, url: str):
        """Add URL to queue"""
        await self.queue.put(url)
        print(f"[QUEUE] URL added to queue: {url}")
        print(f"[QUEUE] Queue size: {self.queue.qsize()}")
        
    async def start_processing(self):
        """Start queue processing if not active"""
        if not self.is_processing and not self.queue.empty():
            # Reset gallery-dl stop flag on new start
            set_stop_flag(False)
            
            self.is_processing = True
            self.should_stop = False
            self.current_task = asyncio.create_task(self.process_queue())
            
    async def process_queue(self):
        """Process queue sequentially"""
        print("[QUEUE] Queue processing started")
        
        try:
            while not self.queue.empty() and not self.should_stop:
                try:
                    url = await self.queue.get()
                    print(f"[QUEUE] Processing URL: {url}")
                    
                    # Check stop flag before processing
                    if self.should_stop:
                        print("[QUEUE] Stopping by user request")
                        self.queue.task_done()
                        break
                    
                    # Process URL through parser
                    await parser.parse(url)
                    
                    # Mark task as completed
                    self.queue.task_done()
                    
                except Exception as e:
                    print(f"[QUEUE] Error processing URL: {e}")
                    self.queue.task_done()
                    
        finally:
            # Always reset flags on completion
            self.is_processing = False
            self.current_task = None
            
            if self.should_stop:
                print("*" * 80)
                print("QUEUE PROCESSING STOPPED")  
                print("*" * 80)
            elif self.queue.empty():
                print("*" * 80)
                print("QUEUE PROCESSING COMPLETED")  
                print("*" * 80)
    
    async def stop_processing(self):
        """Stop processing and clear queue"""
        print("[QUEUE] Processing stop requested")
        
        # Set global stop flags for all parsers
        set_stop_flag(True)          # gallery-dl
        set_ytdlp_stop_flag(True)    # yt-dlp
        
        # Set queue stop flag
        self.should_stop = True
        
        # Cancel current task if exists
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        
        # Clear queue
        cleared_count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                cleared_count += 1
            except asyncio.QueueEmpty:
                break
        
        # Reset flags
        self.is_processing = False
        self.current_task = None
        
        print(f"[QUEUE] Processing stopped. Cleared {cleared_count} URLs from queue")
        return cleared_count

# Create global queue manager instance
queue_manager = QueueManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class URLRequest(BaseModel):
    url: str

@app.get("/")
async def serve_index():
    """Serves the main HTML page"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        raise HTTPException(status_code=404, detail="index.html not found")

@app.post("/parse")
async def parse_url(request: URLRequest):
    """Adds URL to queue for processing"""
    try:
        # Add URL to queue
        await queue_manager.add_url(request.url)
        
        # Start queue processing if not active
        await queue_manager.start_processing()
        
        return {
            "status": "queued", 
            "message": f"URL added to queue: {request.url}",
            "queue_size": queue_manager.queue.qsize()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_processing():
    """Stop processing and clear queue"""
    try:
        cleared_count = await queue_manager.stop_processing()
        return {
            "status": "stopped",
            "message": "Processing stopped and queue cleared",
            "cleared_urls": cleared_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quit")
async def quit_application():
    """Stop processing and quit application"""
    try:
        # First stop processing
        cleared_count = await queue_manager.stop_processing()
        
        print("=" * 80)
        print("APPLICATION SHUTDOWN")
        print(f"Cleared {cleared_count} URLs from queue")
        print("=" * 80)
        
        # Return response to client before shutdown
        response = {
            "status": "shutting_down",
            "message": "Application is shutting down",
            "cleared_urls": cleared_count
        }
        
        # Terminate process after small delay
        import asyncio
        asyncio.create_task(delayed_exit())
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delayed_exit():
    """Terminate process with small delay"""
    await asyncio.sleep(1)  # Give time to send response to client
    print("Shutting down...")
    import os
    os._exit(0)

@app.get("/queue/status")
async def queue_status():
    """Processing queue status"""
    return {
        "queue_size": queue_manager.queue.qsize(),
        "is_processing": queue_manager.is_processing,
        "status": "processing" if queue_manager.is_processing else "idle"
    }

@app.get("/health")
async def health_check():
    """Service health check"""
    return {"status": "ok", "service": "NeoDownloader Addon"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)