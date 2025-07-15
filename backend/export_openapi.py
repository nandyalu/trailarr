import json
from pathlib import Path

import yaml

from main import trailarr_api

print("Exporting OpenAPI documentation...")
# Save JSON to "/app/docs/references/api-docs/openapi.json"
OUTPUT_JSON = Path("/app/docs/references/api-docs") / "openapi.json"
OUTPUT_JSON.write_text(json.dumps(trailarr_api.openapi(), indent=None))

print(f"OpenAPI documentation exported to {OUTPUT_JSON}")


class MyDumper(yaml.Dumper):
    """Helper class to format YAML output."""

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


# Save YAML to "/app/frontend/contract/swagger.yaml"
OUTPUT_JSON = Path("/app/frontend/contract") / "swagger.yaml"
yaml.dump(
    trailarr_api.openapi(),
    open(OUTPUT_JSON, "w"),
    Dumper=MyDumper,
    sort_keys=False,
    allow_unicode=True,
    default_flow_style=False,
)
print(f"OpenAPI documentation exported to {OUTPUT_JSON}")
