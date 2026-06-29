#!/usr/bin/env python3
"""
YouTube to MP3 Converter CLI
Downloads YouTube videos as MP3, adds enriched metadata via external APIs, 
embeds album artwork, and moves files to iTunes "Automatically Add to iTunes" folder.

Requirements:
    pip install yt-dlp mutagen pillow requests
    FFmpeg must be installed and in your PATH
"""

import os
import re
import yt_dlp
import requests
from io import BytesIO
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

# ────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────

DOWNLOAD_DIR = os.path.expanduser("~/Downloads/ConvertedAudio")
ITUNES_AUTO_ADD = os.path.expanduser("~/Music/iTunes/iTunes Media/Automatically Add to iTunes")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ────────────────────────────────────────────────
# METADATA ENRICHMENT APIs
# ────────────────────────────────────────────────

def classify_content(title: str, categories: list) -> str:
    """Determine if the video is a TV Show, Music, or General Video."""
    categories = [c.lower() for c in (categories or [])]
    title_lower = title.lower()

    # Look for S01E01, Season 1 Ep 2, etc.
    tv_pattern = re.search(r'(s\d{1,2}\s*e\d{1,2}|season\s*\d+\s*episode\s*\d+)', title_lower)
    if tv_pattern or 'shows' in categories or 'film & animation' in categories:
        return 'tv_show'

    if 'music' in categories or 'official music video' in title_lower:
        return 'music'

    return 'general'

def enrich_music(artist: str, title: str) -> dict:
    """Fetch enriched song metadata from MusicBrainz."""
    # MusicBrainz requires a descriptive User-Agent to prevent rate-limiting blocks
    headers = {'User-Agent': 'YTMetadataEnricher/1.0 ( your-email@example.com )'}
    query = f'recording:"{title}" AND artist:"{artist}"'
    url = f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json&limit=1"
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('recordings'):
            recording = data['recordings'][0]
            # Grab the first associated release (Album)
            album = recording.get('releases', [{}])[0].get('title')
            date = recording.get('first-release-date', '')[:4]
            return {'album': album, 'date': date, 'genre': 'Music'}
    except requests.RequestException as e:
        print(f"  [!] MusicBrainz lookup failed: {e}")
        
    return {}

def enrich_tv(title: str, uploader: str) -> dict:
    """Extract show name and fetch metadata from TVmaze."""
    # Attempt to isolate show name before "S01E01" or "-"
    show_name = uploader 
    match = re.split(r'(?i)(s\d{1,2}\s*e\d{1,2}|-)', title)
    if match and match[0].strip():
        show_name = match[0].strip()

    url = f"https://api.tvmaze.com/search/shows?q={show_name}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        if data:
            show = data[0]['show']
            genres = ", ".join(show.get('genres', []))
            network = show.get('network', {}).get('name') or show.get('webChannel', {}).get('name') or uploader
            return {
                'artist': network,           # Set Network/Creator as Artist
                'album': show.get('name'),   # Set Show Name as Album
                'genre': genres if genres else 'TV Show',
                'date': show.get('premiered', '')[:4]
            }
    except requests.RequestException as e:
        print(f"  [!] TVmaze lookup failed: {e}")
        
    return {}


# ────────────────────────────────────────────────
# CORE PROCESSING
# ────────────────────────────────────────────────

def download_and_process(url: str) -> None:
    print("Downloading audio...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(uploader)s - %(title)s.%(ext)s'),
        'continuedl': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            print(f"Failed to download video: {e}")
            return

    # ────── Base Metadata Extraction ──────
    yt_title = info.get('title', 'Unknown Title')
    yt_uploader = info.get('uploader') or info.get('channel') or 'Unknown Artist'
    yt_date = info.get('upload_date', '')[:4] if info.get('upload_date') else ''
    categories = info.get('categories', [])

    # Dictionary to hold our final tags
    meta = {
        'title': yt_title,
        'artist': yt_uploader,
        'album': 'YouTube Singles',
        'date': yt_date,
        'genre': 'Podcast/Web'
    }

    # Attempt to parse standard "Artist - Title" pattern
    if ' - ' in yt_title:
        parts = yt_title.split(' - ', 1)
        if len(parts[0]) < 40 and parts[0].strip():
            meta['artist'] = parts[0].strip()
            meta['title'] = parts[1].strip()

    # ────── Content Classification & API Routing ──────
    content_type = classify_content(yt_title, categories)
    
    if content_type == 'music':
        print(f"  🎵 Detected Music. Querying MusicBrainz...")
        enriched = enrich_music(meta['artist'], meta['title'])
        meta.update({k: v for k, v in enriched.items() if v})

    elif content_type == 'tv_show':
        print(f"  📺 Detected TV Show. Querying TVmaze...")
        enriched = enrich_tv(yt_title, yt_uploader)
        meta.update({k: v for k, v in enriched.items() if v})
    else:
        print("  🎬 Detected General Video. Using default metadata.")

    print(f"  Title:  {meta['title']}")
    print(f"  Artist: {meta['artist']}")
    print(f"  Album:  {meta['album']}")

    # ────── Locate the MP3 file ──────
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

    # ────── Write ID3 Metadata ──────
    try:
        tags = EasyID3(mp3_path)
    except ID3NoHeaderError:
        tags = EasyID3()
        tags.save(mp3_path)

    for key, value in meta.items():
        if value:
            tags[key] = value
    tags.save(mp3_path)
    print("  ✓ Text metadata tags updated.")

    # ────── Embed album artwork ──────
    thumbnail_url = info.get('thumbnail')
    if thumbnail_url:
        try:
            resp = requests.get(thumbnail_url, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                img_buffer = BytesIO()
                # Ensure image is RGB for JPEG compatibility (handles WEBP thumbnails with alpha)
                img.convert('RGB').save(img_buffer, format='JPEG')
                
                id3_tags = ID3(mp3_path)
                id3_tags.add(APIC(
                    encoding=3, mime='image/jpeg', type=3, desc='Cover',
                    data=img_buffer.getvalue()
                ))
                id3_tags.save(mp3_path, v2_version=3)
                print("  ✓ Album artwork embedded.")
        except Exception as e:
            print(f"  [!] Could not add artwork: {e}")

    # ────── Move to iTunes ──────
    target_path = os.path.join(ITUNES_AUTO_ADD, os.path.basename(mp3_path))
    try:
        os.replace(mp3_path, target_path)
        print(f"\nSuccess! File routed to iTunes directory.")
    except Exception as e:
        print(f"Could not move file: {e}\nFile remains in: {mp3_path}")


def main():
    print("YouTube to MP3 → iTunes Tool (Enriched Version)")
    print("-" * 60)
    while True:
        url = input("\nPaste YouTube URL (or 'q' to quit): ").strip()
        if url.lower() in ['quit', 'q', 'exit']:
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
