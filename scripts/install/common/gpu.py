"""GPU hardware detection and driver installation instructions."""

import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from common.display import console


@dataclass
class GPUInfo:
    vendor: str  # 'nvidia' | 'intel' | 'amd' | 'apple' | 'unknown'
    name: str
    device_path: str | None = None  # Linux: /dev/dri/renderD128


# Driver instructions shown to the user after detection (not executed).
_DRIVER_INSTRUCTIONS: dict[str, dict[str, str]] = {
    "nvidia": {
        "Ubuntu/Debian": "sudo apt install nvidia-driver-535",
        "Fedora": "sudo dnf install akmod-nvidia",
        "Arch": "sudo pacman -S nvidia",
        "openSUSE": "sudo zypper install nvidia-drivers",
        "Windows": "https://www.nvidia.com/Download/index.aspx  (or GeForce Experience)",
    },
    "intel": {
        "Ubuntu/Debian": "sudo apt install intel-media-va-driver intel-media-va-driver-non-free libva-drm2",
        "Fedora": "sudo dnf install intel-media-driver libva",
        "Arch": "sudo pacman -S intel-media-driver libva",
        "Windows": "https://www.intel.com/content/www/us/en/download-center/home.html",
    },
    "amd": {
        "Ubuntu/Debian": "sudo apt install mesa-va-drivers libva-drm2",
        "Fedora": "sudo dnf install mesa-va-drivers libva",
        "Arch": "sudo pacman -S mesa libva",
        "Windows": "https://www.amd.com/en/support  (AMD Adrenalin Software)",
    },
    "apple": {},  # Metal is built-in; no extra drivers needed
}


def detect_gpus() -> list[GPUInfo]:
    system = platform.system()
    if system == "Linux":
        return _detect_linux()
    elif system == "Darwin":
        return _detect_macos()
    elif system == "Windows":
        return _detect_windows()
    return []


def print_gpu_report(gpus: list[GPUInfo]) -> None:
    """Print a rich panel with detected GPUs and driver installation instructions."""
    if not gpus:
        console.print(
            Panel(
                "[dim]No GPU hardware detected (or detection tools unavailable).\n"
                "CPU-based encoding will be used.",
                title="[bold]GPU Hardware Acceleration[/bold]",
                border_style="dim",
            )
        )
        return

    lines = Text()
    lines.append("Detected GPU(s):\n\n", style="bold")

    for gpu in gpus:
        lines.append(f"  {gpu.name}", style="bold cyan")
        if gpu.device_path:
            lines.append(f"  ({gpu.device_path})", style="dim")
        lines.append("\n")

    vendors_shown: set[str] = set()
    for gpu in gpus:
        if gpu.vendor in vendors_shown or gpu.vendor == "apple":
            continue
        vendors_shown.add(gpu.vendor)
        instructions = _DRIVER_INSTRUCTIONS.get(gpu.vendor, {})
        if not instructions:
            continue

        lines.append(f"\n  To enable {_accel_label(gpu.vendor)}, install drivers:\n", style="bold")
        for distro, cmd in instructions.items():
            lines.append(f"    {distro:<18}", style="dim")
            lines.append(f"{cmd}\n", style="white")

    if "apple" in {g.vendor for g in gpus}:
        lines.append("\n  Metal hardware acceleration is built-in — no drivers needed.\n", style="green")

    lines.append(
        "\nAfter installing drivers, restart Trailarr and enable\n"
        "Hardware Acceleration in [bold]Settings → Video Processing[/bold].",
        style="dim",
    )

    console.print(
        Panel(
            lines,
            title="[bold yellow]GPU Hardware Acceleration[/bold yellow]",
            border_style="yellow",
        )
    )


def _accel_label(vendor: str) -> str:
    return {
        "nvidia": "CUDA/NVENC acceleration",
        "intel": "Intel VAAPI acceleration",
        "amd": "AMD VAAPI acceleration",
    }.get(vendor, f"{vendor} acceleration")


# ---------------------------------------------------------------------------
# Linux detection
# ---------------------------------------------------------------------------

_VENDOR_MAP = {
    "0x10de": "nvidia",
    "0x8086": "intel",
    "0x1002": "amd",
    "0x1022": "amd",
}


def _detect_linux() -> list[GPUInfo]:
    gpus: list[GPUInfo] = []
    dri = Path("/dev/dri")
    if not dri.exists():
        return gpus

    for device in sorted(dri.glob("renderD*")):
        try:
            result = subprocess.run(
                ["udevadm", "info", "--query=path", f"--name={device}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                continue
            syspath = Path("/sys" + result.stdout.strip()) / "device"
            vendor_file = syspath / "vendor"
            if not vendor_file.exists():
                continue
            vendor_id = vendor_file.read_text().strip().lower()
            vendor = _VENDOR_MAP.get(vendor_id, "unknown")
            if vendor == "unknown":
                continue
            name = _linux_gpu_name(vendor, device)
            gpus.append(GPUInfo(vendor=vendor, name=name, device_path=str(device)))
        except Exception:
            continue

    return gpus


def _linux_gpu_name(vendor: str, device: Path) -> str:
    if vendor == "nvidia":
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            name = r.stdout.strip().splitlines()[0]
            if name:
                return name
        except Exception:
            pass
        return "NVIDIA GPU"

    # For Intel/AMD, try lspci
    try:
        r = subprocess.run(
            ["lspci", "-mm"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in r.stdout.splitlines():
            lower = line.lower()
            if vendor == "intel" and "intel" in lower and ("vga" in lower or "display" in lower or "3d" in lower):
                parts = line.split('"')
                if len(parts) >= 4:
                    return parts[3]
            if vendor == "amd" and ("amd" in lower or "radeon" in lower or "ati" in lower) and (
                "vga" in lower or "display" in lower or "3d" in lower
            ):
                parts = line.split('"')
                if len(parts) >= 4:
                    return parts[3]
    except Exception:
        pass

    return {"intel": "Intel GPU", "amd": "AMD GPU"}.get(vendor, "Unknown GPU")


# ---------------------------------------------------------------------------
# macOS detection
# ---------------------------------------------------------------------------


def _detect_macos() -> list[GPUInfo]:
    try:
        r = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(r.stdout)
        gpus = []
        for display in data.get("SPDisplaysDataType", []):
            name: str = display.get("sppci_model", "") or display.get("_name", "Unknown GPU")
            lower = name.lower()
            vendor = (
                "apple"
                if "apple" in lower
                else "nvidia"
                if "nvidia" in lower
                else "amd"
                if ("amd" in lower or "radeon" in lower)
                else "intel"
                if "intel" in lower
                else "unknown"
            )
            gpus.append(GPUInfo(vendor=vendor, name=name))
        return gpus
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Windows detection
# ---------------------------------------------------------------------------


def _detect_windows() -> list[GPUInfo]:
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-WmiObject Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = r.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        gpus = []
        for entry in data:
            name: str = entry.get("Name", "") or "Unknown GPU"
            lower = name.lower()
            vendor = (
                "nvidia"
                if "nvidia" in lower
                else "amd"
                if ("amd" in lower or "radeon" in lower)
                else "intel"
                if "intel" in lower
                else "unknown"
            )
            gpus.append(GPUInfo(vendor=vendor, name=name))
        return gpus
    except Exception:
        return []
