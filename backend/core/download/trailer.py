# Extract youtube video id from url
import re
import time

from yt_dlp import YoutubeDL


def _get_youtube_id(url: str):
    regex = re.compile(
        r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
    )
    match = regex.match(url)
    if match and len(match.group(2)) == 11:
        return match.group(2)
    else:
        return None


def _search_yt_for_trailer(movie_title: str, movie_year: str | None = None):
    # Set options
    options = {
        "format": "best",
    }
    # Construct search query with keywords
    keywords = [f"{movie_title}", "trailer", f"{movie_year}"]
    search_query = "ytsearch:" + " ".join(keywords)

    # Search for video
    with YoutubeDL(options) as ydl:
        search_results = ydl.extract_info(search_query, download=False, process=True)

    # If results are invalid, return None
    if not search_results or isinstance(search_results, dict):
        return None
    if "entries" not in search_results:
        return None
    # Return the first search result video id
    for result in search_results["entries"]:
        return str(result["id"])


def progress_hook(d):
    if d["status"] == "downloading":
        print(f"'abcdefg': Downloading {d['_percent_str']} of {d['_total_bytes_str']}")
    if d["status"] == "error":
        print(f"'abcdefg': Error downloading {d['filename']}")
    if d["status"] == "finished":  # Guaranteed to call
        print("'abcdefg': Done downloading, now converting ...")


def postprocessor_hook(d):
    pprocessor = d["postprocessor"]
    if d["status"] == "started":  # Guaranteed to call
        print(f"{time.ctime()}: '{pprocessor}': Converting downloaded file...")
    if d["status"] == "processing":
        print(f"{time.ctime()}: '{pprocessor}': Conversion in progress...")
    if d["status"] == "finished":  # Guaranteed to call
        print(f"{time.ctime()}: '{pprocessor}': Done converting!")


# ?TODO: Figure out how to get the filename from yt-dlp after download


def download_video(url: str, file_path: str | None = None):
    # Download the video from the given URL to the given path
    if not file_path:
        file_path = "%(title)s.%(ext)s"
    ydl_opts = {
        "format": "bestvideo[height<=?1080]+bestaudio",
        "outtmpl": file_path,
        "compat_opts": {"no-keep-subs"},
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "restrictfilenames": True,
        "merge_output_format": "mkv",
        "ffmpeg_location": "/usr/bin/ffmpeg",
        "postprocessors": [
            {"format": "srt", "key": "FFmpegSubtitlesConvertor", "when": "before_dl"},
            {"already_have_subtitle": False, "key": "FFmpegEmbedSubtitle"},
            {"add_metadata": True, "key": "FFmpegMetadata"},
            {"key": "FFmpegCopyStream"},
        ],
        "subtitleslangs": ["en"],
        "writeautomaticsub": True,
        "writesubtitles": True,
        "postprocessor_args": {
            "copystream": [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "22",
                "-c:a",
                "ac3",
                "-b:a",
                "128k",
                # Below options are for fast straming, but might increase filesize
                "-movflags",
                "+faststart",
                "-tune",
                "zerolatency",
            ],
        },
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    trailer_url = "https://www.youtube.com/watch?v=6ZfuNTqbHE8"
    download_video(trailer_url)
