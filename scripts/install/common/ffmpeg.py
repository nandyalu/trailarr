"""Download platform-specific ffmpeg static binaries from yt-dlp/FFmpeg-Builds."""

import io
import platform
import shutil
import stat
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from common.display import console, make_download_progress, print_success, print_warning

# yt-dlp/FFmpeg-Builds provides static GPL binaries for Linux and Windows.
# macOS binaries come from evermeet.cx (John Van Sickle style static builds).
_FFMPEG_URLS: dict[str, str] = {
    "linux-x86_64": "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
    "linux-aarch64": "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
    "windows-x86_64": "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "windows-aarch64": "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-winarm64-gpl.zip",
    "darwin-x86_64": "https://evermeet.cx/ffmpeg/get/ffmpeg/zip",
    "darwin-arm64": "https://evermeet.cx/ffmpeg/get/ffmpeg/zip",
}
_FFPROBE_URLS: dict[str, str] = {
    "darwin-x86_64": "https://evermeet.cx/ffmpeg/get/ffprobe/zip",
    "darwin-arm64": "https://evermeet.cx/ffmpeg/get/ffprobe/zip",
}


def download_ffmpeg(bin_dir: Path) -> tuple[Path, Path]:
    """
    Download ffmpeg and ffprobe into bin_dir for the current platform.
    Returns (ffmpeg_path, ffprobe_path).
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    machine = platform.machine().lower()
    # Normalize arm64/aarch64
    if machine in ("arm64", "aarch64"):
        machine = "aarch64"

    # Windows reports "amd64"; normalize to match the URL dict keys
    if machine == "amd64":
        machine = "x86_64"

    platform_key = f"{system}-{machine}"
    url = _FFMPEG_URLS.get(platform_key)

    if not url:
        # Fallback: check if ffmpeg is already in PATH
        ffmpeg_in_path = shutil.which("ffmpeg")
        ffprobe_in_path = shutil.which("ffprobe")
        if ffmpeg_in_path and ffprobe_in_path:
            print_warning(f"No pre-built ffmpeg for {platform_key}. Using system ffmpeg: {ffmpeg_in_path}")
            return Path(ffmpeg_in_path), Path(ffprobe_in_path)
        raise RuntimeError(
            f"No ffmpeg build available for platform '{platform_key}'. "
            "Please install ffmpeg manually and set FFMPEG_PATH / FFPROBE_PATH in your .env."
        )

    exe_suffix = ".exe" if system == "windows" else ""
    ffmpeg_dest = bin_dir / f"ffmpeg{exe_suffix}"
    ffprobe_dest = bin_dir / f"ffprobe{exe_suffix}"

    if system == "darwin":
        _download_macos_ffmpeg(platform_key, bin_dir, ffmpeg_dest, ffprobe_dest)
    elif url.endswith(".tar.xz"):
        _download_tarxz(url, bin_dir, ffmpeg_dest, ffprobe_dest)
    elif url.endswith(".zip"):
        _download_zip(url, bin_dir, ffmpeg_dest, ffprobe_dest)

    # Make executable on Unix
    if system != "windows":
        for p in (ffmpeg_dest, ffprobe_dest):
            p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    _verify(ffmpeg_dest, ffprobe_dest)
    print_success(f"ffmpeg installed to {bin_dir}")
    return ffmpeg_dest, ffprobe_dest


def _download_with_progress(url: str, description: str) -> bytes:
    data = io.BytesIO()
    with make_download_progress() as progress:
        task = progress.add_task(description, total=None)

        def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
            if total_size > 0:
                progress.update(task, total=total_size, completed=block_num * block_size)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        urllib.request.urlretrieve(url, tmp_path, reporthook=_reporthook)  # noqa: S310
        data = tmp_path.read_bytes()
        tmp_path.unlink(missing_ok=True)
    return data


def _download_tarxz(url: str, bin_dir: Path, ffmpeg_dest: Path, ffprobe_dest: Path) -> None:
    raw = _download_with_progress(url, "Downloading ffmpeg (tar.xz)")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:xz") as tf:
        for member in tf.getmembers():
            name = Path(member.name).name
            if name in ("ffmpeg", "ffprobe"):
                dest = ffmpeg_dest if name == "ffmpeg" else ffprobe_dest
                extracted = tf.extractfile(member)
                if extracted:
                    dest.write_bytes(extracted.read())


def _download_zip(url: str, bin_dir: Path, ffmpeg_dest: Path, ffprobe_dest: Path) -> None:
    raw = _download_with_progress(url, "Downloading ffmpeg (zip)")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for info in zf.infolist():
            name = Path(info.filename).name
            if name in ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"):
                dest = ffmpeg_dest if "ffmpeg" in name else ffprobe_dest
                dest.write_bytes(zf.read(info.filename))


def _download_macos_ffmpeg(
    platform_key: str, bin_dir: Path, ffmpeg_dest: Path, ffprobe_dest: Path
) -> None:
    for tool, dest in [("ffmpeg", ffmpeg_dest), ("ffprobe", ffprobe_dest)]:
        url = _FFPROBE_URLS.get(platform_key) if tool == "ffprobe" else _FFMPEG_URLS.get(platform_key)
        if not url:
            continue
        raw = _download_with_progress(url, f"Downloading {tool} (macOS)")
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for name in zf.namelist():
                if Path(name).name == tool:
                    dest.write_bytes(zf.read(name))
                    break


def _verify(ffmpeg: Path, ffprobe: Path) -> None:
    import subprocess

    for binary in (ffmpeg, ffprobe):
        if not binary.exists():
            raise RuntimeError(f"Expected binary not found after download: {binary}")
        try:
            result = subprocess.run(
                [str(binary), "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(f"{binary.name} -version returned non-zero: {result.stderr}")
        except FileNotFoundError as e:
            raise RuntimeError(f"Cannot execute {binary}: {e}") from e
