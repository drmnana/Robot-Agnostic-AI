import json
from pathlib import Path

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = REPO_ROOT / "docs" / "openapi.json"


def main() -> None:
    OPENAPI_PATH.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OPENAPI_PATH}")


if __name__ == "__main__":
    main()
