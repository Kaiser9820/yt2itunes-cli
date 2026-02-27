#!/usr/bin/env python3
"""
YouTube to MP3 Converter CLI
Downloads YouTube videos as MP3, adds metadata & album artwork,
and moves files to iTunes "Automatically Add to iTunes" folder.

Requirements:
    pip install yt-dlp mutagen pillow
    FFmpeg must be installed and in your PATH

Usage:
    python cli_converter.py

License: MIT
"""

import os
import time
import yt_dlp
import requests
from io import BytesIO
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError


# ────────────────────────────────────────────────
# CONFIGURATION – users can change these
# ────────────────────────────────────────────────

DOWNLOAD_DIR = os.path.expanduser("~/Downloads/ConvertedAudio")
ITUNES_AUTO_ADD = os.path.expanduser("~/Music/iTunes/iTunes Media/Automatically Add to iTunes")

# Create download folder if missing (iTunes folder should already exist)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_and_process(url: str) -> None:
    """Download video as MP3, tag it, add artwork, move to iTunes."""
    print("Downloading audio...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # 128, 192, 256, 320 possible
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(uploader)s - %(title)s.%(ext)s'),
        'continuedl': True,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # ────── Metadata preparation ──────
    title = info.get('title', 'Unknown Title')
    uploader = info.get('uploader') or info.get('channel') or 'Unknown Artist'
    artist = uploader

    # Attempt to parse "Artist - Title" pattern
    if ' - ' in title:
        parts = title.split(' - ', 1)
        if len(parts[0]) < 40 and parts[0].strip():
            artist = parts[0].strip()
            title = parts[1].strip()

    print(f"  Artist: {artist}")
    print(f"  Title:  {title}")

    # ────── Find the downloaded MP3 file ──────
    mp3_path = None
    latest_mtime = 0
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.lower().endswith('.mp3'):
            path = os.path.join(DOWNLOAD_DIR, filename)
            mtime = os.path.getmtime(path)
            if mtime > latest_mtime:
                latest_mtime = mtime
                mp3_path = path

    if not mp3_path or os.path.getsize(mp3_path) < 100_000:
        print("Could not locate MP3 file. Check download folder manually.")
        return

    print(f"File: {os.path.basename(mp3_path)}")

    # ────── Write ID3 metadata ──────
    try:
        tags = EasyID3(mp3_path)
    except ID3NoHeaderError:
        tags = EasyID3()
        tags.save(mp3_path)

    tags['title'] = title
    tags['artist'] = artist
    tags['album'] = 'YouTube Singles'  # ← customize or remove
    # tags['genre'] = 'Unknown'
    # tags['date'] = info.get('upload_date', '')[:4]  # year
    tags.save(mp3_path)

    print("Metadata tags updated.")

    # ────── Embed album artwork (thumbnail) ──────
    thumbnail_url = info.get('thumbnail')
    if thumbnail_url:
        try:
            print("Adding album artwork...")
            resp = requests.get(thumbnail_url, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                img_buffer = BytesIO()
                img.convert('RGB').save(img_buffer, format='JPEG')
                cover_bytes = img_buffer.getvalue()

                id3_tags = ID3(mp3_path)
                id3_tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # front cover
                    desc='Cover',
                    data=cover_bytes
                ))
                id3_tags.save(mp3_path, v2_version=3)
                print("Album artwork embedded.")
            else:
                print("Failed to download thumbnail.")
        except Exception as e:
            print(f"Could not add artwork: {e}")

    # ────── Move to iTunes auto-add folder ──────
    target_path = os.path.join(ITUNES_AUTO_ADD, os.path.basename(mp3_path))
    try:
        os.replace(mp3_path, target_path)
        print(f"\nSuccess! File moved to:")
        print(f"  {target_path}")
        print("→ Open iTunes → it should import automatically → sync your device.")
    except Exception as e:
        print(f"Could not move file: {e}")
        print("File remains in:", mp3_path)


def main():
    print("YouTube to MP3 → iTunes Tool")
    print("Paste a YouTube URL or type 'quit' / 'q' / 'exit'")
    print("-" * 60)

    while True:
        url = input("\nPaste YouTube URL: ").strip()
        if url.lower() in ['quit', 'q', 'exit']:
            print("Goodbye.")
            break
        if not url:
            continue
        if "youtube.com" not in url and "youtu.be" not in url:
            print("Not a valid YouTube URL.")
            continue

        download_and_process(url)
        print("-" * 60)


if __name__ == "__main__":
    main()
