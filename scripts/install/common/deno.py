"""Download the Deno JavaScript runtime that yt-dlp needs for YouTube.

yt-dlp uses an external JavaScript runtime to solve YouTube's challenges.
Without one, YouTube provides only image formats and every download fails
with 'Requested format is not available'. The Docker image ships Deno;
direct installs get it from this module.
"""

import io
import platform
import shutil
import stat
import zipfile
from pathlib import Path

from common.display import console, print_warning
from common.ffmpeg import _download_with_progress

# Official static builds from the Deno release page. Each zip contains a
# single 'deno' / 'deno.exe' binary.
_DENO_URLS: dict[str, str] = {
    "linux-x86_64": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip",
    "linux-aarch64": "https://github.com/denoland/deno/releases/latest/download/deno-aarch64-unknown-linux-gnu.zip",
    "windows-x86_64": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip",
    "windows-aarch64": "https://github.com/denoland/deno/releases/latest/download/deno-aarch64-pc-windows-msvc.zip",
    "darwin-x86_64": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-apple-darwin.zip",
    "darwin-arm64": "https://github.com/denoland/deno/releases/latest/download/deno-aarch64-apple-darwin.zip",
}


def download_deno(bin_dir: Path) -> Path | None:
    """Download the Deno binary into bin_dir for the current platform.

    Returns the path to the binary, the system copy if one is already on
    PATH and no build is available, or None when Deno cannot be provided.
    A missing Deno does not stop the install — YouTube downloads fail
    without it, so the caller prints a clear warning.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    system = platform.system().lower()
    machine = platform.machine().lower()
    # Normalize arch names to match the URL dict keys (macOS uses arm64,
    # Linux/Windows use aarch64; Windows reports amd64 for x86_64)
    if machine in ("arm64", "aarch64"):
        machine = "arm64" if system == "darwin" else "aarch64"
    if machine == "amd64":
        machine = "x86_64"

    platform_key = f"{system}-{machine}"
    url = _DENO_URLS.get(platform_key)
    exe_suffix = ".exe" if system == "windows" else ""
    deno_dest = bin_dir / f"deno{exe_suffix}"

    if not url:
        deno_in_path = shutil.which("deno")
        if deno_in_path:
            print_warning(
                f"No pre-built Deno for {platform_key}."
                f" Using system Deno: {deno_in_path}"
            )
            return Path(deno_in_path)
        print_warning(
            f"No Deno build available for platform '{platform_key}'."
            " Install Deno manually and set DENO_PATH in your .env —"
            " YouTube downloads fail without a JavaScript runtime."
        )
        return None

    try:
        raw = _download_with_progress(url, "Downloading Deno (zip)")
        with console.status("[step]Copying Deno binary...[/step]"):
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for name in zf.namelist():
                    if Path(name).name in ("deno", "deno.exe"):
                        deno_dest.write_bytes(zf.read(name))
                        break
                else:
                    raise RuntimeError("deno binary not found in archive")
        if system != "windows":
            deno_dest.chmod(
                deno_dest.stat().st_mode
                | stat.S_IEXEC
                | stat.S_IXGRP
                | stat.S_IXOTH
            )
        _verify(deno_dest)
        return deno_dest
    except Exception as exc:
        print_warning(
            f"Could not download Deno: {exc}."
            " Install Deno manually and set DENO_PATH in your .env —"
            " YouTube downloads fail without a JavaScript runtime."
        )
        return None


def _verify(deno: Path) -> None:
    import subprocess

    result = subprocess.run(
        [str(deno), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"deno --version returned non-zero: {result.stderr}"
        )
