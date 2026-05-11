import json
import os
import tempfile
from pathlib import Path

# Must be set before importing main — app_settings and ModuleLogger read it at import time
_tmp = tempfile.mkdtemp(prefix="trailarr-openapi-")
(Path(_tmp) / "logs").mkdir()
os.environ.setdefault("APP_DATA_DIR", _tmp)

from main import trailarr_api  # noqa: E402

print("Exporting OpenAPI documentation...")
repo_path = Path(__file__).parent.parent
OUTPUT_JSON = repo_path / "docs" / "references" / "api-docs" / "openapi.json"
OUTPUT_JSON.write_text(json.dumps(trailarr_api.openapi(), indent=None))
print(f"OpenAPI documentation exported to {OUTPUT_JSON}")
