# Addon for NeoDownloader - GUI for yt-dlp and gallery-dl

REST API addon for [NeoDownloader](https://www.neodownloader.com) - a free Windows bulk media downloader that provides GUI interface for gallery-dl and yt-dlp. This addon extends NeoDownloader's capabilities by integrating these engines, providing support for 1000+ additional websites through a unified API with async queue management.

## Features

🚀 **Unified Interface** - Single API for both yt-dlp and gallery-dl downloaders  
⚡ **Async Processing** - Non-blocking queue-based download management  
🛑 **Stop/Resume** - Full control over download processes  
🌐 **RESTful API** - Easy integration via HTTP endpoints  
🔧 **Download Engine Extension** - Extends NeoDownloader with gallery-dl and yt-dlp support  
🎯 **Smart Detection** - Automatic tool selection based on URL domain  
📊 **Progress Tracking** - Real-time download status and completion events  

## Architecture

```
neodownloader-addon/
├── src/                           # Python source code
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI web server with queue management
│   ├── neodownloader_addon.py    # Core addon logic and download engines
│   ├── gallery_dl_patch.py       # Monkey patch for gallery-dl integration
│   └── download_handler.py       # Unified download completion handler
├── static/                        # Static web files
│   └── index.html                # Web interface for testing and control
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Supported Platforms

### yt-dlp (Video/Audio)  
- YouTube, Vimeo, Twitch
- TikTok, and 1000+ video sites

### Gallery-dl (Images/Media)
- Instagram, Twitter/X, ArtStation  
- DeviantArt, Pixiv, Imgur
- Reddit, Tumblr, Pinterest
- And 100+ more sites

## Installation

```bash
# Clone repository
git clone https://github.com/MrArachnid/neodownloader-addon.git
cd neodownloader-addon

# Install dependencies
pip install -r requirements.txt

# Run server
python -m src.main
```

## API Endpoints

### POST /parse
Add URL to download queue
```json
{
  "url": "https://example.com/media"
}
```

### POST /stop  
Stop all downloads and clear queue

### POST /quit
Stop downloads and shutdown server

### GET /queue/status
Get current queue status

### GET /health
Service health check

## Usage Examples

### Add URL to queue
```bash
curl -X POST http://localhost:8001/parse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=example"}'
```

### Check queue status
```bash
curl http://localhost:8001/queue/status
```

### Stop all downloads
```bash
curl -X POST http://localhost:8001/stop
```

## Web Interface for Testing

Open `http://localhost:8001` in browser for interactive control panel to test the REST API functionality. This web interface demonstrates the API capabilities that power the NeoDownloader GUI application.

## Configuration

The addon automatically detects the best download tool based on URL:

- **Video platforms** → yt-dlp (YouTube, Vimeo, etc.)
- **Art platforms** → gallery-dl (ArtStation, DeviantArt, etc.)  
- **Mixed platforms** → Smart detection with priority rules

## Integration with NeoDownloader

This addon extends [NeoDownloader](https://www.neodownloader.com) - a Windows bulk media downloader that provides GUI interface for gallery-dl and yt-dlp among other capabilities. The addon provides additional engine support by integrating:

- **gallery-dl engine** - Support for 100+ art/image platforms (Instagram, Twitter, DeviantArt, etc.)
- **yt-dlp engine** - Support for 1000+ video platforms (YouTube, TikTok, Vimeo, etc.) 
- **Unified management** - Single API for controlling both engines
- **Extended coverage** - Dramatically expands supported websites beyond NeoDownloader's native capabilities

## Development

### Adding New Download Handlers

Extend `download_handler.py` to add custom completion handlers:

```python
def handle_download_completed(data, source):
    # Your custom logic here
    _save_to_database(data)
    _send_webhook(data)
    _output_to_console(data)
```

### Extending Platform Support

Add new domains to priority lists in `src/neodownloader_addon.py` - `NeoDownloaderAddon.__init__()`.

### Running in Development

```bash
# Run with hot reload
python -m src.main

# Or run directly
cd src && python main.py
```

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## Links

- **NeoDownloader**: https://www.neodownloader.com
- **gallery-dl**: https://github.com/mikf/gallery-dl  
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.