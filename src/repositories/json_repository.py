from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.constituicao_utils import dump_json


class JsonRepository:
    def __init__(self, path: Path) -> None:
        self.path = Path(path).resolve()

    def save(self, data: Any) -> None:
        dump_json(data, self.path)

    def load(self) -> Any:
        if not self.path.exists():
            return None
        with open(self.path, "r", encoding="utf-8") as file:
            import json

            return json.load(file)
