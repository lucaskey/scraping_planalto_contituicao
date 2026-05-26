from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from utils.constituicao_utils import dump_json, get_logger, normalize_whitespace, split_num_nome
from parsers.schema import (
    EstadoParser,
    make_alinea,
    make_artigo,
    make_capitulo,
    make_inciso,
    make_paragrafo,
    make_secao,
    make_subsecao,
    make_titulo,
)
from parsers.detectores import (
    detectar_titulo,
    detectar_capitulo,
    detectar_secao,
    detectar_subsecao,
    detectar_artigo,
    detectar_paragrafo,
    detectar_inciso,
    detectar_alinea,
)
from services.links_service import LinksPipelineDeps, LinksService


BASE_URL = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
OUTPUT_DIR = Path("output_constituicao")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "dado_links.json"
LOGGER = get_logger(__name__)


DEFAULT_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.6,en;q=0.5",
}

SESSION = requests.Session()
SESSION.headers.update(DEFAULT_HEADERS)


@dataclass(frozen=True)
class LinkInfo:
    texto: str
    url: str


def _normalizar_texto(s: str) -> str:
    s = normalize_whitespace(s)
    s = re.sub(r"(\d)\ufffd\b", r"\1Âº", s)
    return s


def _is_planaltoccivil(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception as exc:
        LOGGER.debug("Falha ao parsear URL '%s': %s", url, exc)
        return False
    if p.scheme not in {"http", "https"}:
        return False
    host = (p.netloc or "").lower()
    if host != "www.planalto.gov.br" and not host.endswith("planalto.gov.br"):
        return False
    return p.path.startswith("/ccivil_03/")


def baixar_html(url: str, timeout_s: int = 45) -> str:
    last_err: Exception | None = None
    for attempt in range(1, 6):
        try:
            resp = SESSION.get(url, timeout=timeout_s)
            if resp.status_code in {429, 503}:
                raise requests.HTTPError(f"{resp.status_code} for {url}", response=resp)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return resp.text
        except Exception as e:
            last_err = e
            LOGGER.warning("Tentativa %s falhou: %s - %s", attempt, e, url)
            if attempt >= 5:
                break
            time.sleep(min(2**attempt, 20))
    assert last_err is not None
    raise last_err


def extrair_links_constituicao(url: str = BASE_URL) -> list[LinkInfo]:
    try:
        html = baixar_html(url)
    except Exception as exc:
        LOGGER.warning("Falha ao baixar HTML principal (%s): %s", url, exc)
        # fallback: reaproveita o arquivo jÃ¡ existente (Ãºtil se o Planalto estiver com 503/429)
        if OUTPUT_JSON.exists():
            try:
                with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                    existentes = json.load(f)
                if isinstance(existentes, list):
                    out: list[LinkInfo] = []
                    for it in existentes:
                        if not isinstance(it, dict):
                            continue
                        u = it.get("url")
                        if isinstance(u, str) and u:
                            out.append(LinkInfo(texto=_normalizar_texto(str(it.get("texto", ""))), url=u))
                    if out:
                        return out
            except Exception as fallback_exc:
                LOGGER.warning("Falha ao ler fallback em %s: %s", OUTPUT_JSON, fallback_exc)
        raise
    soup = BeautifulSoup(html, "html.parser")
    links: list[LinkInfo] = []
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        abs_url = urljoin(url, href)
        texto = _normalizar_texto(a.get_text(" ", strip=True))
        links.append(LinkInfo(texto=texto, url=abs_url))

    seen: set[str] = set()
    out: list[LinkInfo] = []
    for li in links:
        if li.url in seen:
            continue
        seen.add(li.url)
        out.append(li)
    return out


def _elementos_textuais(soup: BeautifulSoup) -> list[str]:
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    body = soup.find("body")
    if not body:
        LOGGER.warning("Body nao encontrado.")
        return []

    elems = body.find_all(["p", "h1", "h2", "h3", "h4", "h5", "li"])
    textos: list[str] = []
    for e in elems:
        t = _normalizar_texto(e.get_text(" ", strip=True))
        if not t or len(t) < 2:
            continue
        textos.append(t)
    return textos


def _parsear_documento_planalto(html: str) -> list[dict[str, Any]]:
    """
    Parser estruturado (Planato/ccivil_03) para gerar uma Ã¡rvore parecida com a da ConstituiÃ§Ã£o:
    TÃ­tulo -> CapÃ­tulo -> SeÃ§Ã£o -> SubseÃ§Ã£o -> Artigo -> ParÃ¡grafo -> Inciso -> AlÃ­nea.
    """
    soup = BeautifulSoup(html, "lxml")
    textos = _elementos_textuais(soup)
    estado = EstadoParser()
    titulos: list[dict[str, Any]] = []

    aguardando_desc_titulo = False
    aguardando_desc_capitulo = False
    aguardando_desc_secao = False
    aguardando_desc_subsecao = False

    for texto in textos:
        if aguardando_desc_titulo:
            aguardando_desc_titulo = False
            if estado.titulo_dict is not None:
                estado.titulo_dict["descricao_do_titulo"] = texto.upper()
            continue

        if aguardando_desc_capitulo:
            aguardando_desc_capitulo = False
            if estado.capitulo_dict is not None:
                estado.capitulo_dict["descricao_do_capitulo"] = texto.upper()
            continue

        if aguardando_desc_secao:
            aguardando_desc_secao = False
            if estado.secao_dict is not None:
                estado.secao_dict["descricao_da_secao"] = texto.upper()
            continue

        if aguardando_desc_subsecao:
            aguardando_desc_subsecao = False
            if estado.subsecao_dict is not None:
                estado.subsecao_dict["descricao_da_subsecao"] = texto.upper()
            continue

        # TÃ­tulo
        if detectar_titulo(texto):
            titulo_fechado = estado.fechar_titulo()
            if titulo_fechado:
                titulos.append(titulo_fechado)

            num, desc = split_num_nome(texto, r"^(TÃTULO\s+[IVXLCDM]+)(.*)")
            novo_titulo = make_titulo(titulo=num, descricao=desc)
            estado.abrir_titulo(novo_titulo)
            if not desc.strip():
                aguardando_desc_titulo = True
            continue

        # CapÃ­tulo
        if detectar_capitulo(texto):
            num, desc = split_num_nome(texto, r"^(CAPÃTULO\s+[IVXLCDM]+)(.*)")
            if estado.titulo_dict is None:
                estado.abrir_titulo(make_titulo(titulo="", descricao=""))
            estado.abrir_capitulo(make_capitulo(capitulo=num, descricao=desc))
            if not desc.strip():
                aguardando_desc_capitulo = True
            continue

        # SeÃ§Ã£o
        if detectar_secao(texto):
            num, desc = split_num_nome(texto, r"^(SE[CÃ‡][AÃƒ]O\s+[IVXLCDM]+)(.*)")
            if estado.capitulo_dict is None:
                if estado.titulo_dict is None:
                    estado.abrir_titulo(make_titulo(titulo="", descricao=""))
                estado.abrir_capitulo(make_capitulo(capitulo="", descricao=""))
            estado.abrir_secao(make_secao(secao=num, descricao=desc))
            if not desc.strip():
                aguardando_desc_secao = True
            continue

        # SubseÃ§Ã£o
        if detectar_subsecao(texto):
            num, desc = split_num_nome(texto, r"^(SUBSE[CÃ‡][AÃƒ]O\s+[IVXLCDM]+)(.*)")
            if estado.secao_dict is None:
                if estado.capitulo_dict is None:
                    if estado.titulo_dict is None:
                        estado.abrir_titulo(make_titulo(titulo="", descricao=""))
                    estado.abrir_capitulo(make_capitulo(capitulo="", descricao=""))
                estado.abrir_secao(make_secao(secao="", descricao=""))
            estado.abrir_subsecao(make_subsecao(subsecao=num, descricao=desc))
            if not desc.strip():
                aguardando_desc_subsecao = True
            continue

        # Artigo
        if detectar_artigo(texto):
            if estado.titulo_dict is None:
                estado.abrir_titulo(make_titulo(titulo="", descricao=""))
            match = re.match(r"^(Art\.\s*\d+[ÂºoÂ°]?(?:[â€“\-][A-Z])?\s*\.?\s*)", texto, re.IGNORECASE)
            num_a = match.group(1).strip() if match else texto[:25]
            caput = texto[len(num_a) :].strip() if match else texto
            estado.abrir_artigo(make_artigo(numero=num_a, caput=caput))
            continue

        # ParÃ¡grafo
        if detectar_paragrafo(texto) and estado.artigo_dict:
            match = re.match(
                r"^(Â§\s*\d+[ÂºoÂ°]?(?:[â€“\-][A-Z])?\s*\.?\s*[-â€“]?\s*|ParÃ¡grafo\s+Ãºnico\.?\s*[-â€“]?\s*)",
                texto,
                re.IGNORECASE,
            )
            num_p = match.group(1).strip() if match else "Â§"
            corpo = texto[len(num_p) :].strip() if match else texto
            estado.abrir_paragrafo(make_paragrafo(numero=num_p, texto=corpo))
            continue

        # Inciso
        if detectar_inciso(texto) and estado.artigo_dict:
            partes = re.split(r"\s*[â€“\-]\s*", texto, maxsplit=1)
            num_i = partes[0].strip()
            corpo = partes[1].strip() if len(partes) > 1 else ""
            estado.abrir_inciso(make_inciso(numero=num_i, texto=corpo))
            continue

        # AlÃ­nea
        if detectar_alinea(texto) and estado.inciso_dict:
            match = re.match(r"^([a-z]\))\s*", texto, re.IGNORECASE)
            num_al = (match.group(1) or "").strip() if match else "a)"
            corpo = texto[len(num_al) :].strip() if match else texto
            estado.inciso_dict["alineas"].append(make_alinea(numero=num_al, texto=corpo))
            continue

    titulo_final = estado.fechar_titulo()
    if titulo_final:
        titulos.append(titulo_final)

    for tit in titulos:
        tit.pop("_direto", None)
        for cap in tit.get("capitulos", []):
            cap.pop("_direto", None)

    return titulos


def _filtrar_por_fragmento(titulos: list[dict[str, Any]], fragment: str) -> list[dict[str, Any]]:
    """
    Se a URL tem fragmento tipo #art1, tenta reduzir a saÃ­da para o(s) artigo(s) relevantes.
    Se nÃ£o conseguir inferir, retorna tudo.
    """
    frag = (fragment or "").strip().lstrip("#")
    if not frag:
        return titulos

    m = re.match(r"^art(\d+)", frag, re.IGNORECASE)
    if not m:
        return titulos

    alvo = m.group(1)
    alvo_re = re.compile(rf"^Art\.\s*{re.escape(alvo)}\b", re.IGNORECASE)

    out: list[dict[str, Any]] = []
    for t in titulos:
        t2 = {**t, "capitulos": []}
        for c in t.get("capitulos", []):
            c2 = {**c, "secoes": [], "artigos": []}
            for s in c.get("secoes", []):
                s2 = {**s, "subsecoes": [], "artigos": []}
                for ss in s.get("subsecoes", []):
                    ss2 = {**ss, "artigos": []}
                    for a in ss.get("artigos", []):
                        if alvo_re.match(a.get("numero_artigo", "")):
                            ss2["artigos"].append(a)
                    if ss2["artigos"]:
                        s2["subsecoes"].append(ss2)
                for a in s.get("artigos", []):
                    if alvo_re.match(a.get("numero_artigo", "")):
                        s2["artigos"].append(a)
                if s2["artigos"] or s2["subsecoes"]:
                    c2["secoes"].append(s2)

            for a in c.get("artigos", []):
                if alvo_re.match(a.get("numero_artigo", "")):
                    c2["artigos"].append(a)

            if c2["artigos"] or c2["secoes"]:
                t2["capitulos"].append(c2)

        if t2["capitulos"]:
            out.append(t2)

    return out or titulos


def scrap_link_planalto(url: str) -> dict[str, Any]:
    p = urlparse(url)
    html = baixar_html(url)
    titulos = _parsear_documento_planalto(html)
    titulos = _filtrar_por_fragmento(titulos, p.fragment)
    return {
        "url": url,
        "path": p.path,
        "fragment": p.fragment,
        "estrutura": titulos,
    }


def main() -> None:
    LOGGER.info("[+] Coletando links da Constituicao: %s", BASE_URL)

    def precisa_rescrap(item_existente: dict[str, Any]) -> bool:
        try:
            blob = json.dumps(item_existente.get("dados"), ensure_ascii=False)
        except Exception as exc:
            LOGGER.debug("Falha ao serializar item para checagem de rescrape: %s", exc)
            return True
        return ("\ufffd" in blob) or ("à¸¢à¸š" in blob)

    deps = LinksPipelineDeps(
        extract_links=lambda: extrair_links_constituicao(BASE_URL),
        is_planalto_ccivil=_is_planaltoccivil,
        scrape_link=scrap_link_planalto,
        should_rescrape=precisa_rescrap,
    )
    service = LinksService(OUTPUT_JSON, deps)
    saida = service.run()

    LOGGER.info("[+] Links processados: %s", len(saida))
    LOGGER.info("[+] Salvo em: %s", OUTPUT_JSON.resolve())


if __name__ == "__main__":
    main()


