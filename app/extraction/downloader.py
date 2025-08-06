import yt_dlp

def download_video(link: str) -> tuple[str, str]:
    # Use yt_dlp (supports TikTok, IG, YouTube)
    
    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
        description = info.get("description", "")
        return filename, description
