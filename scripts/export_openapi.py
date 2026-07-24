from __future__ import annotations

import json
from pathlib import Path

from clientatlas_ai.main import app

output = Path("packages/contracts/openapi/ai-service.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(output)
