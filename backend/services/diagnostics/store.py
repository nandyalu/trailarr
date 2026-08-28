"""Keep the last Connection Doctor report of every connection on disk.

Reports were in memory only at first. Docker users restart the
container on every image update, and each restart threw the reports
away. Every connection chip then showed "Not checked", and the Health
page asked the user to run the checks again. The app must not
ask the user for data it can keep.

The reports are diagnostics, not user data: a small JSON file in
APP_DATA_DIR holds them. A missing or damaged file is not an error --
the doctor runs again.

NOTE (phase-07 move map): this package moves to `services/diagnostics/`
in the backend reorganization.
"""

import json
import os

from app_logger import ModuleLogger
from config.settings import app_settings
from services.diagnostics.models import DoctorReport

logger = ModuleLogger("DiagnosticsStore")

_FILENAME = "diagnostics-reports.json"


def _path() -> str:
    return os.path.join(app_settings.app_data_dir, _FILENAME)


def load() -> dict[int, DoctorReport]:
    """Read the stored reports. Returns an empty dict when there is none."""
    path = _path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError) as e:
        logger.warning(f"Could not read '{path}': {e}. Starting empty.")
        return {}
    reports: dict[int, DoctorReport] = {}
    for item in raw if isinstance(raw, list) else []:
        try:
            report = DoctorReport.model_validate(item)
        except Exception as e:
            # A report written by an older version can miss fields.
            logger.debug(f"Skipping an unreadable stored report: {e}")
            continue
        reports[report.connection_id] = report
    return reports


def save(reports: dict[int, DoctorReport]) -> None:
    """Write the reports. A failure here must never break a check."""
    path = _path()
    payload = [report.model_dump(mode="json") for report in reports.values()]
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp_path, path)
    except OSError as e:
        logger.warning(f"Could not save the doctor reports to '{path}': {e}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass
