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

from scrap_legisla_consti import (
    EstadoParser,
    detectar_alinea,
    detectar_artigo,
    detectar_capitulo,
    detectar_inciso,
    detectar_paragrafo,
    detectar_secao,
    detectar_subsecao,
    detectar_titulo,
    make_alinea,
    make_artigo,
    make_capitulo,
    make_inciso,
    make_paragrafo,
    make_secao,
    make_subsecao,
    make_titulo,
    split_num_nome,
)


BASE_URL = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
OUTPUT_DIR = Path("output_constituicao")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "dados_links.json"


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
    s = re.sub(r"[\r\n\t]+", " ", s or "").strip()
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"(\d)\ufffd\b", r"\1º", s)
    return s


def _is_planaltoccivil(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
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
            print(f"Tentativa {attempt} falhou: {e} - {url}")
            if attempt >= 5:
                break
            time.sleep(min(2**attempt, 20))
    assert last_err is not None
    raise last_err


def extrair_links_constituicao(url: str = BASE_URL) -> list[LinkInfo]:
    try:
        html = baixar_html(url)
    except Exception:
        # fallback: reaproveita o arquivo já existente (útil se o Planalto estiver com 503/429)
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
            except Exception:
                pass
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
        print("[!] Body não encontrado.")
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
    Parser estruturado (Planato/ccivil_03) para gerar uma árvore parecida com a da Constituição:
    Título -> Capítulo -> Seção -> Subseção -> Artigo -> Parágrafo -> Inciso -> Alínea.
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

        # Título
        if detectar_titulo(texto):
            titulo_fechado = estado.fechar_titulo()
            if titulo_fechado:
                titulos.append(titulo_fechado)

            num, desc = split_num_nome(texto, r"^(TÍTULO\s+[IVXLCDM]+)(.*)")
            novo_titulo = make_titulo(titulo=num, descricao=desc)
            estado.abrir_titulo(novo_titulo)
            if not desc.strip():
                aguardando_desc_titulo = True
            continue

        # Capítulo
        if detectar_capitulo(texto):
            num, desc = split_num_nome(texto, r"^(CAPÍTULO\s+[IVXLCDM]+)(.*)")
            if estado.titulo_dict is None:
                estado.abrir_titulo(make_titulo(titulo="", descricao=""))
            estado.abrir_capitulo(make_capitulo(capitulo=num, descricao=desc))
            if not desc.strip():
                aguardando_desc_capitulo = True
            continue

        # Seção
        if detectar_secao(texto):
            num, desc = split_num_nome(texto, r"^(SE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)")
            if estado.capitulo_dict is None:
                if estado.titulo_dict is None:
                    estado.abrir_titulo(make_titulo(titulo="", descricao=""))
                estado.abrir_capitulo(make_capitulo(capitulo="", descricao=""))
            estado.abrir_secao(make_secao(secao=num, descricao=desc))
            if not desc.strip():
                aguardando_desc_secao = True
            continue

        # Subseção
        if detectar_subsecao(texto):
            num, desc = split_num_nome(texto, r"^(SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)")
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
            match = re.match(r"^(Art\.\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*)", texto, re.IGNORECASE)
            num_a = match.group(1).strip() if match else texto[:25]
            caput = texto[len(num_a) :].strip() if match else texto
            estado.abrir_artigo(make_artigo(numero=num_a, caput=caput))
            continue

        # Parágrafo
        if detectar_paragrafo(texto) and estado.artigo_dict:
            match = re.match(
                r"^(§\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)",
                texto,
                re.IGNORECASE,
            )
            num_p = match.group(1).strip() if match else "§"
            corpo = texto[len(num_p) :].strip() if match else texto
            estado.abrir_paragrafo(make_paragrafo(numero=num_p, texto=corpo))
            continue

        # Inciso
        if detectar_inciso(texto) and estado.artigo_dict:
            partes = re.split(r"\s*[–\-]\s*", texto, maxsplit=1)
            num_i = partes[0].strip()
            corpo = partes[1].strip() if len(partes) > 1 else ""
            estado.abrir_inciso(make_inciso(numero=num_i, texto=corpo))
            continue

        # Alínea
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
    Se a URL tem fragmento tipo #art1, tenta reduzir a saída para o(s) artigo(s) relevantes.
    Se não conseguir inferir, retorna tudo.
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
    print(f"[+] Coletando links da Constituição: {BASE_URL}", flush=True)
    links = extrair_links_constituicao(BASE_URL)
    print(f"[+] Links encontrados: {len(links)}", flush=True)

    # resume/cache: se já existe arquivo anterior, reaproveita e só completa o que falta
    existentes_por_url: dict[str, dict[str, Any]] = {}
    if OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                existentes = json.load(f)
            if isinstance(existentes, list):
                for it in existentes:
                    if isinstance(it, dict) and isinstance(it.get("url"), str):
                        existentes_por_url[it["url"]] = it
        except Exception:
            existentes_por_url = {}

    saida: list[dict[str, Any]] = []
    total = len(links)

    def precisa_rescrap(item_existente: dict[str, Any]) -> bool:
        try:
            blob = json.dumps(item_existente.get("dados"), ensure_ascii=False)
        except Exception:
            return True
        return ("\ufffd" in blob) or ("ยบ" in blob)

    for idx, link in enumerate(links, start=1):
        item: dict[str, Any] = {
            "texto": link.texto,
            "url": link.url,
            "tipo": "planalto_ccivil" if _is_planaltoccivil(link.url) else "externo",
        }

        anterior = existentes_por_url.get(link.url)
        if isinstance(anterior, dict):
            # preserva o que já foi coletado; atualiza texto/tipo se mudarem
            item.update(anterior)
            item["texto"] = link.texto
            item["tipo"] = "planalto_ccivil" if _is_planaltoccivil(link.url) else "externo"

        if _is_planaltoccivil(link.url):
            if item.get("sucesso") is True and isinstance(item.get("dados"), dict):
                if precisa_rescrap(item):
                    item["sucesso"] = False
                    item.pop("erro", None)
                else:
                    print(f"[{idx}/{total}] (cache) {link.url}", flush=True)
            else:
                try:
                    print(f"[{idx}/{total}] (scrap) {link.url}", flush=True)
                    item["dados"] = scrap_link_planalto(link.url)
                    item["sucesso"] = True
                except Exception as e:
                    item["sucesso"] = False
                    item["erro"] = str(e)
        saida.append(item)

        # grava incrementalmente (para execuções longas)
        try:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(saida, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"[+] Salvo em: {OUTPUT_JSON.resolve()}")


if __name__ == "__main__":
    main()

