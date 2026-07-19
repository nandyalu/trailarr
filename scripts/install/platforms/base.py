"""Abstract base class shared by all platform installers."""

import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from common.config import ask_port, write_initial_config
from common.display import print_info, print_success, step_context
from common.env_file import load_env
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
        # Read any existing config before touching files, and stop a running
        # service so it doesn't hold the app port during re-install/upgrade.
        existing_env = load_env(self.env_path)
        self.stop_existing_service()
        self.create_dirs()
        self.copy_files()
        self.setup_python()
        self.download_ffmpeg_binary()
        port = self._resolve_port(existing_env)
        self.write_config(port)
        self.create_service(port)
        self.install_cli()
        self.detect_and_report_gpu()

    def _resolve_port(self, existing_env: dict[str, str]) -> int:
        """Keep the port from a previous install so bookmarks keep working."""
        existing = existing_env.get("APP_PORT", "")
        if existing.isdigit() and 0 < int(existing) <= 65535:
            print_info(f"Reusing configured port {existing}")
            return int(existing)
        return ask_port()

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

            # Install a managed Python inside the install dir so the account
            # the service runs as owns/reads the stdlib. Without this, uv
            # reuses the installing user's ~/.local/share/uv/python (root's,
            # on Linux/macOS), which the service account cannot read —
            # "Failed to import encodings" at service start.
            uv_python_dir = self.backend_dir / ".uv-python"
            uv_python_dir.mkdir(parents=True, exist_ok=True)

            # Clear VIRTUAL_ENV to avoid conflicts with the outer `uv run`
            # environment the installer itself executes in.
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT")
            }
            env["UV_PYTHON_INSTALL_DIR"] = str(uv_python_dir)

            subprocess.run(
                [uv, "python", "install", "cpython-3.13"],
                capture_output=True,
                text=True,
                env=env,
            )

            python_bin = self._find_managed_python(uv_python_dir)
            if not python_bin:
                raise RuntimeError(f"Python 3.13 not found in {uv_python_dir} after install")

            result = subprocess.run(
                [uv, "sync", "--no-cache", "--python", str(python_bin)],
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode != 0:
                raise RuntimeError(f"uv sync failed:\n{result.stderr}")

    @staticmethod
    def _find_managed_python(uv_python_dir: Path) -> Path | None:
        if sys.platform == "win32":
            bins = sorted(uv_python_dir.glob("cpython-3.13*/python.exe"))
            return bins[0] if bins else None
        bins = sorted(uv_python_dir.glob("cpython-3.13*/bin/python3*"))
        return next(
            (p for p in bins if not p.name.endswith(("-config", ".1"))),
            None,
        )

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
    def stop_existing_service(self) -> None:
        """Stop a service left over from a previous install (no-op if absent)."""

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
