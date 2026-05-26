from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class Repository(Protocol):
    def save(self, data: Any) -> None:
        ...

    def load(self) -> Any:
        ...


class FileRepository(Repository, Protocol):
    path: Path
