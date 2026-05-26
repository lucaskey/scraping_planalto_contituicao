import re


def detectar_titulo(t: str) -> bool:
    return bool(re.match(r'^TÍTULO\s+[IVXLCDM]+', t.strip().upper()))


def detectar_capitulo(t: str) -> bool:
    return bool(re.match(r'^CAPÍTULO\s+[IVXLCDM]+', t.strip().upper()))


def detectar_secao(t: str) -> bool:
    return bool(re.match(r'^SE[CÇ][AÃ]O\s+[IVXLCDM]+(?:-[A-Z])?', t.strip().upper()))


def detectar_subsecao(t: str) -> bool:
    return bool(re.match(r'^SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+', t.strip().upper()))


def detectar_artigo(t: str) -> bool:
    return bool(re.match(r'^Art\.\s*\d+', t.strip(), re.IGNORECASE))


def detectar_paragrafo(t: str) -> bool:
    return bool(
        re.match(
            r'^(§\s*\d+\s*[ºo]?\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)',
            t.strip(),
            re.IGNORECASE,
        )
    )


def detectar_inciso(t: str) -> bool:
    return bool(re.match(r'^[IVXLCDM]+\s*[–\-]\s+', t.strip()))


def detectar_alinea(t: str) -> bool:
    return bool(re.match(r'^\s*([a-z]\s*\))\s*', t.strip()))
