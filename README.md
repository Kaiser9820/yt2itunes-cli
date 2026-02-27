# yt2itunes-cli - YouTube to iTunes MP3 Downloader

A simple command-line tool that:

- Downloads YouTube videos as high-quality MP3
- Uses yt-dlp + FFmpeg
- Automatically tags the file (title + artist)
- Moves it to iTunes "Automatically Add to iTunes" folder

## Requirements

- Python 3.8+
- yt-dlp (`pip install yt-dlp`)
- mutagen (`pip install mutagen`)
- FFmpeg (installed and in PATH)

## Usage

```bash
python cli_converter.py
