import json
from pathlib import Path

from main import trailarr_api

print("Exporting OpenAPI documentation...")
repo_path = Path(__file__).parent.parent
OUTPUT_JSON = repo_path / "docs" / "references" / "api-docs" / "openapi.json"
OUTPUT_JSON.write_text(json.dumps(trailarr_api.openapi(), indent=None))
print(f"OpenAPI documentation exported to {OUTPUT_JSON}")
