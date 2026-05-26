from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def normalize_whitespace(text: str) -> str:
    cleaned = re.sub(r"[\r\n\t]+", " ", text or "").strip()
    return re.sub(r"\s{2,}", " ", cleaned)


def sanitize_text_for_json(text: str) -> str:
    sanitized = (text or "").replace('"', "")
    return sanitized.replace("â€œ", "").replace("â€", "")


def split_num_nome(text: str, pattern: str) -> tuple[str, str]:
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if not match:
        return text.strip(), ""

    numero = match.group(1).strip()
    descricao = text.strip()[len(match.group(0)) :].strip()
    descricao = re.sub(r"^[-â€“:\s]+", "", descricao)
    return numero, descricao


def dump_json(data: Any, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
