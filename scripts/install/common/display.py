"""Rich-based terminal display helpers for the Trailarr installer."""

from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.theme import Theme
from rich.text import Text

_theme = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
        "step": "bold blue",
        "dim": "dim white",
    }
)

console = Console(theme=_theme)

BANNER = r"""
 _____ ____      _    ___ _        _    ____  ____
|_   _|  _ \    / \  |_ _| |      / \  |  _ \|  _ \
  | | | |_) |  / _ \  | || |     / _ \ | |_) | |_) |
  | | |  _ <  / ___ \ | || |___ / ___ \|  _ <|  _ <
  |_| |_| \_\/_/   \_\___|_____/_/   \_\_| \_\_| \_\
"""


def print_banner(version: str) -> None:
    import platform
    os_name = platform.system() or "Unknown"
    console.print(
        Panel(
            f"[bold]Version:[/bold]  {version}\n"
            f"[bold]Platform:[/bold] {os_name}",
            style="blue",
            expand=False,
        )
    )
    console.print()


def print_step(message: str) -> None:
    console.print(f"[step]  →  {message}[/step]")


def print_success(message: str) -> None:
    console.print(f"[success]  ✓  {message}[/success]")


def print_warning(message: str) -> None:
    console.print(f"[warning]  ⚠  {message}[/warning]")


def print_error(message: str) -> None:
    console.print(f"[error]  ✗  {message}[/error]")


def print_info(message: str) -> None:
    console.print(f"[info]     {message}[/info]")


def print_section(title: str) -> None:
    console.rule(f"[bold]{title}[/bold]")


def make_download_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )


@contextmanager
def step_context(description: str):
    """Context manager that shows a spinner while work is done, then ✓ on success."""
    with console.status(f"[step]{description}...[/step]"):
        yield
    print_success(description)


def print_completion(install_dir: str, data_dir: str, port: int, os_name: str) -> None:
    instructions: dict[str, str] = {
        "Linux": "sudo systemctl status trailarr",
        "Darwin": "launchctl list com.trailarr.app",
        "Windows": "Get-ScheduledTask -TaskName Trailarr",
    }
    status_cmd = instructions.get(os_name, "trailarr status")

    console.print()
    console.print(
        Panel(
            Text.assemble(
                ("🎉 Trailarr installed successfully!\n\n", "bold green"),
                ("  Install dir:   ", "dim"),
                (f"{install_dir}\n", "white"),
                ("  Data dir:      ", "dim"),
                (f"{data_dir}\n", "white"),
                ("  Web interface: ", "dim"),
                (f"http://localhost:{port}\n\n", "bold cyan"),
                ("CLI commands:\n", "dim"),
                ("  trailarr run       ", "white"), ("— Start Trailarr\n", "dim"),
                ("  trailarr stop      ", "white"), ("— Stop Trailarr\n", "dim"),
                ("  trailarr restart   ", "white"), ("— Restart Trailarr\n", "dim"),
                ("  trailarr status    ", "white"), ("— Show service status\n", "dim"),
                ("  trailarr logs      ", "white"), ("— View logs\n", "dim"),
                ("  trailarr update    ", "white"), ("— Update to latest version\n", "dim"),
                ("  trailarr uninstall ", "white"), ("— Remove Trailarr\n", "dim"),
                ("  run, stop, restart, update, uninstall require " + ("Run as Administrator" if os_name == "Windows" else "sudo") + "\n\n", "dim italic"),
                ("  (open a new terminal if 'trailarr' is not found)\n\n", "dim"),
                ("Documentation:\n", "dim"),
                ("  https://github.com/nandyalu/trailarr", "cyan"),
            ),
            title="[bold green]Installation Complete[/bold green]",
            border_style="green",
        )
    )
