# yt2itunes-cli - YouTube to iTunes MP3 Converter (CLI)

**Important:** This is my personal project. You are welcome to use it for yourself or share the link with friends.  
However, please **do not** re-upload it to your own GitHub/other sites, remove my name, claim you created it, or present it as your own work.  
If you make improvements, feel free to fork it and send a pull request — happy to give credit.

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
