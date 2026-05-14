"""Abstract base class shared by all platform installers."""

import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from common.config import ask_port, write_initial_config
from common.display import console, print_info, print_section, print_step, print_success, step_context
from common.ffmpeg import download_ffmpeg
from common.gpu import detect_gpus, print_gpu_report


class BaseInstaller(ABC):
    def __init__(
        self,
        source_dir: Path,
        install_dir: Path,
        data_dir: Path,
        log_dir: Path,
        version: str,
    ) -> None:
        self.source_dir = source_dir
        self.install_dir = install_dir
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.version = version
        self.bin_dir = install_dir / "bin"
        self.backend_dir = install_dir / "backend"
        self.venv_dir = self.backend_dir / ".venv"
        self.env_path = data_dir / ".env"
        # Set by download_ffmpeg_binary(); used by write_config()
        self.ffmpeg_path: Path = self.bin_dir / "ffmpeg"
        self.ffprobe_path: Path = self.bin_dir / "ffprobe"

    # ------------------------------------------------------------------
    # Main flow
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.check_prerequisites()
        self.create_dirs()
        self.copy_files()
        self.setup_python()
        self.download_ffmpeg_binary()
        port = ask_port()
        self.write_config(port)
        self.create_service(port)
        self.install_cli()
        self.detect_and_report_gpu()

    # ------------------------------------------------------------------
    # Shared implementations
    # ------------------------------------------------------------------

    def copy_files(self) -> None:
        with step_context("Copying application files"):
            for name in ("backend", "frontend-build", "assets", "scripts"):
                src = self.source_dir / name
                dst = self.install_dir / name
                if src.exists():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)

    def setup_python(self) -> None:
        with step_context("Setting up Python environment (uv sync)"):
            uv = shutil.which("uv")
            if not uv:
                raise RuntimeError("uv not found in PATH. Please install uv first: https://docs.astral.sh/uv/")
            result = subprocess.run(
                [uv, "sync", "--no-cache-dir"],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"uv sync failed:\n{result.stderr}")

    def download_ffmpeg_binary(self) -> None:
        self.ffmpeg_path, self.ffprobe_path = download_ffmpeg(self.bin_dir)
        print_success("ffmpeg downloaded")
        print_info(f"ffmpeg installed to {self.bin_dir}")

    def write_config(self, port: int) -> None:
        venv_bin = self.venv_dir / "Scripts" if sys.platform == "win32" else self.venv_dir / "bin"
        ytdlp_name = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
        python_name = "python.exe" if sys.platform == "win32" else "python"

        write_initial_config(
            self.env_path,
            version=self.version,
            install_dir=self.install_dir,
            data_dir=self.data_dir,
            port=port,
            ffmpeg_path=self.ffmpeg_path,
            ffprobe_path=self.ffprobe_path,
            ytdlp_path=venv_bin / ytdlp_name,
            python_executable=venv_bin / python_name,
        )

    def detect_and_report_gpu(self) -> None:
        gpus = detect_gpus()
        print_gpu_report(gpus)

    # ------------------------------------------------------------------
    # Abstract (platform-specific)
    # ------------------------------------------------------------------

    @abstractmethod
    def check_prerequisites(self) -> None: ...

    @abstractmethod
    def create_dirs(self) -> None: ...

    @abstractmethod
    def create_service(self, port: int) -> None: ...

    @abstractmethod
    def install_cli(self) -> None: ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _python_exec(self) -> Path:
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def _run(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, check=True, **kwargs)
