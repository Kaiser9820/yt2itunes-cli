# yt2itunes-cli - YouTube to iTunes MP3 Converter (CLI)
Simple command-line tool that:

- Downloads any YouTube video as MP3 (using yt-dlp + FFmpeg)
- Automatically tags the file with title + artist
- Embeds the video thumbnail as album artwork
- Moves the file to iTunes "Automatically Add to iTunes" folder

## Requirements

- Python 3.8+
- FFmpeg (in PATH)
- Packages: `pip install -r requirements.txt`

## Usage

```bash
python cli_converter.py
