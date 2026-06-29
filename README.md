# yt2itunes-cli - YouTube to iTunes MP3 Converter (Enriched CLI)

**Important:** This is my personal project. You are welcome to use it for yourself or share the link with friends.  
However, please **do not** re-upload it to your own GitHub/other sites, remove my name, claim you created it, or present it as your own work.  
If you make improvements, feel free to fork it and send a pull request — happy to give credit.

---

A smart command-line tool that seamlessly downloads YouTube videos as MP3s, intelligently categorizes them, enriches their metadata using external databases, and automatically imports them into iTunes.

## Features

- **High-Quality Audio:** Downloads any YouTube video as an MP3 using `yt-dlp` and FFmpeg.
- **Smart Content Classification:** Automatically detects if a video is a TV Show episode, Music Video, or General content based on the title and YouTube categories.
- **External Metadata Enrichment:** - **Music:** Queries the **MusicBrainz** API for accurate official album names and release dates.
  - **TV Shows:** Queries the **TVmaze** API to tag the correct series name, network/creator, and genres.
- **Artwork Embedding:** Automatically downloads and embeds the highest quality video thumbnail as the track's album artwork.
- **Auto-Import:** Moves the finished file directly to your iTunes/Apple Music "Automatically Add to iTunes" folder so it syncs immediately.
- **Resilient Fallbacks:** Gracefully falls back to default YouTube metadata if external database lookups fail or rate-limit.

## Requirements

- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) (Must be installed and added to your system PATH)
- Required Python packages:
  
  ```bash
  pip install -r requirements.txt
