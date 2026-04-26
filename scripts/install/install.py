"""
Trailarr cross-platform installer.

Run via the bootstrap scripts (install.sh / install.ps1):
  uv run --python 3.13 --with rich scripts/install/install.py \
      --source-dir /tmp/trailarr-v1.0.0 --version v1.0.0
"""

import argparse
import platform
import sys
import traceback
from pathlib import Path

# Ensure sibling packages (common/, platforms/) are importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

from common.display import console, print_banner, print_error  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trailarr installer")
    parser.add_argument("--source-dir", required=True, type=Path, help="Path to extracted release archive")
    parser.add_argument("--version", required=True, help="Release version string (e.g. v1.2.3)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir: Path = args.source_dir.resolve()
    version: str = args.version

    print_banner(version)

    if not source_dir.exists():
        print_error(f"Source directory not found: {source_dir}")
        sys.exit(1)

    os_name = platform.system()

    try:
        if os_name == "Linux":
            from platforms.linux import LinuxInstaller
            installer = LinuxInstaller(source_dir=source_dir, version=version)

        elif os_name == "Darwin":
            from platforms.macos import MacOSInstaller
            installer = MacOSInstaller(source_dir=source_dir, version=version)

        elif os_name == "Windows":
            from platforms.windows import WindowsInstaller
            installer = WindowsInstaller(source_dir=source_dir, version=version)

        else:
            print_error(f"Unsupported operating system: {os_name}")
            console.print(
                "[dim]Trailarr direct installation supports Linux, macOS, and Windows.\n"
                "For other systems, use the Docker image: https://hub.docker.com/r/nandyalu/trailarr[/dim]"
            )
            sys.exit(1)

        installer.run()

        from common.display import print_completion
        install_dir = str(installer.install_dir)
        data_dir = str(installer.data_dir)
        from common.env_file import load_env
        env = load_env(installer.env_path)
        port = int(env.get("APP_PORT", "7889"))
        print_completion(install_dir, data_dir, port, os_name)

    except RuntimeError as exc:
        print_error(str(exc))
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled.[/yellow]")
        sys.exit(1)
    except Exception:
        print_error("An unexpected error occurred:")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
