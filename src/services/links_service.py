from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

from repositories.json_repository import JsonRepository
from utils.constituicao_utils import get_logger


LOGGER = get_logger(__name__)


@dataclass(slots=True)
class LinksPipelineDeps:
    extract_links: Callable[[], List[Any]]
    is_planalto_ccivil: Callable[[str], bool]
    scrape_link: Callable[[str], Dict[str, Any]]
    should_rescrape: Callable[[Dict[str, Any]], bool]


class LinksService:
    def __init__(self, output_path: Path, deps: LinksPipelineDeps) -> None:
        self.output_repo = JsonRepository(output_path)
        self.deps = deps

    def run(self) -> List[Dict[str, Any]]:
        links = self.deps.extract_links()

        existing_by_url: Dict[str, Dict[str, Any]] = {}
        existing = self.output_repo.load()
        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict) and isinstance(item.get("url"), str):
                    existing_by_url[item["url"]] = item

        output: List[Dict[str, Any]] = []
        for link in links:
            item: Dict[str, Any] = {
                "texto": link.texto,
                "url": link.url,
                "tipo": "planalto_ccivil" if self.deps.is_planalto_ccivil(link.url) else "externo",
            }

            previous = existing_by_url.get(link.url)
            if isinstance(previous, dict):
                item.update(previous)
                item["texto"] = link.texto
                item["tipo"] = "planalto_ccivil" if self.deps.is_planalto_ccivil(link.url) else "externo"

            if self.deps.is_planalto_ccivil(link.url):
                if item.get("sucesso") is True and isinstance(item.get("dados"), dict):
                    if self.deps.should_rescrape(item):
                        item["sucesso"] = False
                        item.pop("erro", None)
                else:
                    try:
                        item["dados"] = self.deps.scrape_link(link.url)
                        item["sucesso"] = True
                    except Exception as exc:
                        item["sucesso"] = False
                        item["erro"] = str(exc)

            output.append(item)
            try:
                self.output_repo.save(output)
            except Exception as exc:
                # Mantém o comportamento legado: falha de escrita incremental
                # não deve abortar o scraping completo.
                LOGGER.warning("Falha ao salvar progresso incremental de links: %s", exc)

        self.output_repo.save(output)
        return output
