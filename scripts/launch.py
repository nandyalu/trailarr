#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
CONFIG_DIR = PROJECT_ROOT / "config-dev"
LOGS_DIR = CONFIG_DIR / "logs"
BACKUPS_DIR = CONFIG_DIR / "backups"

CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

env = os.environ.copy()
env["APP_DATA_DIR"] = str(CONFIG_DIR)
env["PYTHONPATH"] = str(BACKEND_DIR)

# --- Database backup ---
OLD_DB = CONFIG_DIR / "trailarr.db"
backup_path: Path | None = None

if OLD_DB.exists():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = BACKUPS_DIR / f"trailarr_{timestamp}.db"
    shutil.copy2(OLD_DB, backup_path)
    print(f"Database backup created: {backup_path.name}")

    # Keep only the 30 most recent backups
    backups = sorted(
        BACKUPS_DIR.glob("trailarr_*.db"), key=lambda p: p.name, reverse=True
    )
    to_delete = backups[30:]
    if to_delete:
        for old in to_delete:
            old.unlink()
        print(f"{len(to_delete)} old backup(s) deleted.")
    else:
        print(f"Backup count: {len(backups)}, no old backups deleted.")
else:
    print("No existing database found, skipping backup.")

# --- Database migrations ---
print("Running database migrations...")
result = subprocess.run(
    ["uv", "run", "alembic", "upgrade", "head"],
    cwd=BACKEND_DIR,
    env=env,
)
if result.returncode != 0:
    print("Database migrations failed!", file=sys.stderr)
    if backup_path and backup_path.exists():
        shutil.copy2(backup_path, OLD_DB)
        print(f"Database restored from backup: {backup_path.name}")
    sys.exit(1)
print("Database migrations ran successfully!")

# --- Start application ---
print("Starting Trailarr application...")
os.chdir(BACKEND_DIR)
os.execvpe(
    "uv",
    [
        "uv",
        "run",
        "uvicorn",
        "main:trailarr_api",
        "--host",
        "0.0.0.0",
        "--port",
        "7890",
    ],
    env,
)
