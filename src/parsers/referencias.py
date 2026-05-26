from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from utils.constituicao_utils import get_logger
from parsers.schema import (
    STATUS_REVOGADO,
    STATUS_VIGENTE,
    TIPO_ALTERACAO,
    TIPO_INCLUSAO,
    TIPO_REF_ADI,
    TIPO_REF_ADIN,
    TIPO_REF_ADPF,
    TIPO_REF_DECRETO,
    TIPO_REF_DECRETO_LEI,
    TIPO_REF_EMENDA,
    TIPO_REF_LEI,
    TIPO_REF_MPV,
    TIPO_REF_OUTRO,
    TIPO_REVOGACAO,
    make_modificacoes_historicas,
    make_referencial_legislativo,
)

LOGGER = get_logger(__name__)


def normalizar_numero_documento(numero: str) -> str:
    n = re.sub(r"[^\d]", "", numero or "")
    if not n:
        return ""
    if len(n) <= 3:
        return n
    return f"{n[:-3]}.{n[-3:]}"


def extrair_numero_referencia(texto: str, href: str) -> str:
    t = texto or ""

    m = re.search(r"\bmi\s*(\d+)\b", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.search(
        r"\b(adi|adin|adpf)\b(?:\s*n\s*[ºo°\.]?\s*)?\s*(\d[\d\.]*)\b",
        t,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(2).strip()

    m = re.search(r"\bn[ºo°\.]?\s*([\d\.]+)", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    m = re.search(r"\b(?:lei|decreto|emenda|mpv)\s*n[ºo°\.]?\s*([\d\.]+)", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    h = (href or "").strip()
    m = re.search(r"/L(\d+)\.htm", h, flags=re.IGNORECASE)
    if m:
        return normalizar_numero_documento(m.group(1))

    m = re.search(r"/(?:EC|ECONST|EMENDA)(\d+)\.htm", h, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    return ""


def tipo_de_referencia(texto: str, href: str) -> str:
    h = (href or "").lower()
    t = (texto or "").lower()

    if "stf.jus.br" in h:
        if "adpf" in t:
            return TIPO_REF_ADPF
        if "adin" in t:
            return TIPO_REF_ADIN
        if re.search(r"\badi\b", t):
            return TIPO_REF_ADI
        return TIPO_REF_OUTRO

    if "decreto-lei" in h or "decretolei" in h:
        return TIPO_REF_DECRETO_LEI
    if "/decreto" in h or "decreto" in h:
        return TIPO_REF_DECRETO
    if "/mpv" in h or "mpv" in h:
        return TIPO_REF_MPV
    if "/emenda" in h or "emenda" in h:
        return TIPO_REF_EMENDA
    if "/leis/" in h or "/lei" in h or "lei" in h:
        return TIPO_REF_LEI

    return TIPO_REF_OUTRO


def status_da_referencia(a_tag: Any) -> str:
    if a_tag is None:
        return STATUS_VIGENTE

    texto_link = a_tag.get_text(" ", strip=True) if hasattr(a_tag, "get_text") else ""
    if re.match(r"^\s*revogad[oa]s?\b", texto_link or "", flags=re.IGNORECASE):
        return STATUS_REVOGADO

    try:
        for prev in a_tag.previous_elements:
            if prev is a_tag:
                continue
            if getattr(prev, "name", None) in {"p", "h1", "h2", "h3", "h4", "h5"}:
                break
            if getattr(prev, "name", None) in {"strike", "s", "del"}:
                return STATUS_REVOGADO
            style = (getattr(prev, "attrs", {}) or {}).get("style", "") or ""
            if "line-through" in style.lower():
                return STATUS_REVOGADO
    except Exception as exc:
        LOGGER.debug("Falha ao inspecionar previous_elements para status da referencia: %s", exc)

    return STATUS_VIGENTE


def forcar_status_em_referencias(refs: List[Dict[str, Any]], status: Optional[str]) -> List[Dict[str, Any]]:
    if not refs or not status:
        return refs
    for ref in refs:
        ref["status_da_referencia"] = status
    return refs


def extrair_referenciais_legislativos(elem: Any, status_dispositivo: Optional[str] = None) -> List[Dict[str, Any]]:
    if elem is None:
        return []

    refs: List[Dict[str, Any]] = []
    try:
        a_tags = elem.find_all("a", href=True)
    except Exception as exc:
        LOGGER.debug("Falha ao coletar links em referencial legislativo: %s", exc)
        return []

    for a_tag in a_tags:
        href = (a_tag.get("href") or "").strip()
        texto_link = re.sub(r"\s{2,}", " ", a_tag.get_text(" ", strip=True) or "").strip()
        if not href or not texto_link:
            continue

        numero = extrair_numero_referencia(texto_link, href)
        tipo = tipo_de_referencia(texto_link, href)
        status = status_da_referencia(a_tag)
        if status_dispositivo == STATUS_REVOGADO:
            status = STATUS_REVOGADO

        refs.append(
            make_referencial_legislativo(
                numero=numero,
                tipo=tipo,
                texto=texto_link,
                status=status,
            )
        )

    return forcar_status_em_referencias(refs, status_dispositivo)


def extrair_texto_riscado(elem: Any) -> str:
    if elem is None:
        return ""

    partes: List[str] = []
    try:
        for t in elem.find_all(["strike", "s", "del"]):
            tx = re.sub(r"\s{2,}", " ", t.get_text(" ", strip=True) or "").strip()
            if tx:
                partes.append(tx)
    except Exception as exc:
        LOGGER.debug("Falha ao extrair texto riscado por tags strike/s/del: %s", exc)

    try:
        for t in elem.find_all(True):
            style = (t.attrs or {}).get("style", "") or ""
            if "line-through" not in style.lower():
                continue
            tx = re.sub(r"\s{2,}", " ", t.get_text(" ", strip=True) or "").strip()
            if tx:
                partes.append(tx)
    except Exception as exc:
        LOGGER.debug("Falha ao extrair texto com line-through em estilos: %s", exc)

    vistos = set()
    unicos: List[str] = []
    for parte in partes:
        if parte in vistos:
            continue
        vistos.add(parte)
        unicos.append(parte)

    return " | ".join(unicos).strip()


def tipo_modificacao_por_texto(texto_link: str) -> Optional[str]:
    t = (texto_link or "").strip()
    if not t:
        return None

    t_limpo = re.sub(r"^[\(\[\s]+|[\)\]\s]+$", "", t).strip()
    t_low = t_limpo.lower()

    if "redação dada" in t_low or "redacao dada" in t_low:
        return TIPO_ALTERACAO
    if re.match(r"^(inclu[ií]d[oa])\b", t_limpo, flags=re.IGNORECASE):
        return TIPO_INCLUSAO
    if re.match(r"^(revogad[oa])\b", t_limpo, flags=re.IGNORECASE):
        return TIPO_REVOGACAO
    return None


def extrair_modificacoes_historicas(elem: Any, status_dispositivo: Optional[str] = None) -> List[Dict[str, Any]]:
    if elem is None:
        return []

    mods: List[Dict[str, Any]] = []
    texto_antigo = extrair_texto_riscado(elem)

    try:
        a_tags = elem.find_all("a")
    except Exception as exc:
        LOGGER.debug("Falha ao coletar links para modificacoes historicas: %s", exc)
        return []

    for a_tag in a_tags:
        texto_link = re.sub(r"\s{2,}", " ", a_tag.get_text(" ", strip=True) or "").strip()
        if not texto_link:
            continue

        status_ref = status_da_referencia(a_tag)
        dispositivo_revogado = status_dispositivo == STATUS_REVOGADO

        tipo = tipo_modificacao_por_texto(texto_link)
        if dispositivo_revogado or status_ref == STATUS_REVOGADO:
            tipo = TIPO_REVOGACAO

        if not tipo:
            continue

        status_mod = STATUS_REVOGADO if tipo == TIPO_REVOGACAO else STATUS_VIGENTE

        mods.append(
            make_modificacoes_historicas(
                tipo=tipo,
                descricao=texto_link,
                texto_antigo=texto_antigo,
                status=status_mod,
            )
        )

    return mods
