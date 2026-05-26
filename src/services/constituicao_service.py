from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Dict

from repositories.json_repository import JsonRepository


@dataclass(slots=True)
class ConstituicaoPipelineDeps:
    create_driver: Callable[[bool], Any]
    load_page: Callable[[Any, str], str]
    parse_html: Callable[[str], List[Dict[str, Any]]]


class ConstituicaoService:
    def __init__(
        self,
        base_url: str,
        output_path: Path,
        deps: ConstituicaoPipelineDeps,
    ) -> None:
        self.base_url = base_url
        self.output_repo = JsonRepository(output_path)
        self.deps = deps

    def run(self, headless: bool = True) -> List[Dict[str, Any]]:
        driver = self.deps.create_driver(headless)
        try:
            html = self.deps.load_page(driver, self.base_url)
            data = self.deps.parse_html(html)
            self.output_repo.save(data)
            return data
        finally:
            driver.quit()
