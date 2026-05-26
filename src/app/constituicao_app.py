"""
Hierarquia de dados para a Legislação - Constituição:
Título
    └── Capítulo
        └── Seção
            ├── Subseção
            └── Artigo
                ├── referenciais legislativos
                ├── modificações históricas            
                └── Parágrafo
                    ├── referenciais legislativos
                    ├── modificações históricas            
                    └── Inciso
                        ├── referenciais legislativos
                        ├── modificações históricas            
                        └── Alínea
                            ├── referenciais legislativos
                            └──  modificações históricas            
"""

import time
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from utils.constituicao_utils import get_logger, normalize_whitespace, sanitize_text_for_json, split_num_nome
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
from parsers.schema import (
    EstadoParser,
    STATUS_VIGENTE,
    STATUS_REVOGADO,
    make_titulo,
    make_capitulo,
    make_secao,
    make_subsecao,
    make_artigo,
    make_paragrafo,
    make_inciso,
    make_alinea,
)
from parsers.referencias import (
    extrair_modificacoes_historicas,
    extrair_referenciais_legislativos,
    forcar_status_em_referencias,
)
from services.constituicao_service import ConstituicaoPipelineDeps, ConstituicaoService


BASE_URL = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
OUTPUT_DIR = Path("output_constituicao")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "constituicao_schema.json"
LOGGER = get_logger(__name__)

def _texto_indica_revogacao(texto: str) -> bool:
    t = (texto or "").strip().lower()

    inicio = t[:80]

    padroes = [
        r'^\(?revogad[oa]\)?[\.;,\s]',         
        r'^[a-z0-9]+\)\s*\(?revogad[oa]\)?',    
        r'^\(?revogad[oa]\)?$',                 
    ]
    return any(re.search(p, inicio) for p in padroes)


def _extrair_desc_vigente_do_elem(elem) -> str:
    """
    Extrai a descrição VIGENTE de um elemento que pode conter texto riscado misturado com texto normal
    Retorna string vazia se não sobrar texto útil.
    """
    if elem is None:
        return ""

    import copy
    copia = copy.copy(elem)

    # Remove tags riscadas
    for tag in copia.find_all(["strike", "s", "del"]):
        tag.decompose()

    # Remove tags com style line-through
    for tag in copia.find_all(True):
        style = (tag.attrs or {}).get("style", "") or ""
        if "line-through" in style.lower():
            tag.decompose()

    # Remove links (não fazem parte da descrição)
    for tag in copia.find_all("a"):
        tag.decompose()

    texto = re.sub(r"\s{2,}", " ", copia.get_text(" ", strip=True) or "").strip()
    return texto


def _elem_e_apenas_link_redacao_dada(elem) -> bool:
    """
    Retorna True se o elemento contém APENAS um link do tipo
    'Redação dada pela Emenda Constitucional ...' sem texto livre adicional.
    """
    if elem is None:
        return False
    texto_bruto = re.sub(r"\s{2,}", " ", elem.get_text(" ", strip=True) or "").strip()
    t_low = texto_bruto.lower()
    # Só contém link de redação dada / incluída / revogada se o texto começa com esses padrões
    if re.match(
        r"^\(?(?:redação\s+dada|incluíd[oa]|revogad[oa])\b",
        t_low,
        flags=re.IGNORECASE,
    ):
        return True
    return False


def _elemento_em_risco(elem) -> bool:
    """
    Detecta se o texto está visualmente "riscado" no HTML
    (<strike>, <s>, <del>, ou style line-through)
    """
    if elem is None:
        return False

    strike_tags = {"strike", "s", "del"}

    try:
        if elem.find(list(strike_tags)):
            return True
    except Exception as exc:
        LOGGER.debug("Falha ao buscar tags riscadas no elemento: %s", exc)

    try:
        cadeia = [elem, *list(getattr(elem, "parents", []))]
    except Exception:
        cadeia = [elem]

    for t in cadeia:
        nome = getattr(t, "name", None)
        if nome in strike_tags:
            return True
        style = (getattr(t, "attrs", {}) or {}).get("style", "") or ""
        style_l = style.lower()
        if "line-through" in style_l:
            return True
        if "text-decoration" in style_l and "through" in style_l:
            return True

    # Check line-through on descendant elements (span, font, etc.)
    try:
        for child in elem.find_all(True):
            style = (child.attrs or {}).get("style", "") or ""
            if "line-through" in style.lower():
                return True
    except Exception as exc:
        LOGGER.debug("Falha ao inspecionar estilos dos descendentes: %s", exc)

    return False


def detectar_status_dispositivo(texto: str, elem) -> str:
    if _texto_indica_revogacao(texto) or _elemento_em_risco(elem):
        return STATUS_REVOGADO
    return STATUS_VIGENTE


# CRIAR DRIVER
def criar_driver (headless: bool = False) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    service =  Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver


# CARREGAR PÁGINA
def carregar_pagina(driver: webdriver.Chrome, url: str) -> str:
    LOGGER.info("Acessando: %s", url)
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        LOGGER.warning("Timeout ao aguardar o carregamento da pagina.")
    time.sleep(2)
    LOGGER.info("Pagina carregada: %s", driver.title)
    return driver.page_source


# PARSER PRINCIPAL
def parsear_constituicao(html: str) -> List[Dict]:
    """
    Faz o parsing do HTML e retorna lista
    no formato exato do schema estrutura_constituicao.json.
    """
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    body = soup.find("body")
    if not body:
        LOGGER.warning("Body nao encontrado.")
        return []

    elementos = body.find_all(["p", "h1", "h2", "h3", "h4", "h5"])

    titulos_resultado: List[Dict] = []
    estado = EstadoParser()
    coletando_preambulo = True

    aguardando_desc_titulo = False
    aguardando_desc_capitulo = False
    aguardando_desc_secao = False
    aguardando_desc_subsecao = False


    for elem in elementos:
        texto = re.sub(r'[\n\r\t]+', ' ', elem.get_text(" ", strip=True)).strip()
        
        texto = sanitize_text_for_json(texto)
        if not texto or len(texto) < 2:
            continue

        texto_upper = texto.upper().strip()
        status_dispositivo = detectar_status_dispositivo(texto, elem)
        refs_no_elem = extrair_referenciais_legislativos(elem, status_dispositivo=status_dispositivo)
        mods_no_elem = extrair_modificacoes_historicas(elem, status_dispositivo=status_dispositivo)

        # Marcador de preâmbulo
        if "PREÂMBULO" in texto_upper or "PREAMBULO" in texto_upper:
            coletando_preambulo = True
            aguardando_desc_titulo = False
            aguardando_desc_capitulo = False
            aguardando_desc_secao = False
            continue

        if aguardando_desc_titulo:
            aguardando_desc_titulo = False
            if estado.titulo_dict is not None:
                estado.titulo_dict["descricao_do_titulo"] = texto.upper()
                if refs_no_elem:
                    estado.titulo_dict["referenciais_legislativos"].extend(refs_no_elem)
                if mods_no_elem:
                    estado.titulo_dict["modificacoes_historicas"].extend(mods_no_elem)
            continue

        if aguardando_desc_capitulo:
            if detectar_titulo(texto) or detectar_capitulo(texto) or detectar_secao(texto):
                aguardando_desc_capitulo = False
            elif _elem_e_apenas_link_redacao_dada(elem):
                if estado.capitulo_dict is not None:
                    desc_antiga_pend = estado.capitulo_dict.get("_desc_antiga_pendente")
                    if refs_no_elem:
                        estado.capitulo_dict["referenciais_legislativos"].extend(refs_no_elem)
                    if mods_no_elem:
                        for mod in mods_no_elem:
                            if desc_antiga_pend and not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = desc_antiga_pend
                        estado.capitulo_dict["modificacoes_historicas"].extend(mods_no_elem)
                        if desc_antiga_pend:
                            estado.capitulo_dict.pop("_desc_antiga_pendente", None)
                continue
            elif _elemento_em_risco(elem):
                if estado.capitulo_dict is not None:
                    if estado.capitulo_dict["modificacoes_historicas"]:
                        for mod in estado.capitulo_dict["modificacoes_historicas"]:
                            if not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = texto
                    else:
                        estado.capitulo_dict["_desc_antiga_pendente"] = texto
                continue
            else:
                aguardando_desc_capitulo = False
                if estado.capitulo_dict is not None:
                    desc_antiga_pend = estado.capitulo_dict.pop("_desc_antiga_pendente", None)
                    estado.capitulo_dict["descricao_do_capitulo"] = texto.upper()
                    if refs_no_elem:
                        estado.capitulo_dict["referenciais_legislativos"].extend(refs_no_elem)
                    if mods_no_elem:
                        for mod in mods_no_elem:
                            if desc_antiga_pend and not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = desc_antiga_pend
                        estado.capitulo_dict["modificacoes_historicas"].extend(mods_no_elem)
                    elif desc_antiga_pend:
                        estado.capitulo_dict["_desc_antiga_pendente"] = desc_antiga_pend
                continue

        if aguardando_desc_secao:
            if detectar_titulo(texto) or detectar_capitulo(texto) or detectar_secao(texto):
                aguardando_desc_secao = False
            elif _elem_e_apenas_link_redacao_dada(elem):
                if estado.secao_dict is not None:
                    desc_antiga_pend = estado.secao_dict.get("_desc_antiga_pendente")
                    if refs_no_elem:
                        estado.secao_dict["referenciais_legislativos"].extend(refs_no_elem)
                    if mods_no_elem:
                        for mod in mods_no_elem:
                            if desc_antiga_pend and not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = desc_antiga_pend
                        estado.secao_dict["modificacoes_historicas"].extend(mods_no_elem)
                        if desc_antiga_pend:
                            estado.secao_dict.pop("_desc_antiga_pendente", None)
                continue
            elif _elemento_em_risco(elem):
                if estado.secao_dict is not None:
                    if estado.secao_dict["modificacoes_historicas"]:
                        for mod in estado.secao_dict["modificacoes_historicas"]:
                            if not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = texto
                    else:
                        estado.secao_dict["_desc_antiga_pendente"] = texto
                continue
            else:
                aguardando_desc_secao = False
                if estado.secao_dict is not None:
                    desc_antiga_pend = estado.secao_dict.pop("_desc_antiga_pendente", None)
                    estado.secao_dict["descricao_da_secao"] = texto.upper()
                    if refs_no_elem:
                        estado.secao_dict["referenciais_legislativos"].extend(refs_no_elem)
                    if mods_no_elem:
                        for mod in mods_no_elem:
                            if desc_antiga_pend and not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = desc_antiga_pend
                        estado.secao_dict["modificacoes_historicas"].extend(mods_no_elem)
                    elif desc_antiga_pend:
                        estado.secao_dict["_desc_antiga_pendente"] = desc_antiga_pend
                continue

        if aguardando_desc_subsecao:
            aguardando_desc_subsecao = False
            if estado.subsecao_dict is not None:
                estado.subsecao_dict["descricao_da_subsecao"] = texto.upper()
                if refs_no_elem:
                    estado.subsecao_dict["referenciais_legislativos"].extend(refs_no_elem)
                if mods_no_elem:
                    estado.subsecao_dict["modificacoes_historicas"].extend(mods_no_elem)
            continue

        # Título
        if detectar_titulo(texto):
            coletando_preambulo = False
            titulo_fechado = estado.fechar_titulo()
            if titulo_fechado:
                titulos_resultado.append(titulo_fechado)

            num, desc = split_num_nome(texto, r'^(TÍTULO\s+[IVXLCDM]+)(.*)')
            novo_titulo = make_titulo(titulo=num, descricao=desc, status=status_dispositivo)
            if refs_no_elem:
                novo_titulo["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                novo_titulo["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_titulo(novo_titulo)
            if not desc.strip():
                aguardando_desc_titulo = True
            continue

        # Capítulo
        if detectar_capitulo(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(CAPÍTULO\s+[IVXLCDM]+)(.*)')

            if elem.find(["strike", "s", "del"]):
                desc_vigente_raw = _extrair_desc_vigente_do_elem(elem)
                num_upper = num.strip().upper()
                if desc_vigente_raw.upper().startswith(num_upper):
                    desc_vigente_raw = desc_vigente_raw[len(num_upper):].strip()
                desc_vigente_raw = re.sub(r'^[-–:\s]+', '', desc_vigente_raw)
                if desc_vigente_raw.strip():
                    desc = desc_vigente_raw

            novo_capitulo = make_capitulo(capitulo=num, descricao=desc, status=status_dispositivo)
            if refs_no_elem:
                novo_capitulo["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                novo_capitulo["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_capitulo(novo_capitulo)
            if not desc.strip():
                 aguardando_desc_capitulo = True
            continue

        # Seção
        if detectar_secao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SE[CÇ][AÃ]O\s+[IVXLCDM]+(?:-[A-Z])?)(.*)')

            if elem.find(["strike", "s", "del"]):
                desc_vigente_raw = _extrair_desc_vigente_do_elem(elem)
                num_upper = num.strip().upper()
                if desc_vigente_raw.upper().startswith(num_upper):
                    desc_vigente_raw = desc_vigente_raw[len(num_upper):].strip()
                desc_vigente_raw = re.sub(r'^[-–:\s]+', '', desc_vigente_raw)
                if desc_vigente_raw.strip():
                    desc = desc_vigente_raw

            nova_secao = make_secao(secao=num, descricao=desc, status=status_dispositivo)
            if refs_no_elem:
                nova_secao["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                nova_secao["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_secao(nova_secao)
            if not desc.strip():
                 aguardando_desc_secao = True
            continue

        # Subseção
        if detectar_subsecao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)')
            nova_subsecao = make_subsecao(subsecao=num, descricao=desc, status=status_dispositivo)
            if refs_no_elem:
                nova_subsecao["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                nova_subsecao["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_subsecao(nova_subsecao)
            if not desc.strip():
                 aguardando_desc_subsecao = True
            continue

        # Artigo
        if detectar_artigo(texto):
            coletando_preambulo = False
            match = re.match(r'^(Art\.\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*)', texto, re.IGNORECASE)
            num_a  = match.group(1).strip() if match else texto[:25]
            caput  = texto[len(num_a):].strip() if match else texto
            artigo = make_artigo(numero=num_a, caput=caput, status=status_dispositivo)
            if refs_no_elem:
                artigo["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                artigo["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_artigo(artigo)
            continue

        # Parágrafo
        if detectar_paragrafo(texto) and estado.artigo_dict:
            match = re.match(r'^(§\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)', texto, re.IGNORECASE)
            num_p  = match.group(1).strip() if match else "§"
            corpo  = texto[len(num_p):].strip() if match else texto
            par = make_paragrafo(numero=num_p, texto=corpo, status=status_dispositivo)
            if refs_no_elem:
                par["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                par["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_paragrafo(par)
            continue

        # Inciso
        if detectar_inciso(texto) and estado.artigo_dict:
            matches = re.split(r'\s*[–\-]\s*', texto, maxsplit=1)
            num_i  = matches[0].strip()
            corpo  = matches[1].strip() if len(matches) > 1 else ""
            inc = make_inciso(numero=num_i, texto=corpo, status=status_dispositivo)
            if refs_no_elem:
                inc["referenciais_legislativos"].extend(refs_no_elem)
            if mods_no_elem:
                inc["modificacoes_historicas"].extend(mods_no_elem)
            estado.abrir_inciso(inc)
            continue

        # Alínea
        if detectar_alinea(texto) and estado.inciso_dict:
            match  = re.match(r'^([a-z]\s*\))\s*', texto)
            
            # Padroniza para remover espaços internos (transforma "a )" em "a)")
            num_al = match.group(1).replace(" ", "").strip() if match else "a)"
            corpo  = texto[match.end():].strip() if match else texto
            matches = re.split(r'(?<!\w)([a-z]\s*\))\s+', corpo)
            alineas_para_inserir = [(num_al, matches[0].strip())]
            for letra, seg in zip(matches[1::2], matches[2::2]):
                letra_limpa = letra.replace(" ", "").strip()
                alineas_para_inserir.append((letra_limpa, seg.strip()))

            for idx, (num, corp) in enumerate(alineas_para_inserir):
                ali = make_alinea(numero=num, texto=corp, status=status_dispositivo)
                if idx == 0:
                    if refs_no_elem:
                        ali["referenciais_legislativos"].extend(refs_no_elem)
                    if mods_no_elem:
                        ali["modificacoes_historicas"].extend(mods_no_elem)
                estado.inciso_dict["alineas"].append(ali)
            continue

        # Preâmbulo → ignora
        if coletando_preambulo:
            continue

        # Se o parágrafo não abriu um novo dispositivo, mas contém links, anexa os referenciais ao último dispositivo "aberto".
        if refs_no_elem or mods_no_elem:
            alvo = estado.inciso_dict or estado.paragrafo_dict or estado.artigo_dict
            if alvo is None:
                alvo = estado.subsecao_dict or estado.secao_dict or estado.capitulo_dict or estado.titulo_dict
            if alvo is not None:
                # Se estamos anexando a um dispositivo já aberto, o status do dispositivo tem prioridade para o status das referências.
                status_alvo = (
                    alvo.get("status_da_alinea")
                    or alvo.get("status_do_inciso")
                    or alvo.get("status_do_paragrafo")
                    or alvo.get("status_do_artigo")
                    or alvo.get("status_da_subsecao")
                    or alvo.get("status_da_secao")
                    or alvo.get("status_do_capitulo")
                    or alvo.get("status_do_titulo")
                )
                if refs_no_elem:
                    alvo["referenciais_legislativos"].extend(
                        forcar_status_em_referencias(refs_no_elem, status_alvo)
                    )
                if mods_no_elem:
                    desc_antiga_pend = alvo.get("_desc_antiga_pendente", None)
                    if desc_antiga_pend:
                        for mod in mods_no_elem:
                            if not mod.get("texto_antigo_descontinuado"):
                                mod["texto_antigo_descontinuado"] = desc_antiga_pend
                    alvo["modificacoes_historicas"].extend(mods_no_elem)

    # Fecha o último estado pendente
    titulo_final = estado.fechar_titulo()
    if titulo_final:
        titulos_resultado.append(titulo_final)

    # Remove chaves internas auxiliares
    for tit in titulos_resultado:
        tit.pop("_direto", None)
        for cap in tit.get("capitulos", []):
            cap.pop("_direto", None)

    return titulos_resultado


# SALVAR DADOS EM JSON
def salvar_json(dados: List[Dict], caminho: Path) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    LOGGER.info("JSON salvo em: %s", caminho)


# MAIN
def main():
    LOGGER.info("=" * 50)
    LOGGER.info("Parser - Constituicao Federal do Brasil")
    LOGGER.info("Output: constituicao_schema.json")
    LOGGER.info("=" * 50)

    deps = ConstituicaoPipelineDeps(
        create_driver=criar_driver,
        load_page=carregar_pagina,
        parse_html=parsear_constituicao,
    )
    service = ConstituicaoService(BASE_URL, OUTPUT_JSON, deps)
    LOGGER.info("[+] Parsing estruturado...")
    _ = service.run(headless=True)
    LOGGER.info("Arquivo: %s", OUTPUT_JSON.resolve())
    LOGGER.info("[+] Driver encerrado.")

    
if __name__ == "__main__":
    main()

