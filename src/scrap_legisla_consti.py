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
import uuid
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


BASE_URL = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
OUTPUT_DIR = Path("output_constituicao")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "constituicao_schema.json"

# STATUS DA MODIFICAÇÃO
STATUS_VIGENTE        = "VIGENTE"
STATUS_REVOGADO       = "REVOGADO"

# TIPO DE MODIFICAÇÃO
TIPO_INCLUSAO  = "INCLUSAO"
TIPO_ALTERACAO = "ALTERACAO"
TIPO_REVOGACAO = "REVOGACAO"

# TIPO DE REFERÊNCIA
TIPO_REF_LEI       = "LEI"
TIPO_REF_DECRETO   = "DECRETO"
TIPO_REF_DECRETO_LEI = "DECRETO-LEI"
TIPO_REF_EMENDA    = "EMENDA"
TIPO_REF_MPV       = "MPV"
TIPO_REF_ADI       = "ADI"
TIPO_REF_ADIN      = "ADIN"
TIPO_REF_ADPF      = "ADPF"
TIPO_REF_OUTRO     = "OUTRO"


# GERRAR ID
def gerar_id():
    return str(uuid.uuid4())


# MODIFICAÇÕES HISTÓRICAS
def make_modificacoes_historicas (
    tipo: Optional[str] = None,
    descricao: str = "",
    texto_antigo: str = "",
    status: Optional[str] = None,
) -> Dict [str, Any]:
    """
    Schema:
    {
        "tipo_de_modificacao": "INCLUSAO | ALTERACAO | REVOGACAO",
        "descricao_da_modificacao": "...",
        "texto_antigo_descontinuado": "...",
        "status_da_modificacao": "VIGENTE | REVOGADO"
    }
    """
    return {
        "tipo_de_modificacao": tipo,
        "descricao_da_modificacao": descricao,
        "texto_antigo_descontinuado": texto_antigo,
        "status_da_modificacao": status,
    }


# REFERENCIAIS LEGISLATIVOS
def make_referencial_legislativo(
    numero: str = "",
    tipo: Optional[str] = None,
    texto: str = "",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_referencia": "...",
        "numero_referencia": "...",
        "tipo_de_referencia": "LEI | DECRETO | DECRETO-LEI | EMENDA | MPV | ADI | ADIN | ADPF | OUTRO",
        "texto_da_referencia": "...",
        "status_da_modificacao": "VIGENTE | REVOGADO"
    }
    """
    return {
        "id_referencia": gerar_id(),
        "numero_referencia": numero,
        "tipo_de_referencia": tipo,
        "texto_da_referencia": texto,
        "status_da_referencia": status,
    }


# TÍTULOS
def make_titulo(
    titulo: str = "",
    descricao: str = "",
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "titulo": "...",
        "descricao_do_titulo": "...",
        "capitulos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "titulo": titulo,
        "descricao_do_titulo": descricao.upper(),
        "capitulos": [],
    }


# CAPÍTULO
def make_capitulo(
    capitulo: str = "",
    descricao: str = "",
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "capitulo": "...",
        "descricao_do_capitulo": "...",
        "secoes": [...],
        "artigos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "capitulo": capitulo,
        "descricao_do_capitulo": descricao.upper(),
        "secoes": [],
        "artigos": [],
    }


# SEÇÕES
def make_secao(
    secao: str = "",
    descricao: str = "",
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "secao": "...",
        "descricao_da_secao": "...",
        "subsecoes": [...],
        "artigos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "secao": secao,
        "descricao_da_secao": descricao.upper(),
        "subsecoes": [],
        "artigos": [],
    }

# SUBSEÇÃO
def make_subsecao(
    subsecao: str = "",
    descricao: str = "",
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "subsecao": "...",
        "descricao_da_subsecao": "...",
        "artigos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "subsecao": subsecao,
        "descricao_da_subsecao": descricao.upper(),
        "artigos": [],
    }


# ARTIGOS
def make_artigo(
    numero: str = "",
    caput: str = "",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "numero_artigo": "...",
        "caput": "...",
        "status_do_artigo": "VIGENTE | REVOGADO",
        "referenciais_legislativos": [...],
        "modificacoes_historicas": [...],
        "paragrafos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "numero_artigo": numero,
        "caput": caput,
        "status_do_artigo": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "incisos_caput": [],
        "paragrafos": [],
    }


# PARÁGRAFOS
def make_paragrafo(
    numero: str = "",
    texto: str = "",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "numero_paragrafo": "...",
        "texto_do_paragrafo": "...",
        "status_do_paragrafo": "VIGENTE | REVOGADO ",
        "refereiais_legislativos": [...],
        "modificacoes_historicas": [...],
        "incisos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "numero_paragrafo": numero,
        "texto_do_paragrafo": texto,
        "status_do_paragrafo": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "incisos": [],
    }


# INCISO
def make_inciso(
    numero: str = "",
    texto: str = "",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "numero_inciso": "...",
        "texto_do_inciso": "...",
        "status_do_inciso": "VIGENTE | REVOGADO ",
        "refereiais_legislativos": [...],
        "modificacoes_historicas": [...],
        "alineas": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "numero_inciso": numero,
        "texto_do_inciso": texto,
        "status_do_inciso": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "alineas": [],
    }


# ALINEA
def make_alinea(
    numero: str = "",
    texto: str = "",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Schema:
    {
        "id_dispositivo_legislativo": "...",
        "numero_alinea": "...",
        "texto_da_alinea": "...",
        "status_da_alinea": "VIGENTE | REVOGADO | REDACAO_ANTIGA",
        "refereiais_legislativos": [...],
        "modificacoes_historicas": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "numero_alinea": numero,
        "texto_da_alinea": texto,
        "status_da_alinea": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
    }


# DETECÇÃO DE ELEMENTOS
def detectar_titulo(t: str) -> bool:
    return bool(re.match(r'^TÍTULO\s+[IVXLCDM]+', t.strip().upper()))

def detectar_capitulo(t: str) -> bool:
    return bool(re.match(r'^CAPÍTULO\s+[IVXLCDM]+', t.strip().upper()))  

def detectar_secao(t: str) -> bool:    
    return bool(re.match(r'^SE[CÇ][AÃ]O\s+[IVXLCDM]+', t.strip().upper()))  

def detectar_subsecao(t: str) -> bool:    
    return bool(re.match(r'^SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+', t.strip().upper())) 

def detectar_artigo(t: str) -> bool:    
    return bool(re.match(r'^Art\.\s*\d+', t.strip(), re.IGNORECASE))

def detectar_paragrafo(t: str) -> bool:
    return bool(re.match(r'^(§\s*\d+\s*[ºo]?\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)', t.strip(),re.IGNORECASE))

def detectar_inciso(t: str) -> bool:
    return bool(re.match(r'^[IVXLCDM]+\s*[–\-]\s+', t.strip()))

def detectar_alinea(t: str) -> bool:    
    return bool(re.match(r'^\s*([a-z]\s*\))\s*', t.strip()))

def split_num_nome(t: str, pattern: str) -> tuple[str, str]:
    match = re.match(pattern, t.strip(), re.IGNORECASE)
    if match:
        num = match.group(1).strip()
        nome = t.strip()[len(match.group(0)):].strip()
        nome = re.sub(r'^[-–:\s]+', '', nome)
        return num, nome
    return t.strip(), ""


def _texto_indica_revogacao(texto: str) -> bool:
    t = (texto or "").strip().lower()

    inicio = t[:80]

    padroes = [
        r'^\(?revogad[oa]\)?[\.;,\s]',          # "revogada;", "(revogada)"
        r'^[a-z0-9]+\)\s*\(?revogad[oa]\)?',    # "a) (revogada)"
        r'^\(?revogad[oa]\)?$',                 # só "(revogada)"
    ]
    return any(re.search(p, inicio) for p in padroes)


def _elemento_em_risco(elem) -> bool:
    """
    Detecta se o texto está visualmente "riscado" no HTML (<strike>)
    """
    if elem is None:
        return False

    strike_tags = {"strike"}

    try:
        if elem.find(strike_tags):
            return True
    except Exception:
        pass

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

    return False


def detectar_status_dispositivo(texto: str, elem) -> str:
    if _texto_indica_revogacao(texto) or _elemento_em_risco(elem):
        return STATUS_REVOGADO
    return STATUS_VIGENTE

def _normalizar_numero_documento(numero: str) -> str:
    n = re.sub(r"[^\d]", "", numero or "")
    if not n:
        return ""
    if len(n) <= 3:
        return n
    return f"{n[:-3]}.{n[-3:]}"

def _extrair_numero_referencia(texto: str, href: str) -> str:
    """
    Ex.: "Vide Lei nº 9.296, de 1996" -> "9.296"
    Fallback: tenta inferir pelo path (ex.: ".../LEIS/L9296.htm" -> "9.296")
    """
    t = texto or ""

    # STF: Mandado de Injunção (MI)
    m = re.search(r"\bmi\s*(\d+)\b", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # STF: ADI / ADIN / ADPF
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
        return _normalizar_numero_documento(m.group(1))

    m = re.search(r"/(?:EC|ECONST|EMENDA)(\d+)\.htm", h, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    return ""

def _tipo_de_referencia(texto: str, href: str) -> str:
    h = (href or "").lower()
    t = (texto or "").lower()

    if "stf.jus.br" in h:
        # STF: inferir pelo texto do link conforme escrito na Constituição.
        if "adpf" in t:
            return TIPO_REF_ADPF
        if "adin" in t:
            return TIPO_REF_ADIN
        if re.search(r"\badi\b", t):
            return TIPO_REF_ADI
        return TIPO_REF_OUTRO

    # Planalto: o tipo aparece na URL (lei/decreto/decreto-lei/emendas/mpv)
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

def _status_da_referencia(a_tag) -> str:
    """
    - REVOGADO: se o texto do link começar com "revogado/revogada" ou se houver texto riscado (<strike>/<s>/<del>).
    - VIGENTE: caso contrário.
    """
    if a_tag is None:
        return STATUS_VIGENTE

    texto_link = a_tag.get_text(" ", strip=True) if hasattr(a_tag, "get_text") else ""
    if re.match(r"^\s*revogad[oa]s?\b", texto_link or "", flags=re.IGNORECASE):
        return STATUS_REVOGADO

    # Checa se existe conteúdo riscado antes do link no mesmo bloco
    try:
        for prev in a_tag.previous_elements:
            if prev is a_tag:
                continue
            # para quando sair do parágrafo/bloco atual
            if getattr(prev, "name", None) in {"p", "h1", "h2", "h3", "h4", "h5"}:
                break
            if getattr(prev, "name", None) in {"strike", "s", "del"}:
                return STATUS_REVOGADO
            style = (getattr(prev, "attrs", {}) or {}).get("style", "") or ""
            if "line-through" in style.lower():
                return STATUS_REVOGADO
    except Exception:
        pass

    return STATUS_VIGENTE

def _forcar_status_em_referencias(refs: List[Dict[str, Any]], status: Optional[str]) -> List[Dict[str, Any]]:
    if not refs or not status:
        return refs
    for r in refs:
        r["status_da_referencia"] = status
    return refs

def extrair_referenciais_legislativos(elem, status_dispositivo: Optional[str] = None) -> List[Dict[str, Any]]:
    if elem is None:
        return []
    refs: List[Dict[str, Any]] = []
    try:
        a_tags = elem.find_all("a", href=True)
    except Exception:
        return []

    for a in a_tags:
        href = (a.get("href") or "").strip()
        texto_link = re.sub(r"\s{2,}", " ", a.get_text(" ", strip=True) or "").strip()
        if not href or not texto_link:
            continue

        numero = _extrair_numero_referencia(texto_link, href)
        tipo = _tipo_de_referencia(texto_link, href)
        status = _status_da_referencia(a)
        # Prioridade: se o dispositivo onde o link está inserido é REVOGADO, a referência deve refletir esse status.
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

    return _forcar_status_em_referencias(refs, status_dispositivo)

def _extrair_texto_riscado(elem) -> str:
    """
    Extrai texto "descontinuado" (riscado) no bloco atual:
    - tags <strike>/<s>/<del>
    - qualquer elemento com style contendo line-through
    """
    if elem is None:
        return ""

    partes: List[str] = []

    try:
        for t in elem.find_all(["strike", "s", "del"]):
            tx = re.sub(r"\s{2,}", " ", t.get_text(" ", strip=True) or "").strip()
            if tx:
                partes.append(tx)
    except Exception:
        pass

    try:
        for t in elem.find_all(True):
            style = (t.attrs or {}).get("style", "") or ""
            if "line-through" not in style.lower():
                continue
            tx = re.sub(r"\s{2,}", " ", t.get_text(" ", strip=True) or "").strip()
            if tx:
                partes.append(tx)
    except Exception:
        pass

    # remove duplicados preservando ordem
    vistos = set()
    unicos: List[str] = []
    for p in partes:
        if p in vistos:
            continue
        vistos.add(p)
        unicos.append(p)

    return " | ".join(unicos).strip()

def _tipo_modificacao_por_texto(texto_link: str) -> Optional[str]:
    """
    - "Redação dada ..." => ALTERACAO
    - começa com "Incluído ..." => INCLUSAO
    - começa com "Revogado/Revogada ..." => REVOGACAO
    Caso não encontre padrão, retorna None.
    """
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

def extrair_modificacoes_historicas(elem, status_dispositivo: Optional[str] = None) -> List[Dict[str, Any]]:
    if elem is None:
        return []

    mods: List[Dict[str, Any]] = []
    texto_antigo = _extrair_texto_riscado(elem)

    try:
        a_tags = elem.find_all("a")
    except Exception:
        return []

    for a in a_tags:
        texto_link = re.sub(r"\s{2,}", " ", a.get_text(" ", strip=True) or "").strip()
        if not texto_link:
            continue

        status_ref = _status_da_referencia(a)
        dispositivo_revogado = (status_dispositivo == STATUS_REVOGADO)

        tipo = _tipo_modificacao_por_texto(texto_link)

        # Prioridade: se o dispositivo ou a referência estiver revogado, a modificação deve ser REVOGACAO/REVOGADO, mesmo que o texto indique outro status.
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

def _normalizar_texto_para_json(texto: str) -> str:
    """
    Remove aspas do texto para evitar sequências \" no JSON gerado.
    """
    t = (texto or "")
    t = t.replace('"', "")
    t = t.replace("“", "").replace("”", "")
    return t


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
    print(f"Acessando: {url}")
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("Timeout ao aguardar o carregamento da página.")
    time.sleep(2)
    print(f"Página carregada: {driver.title}")
    return driver.page_source


# PARSER DO CONTEÚDO
class EstadoParser:

    def __init__(self) -> None:
        self.titulo_dict:   Optional[Dict] = None
        self.capitulo_dict: Optional[Dict] = None
        self.secao_dict:   Optional[Dict] = None
        self.subsecao_dict: Optional[Dict] = None
        self.artigo_dict:   Optional[Dict] = None
        self.paragrafo_dict: Optional[Dict] = None
        self.inciso_dict:   Optional[Dict] = None


    # Título
    def abrir_titulo(self, titulo: Dict):
        self.fechar_titulo()
        self.titulo_dict = titulo

    def fechar_titulo(self) -> Optional[Dict]:
        self.fechar_capitulo()
        t = self.titulo_dict
        if t:
            t.pop("_direto", None)
        self.titulo_dict = None
        return t


    # Capítulo
    def abrir_capitulo(self, capitulo: Dict):
        self.fechar_capitulo()
        self.capitulo_dict = capitulo

    def fechar_capitulo(self):
        self.fechar_secao()
        if self.capitulo_dict is not None and self.titulo_dict is not None:
            self.capitulo_dict.pop("_direto", None)
            self.titulo_dict["capitulos"].append(self.capitulo_dict)
        self.capitulo_dict = None
    

    # Seção
    def abrir_secao(self, secao: Dict):
        self.fechar_secao()
        self.secao_dict = secao

    def fechar_secao(self):
        self.fechar_subsecao()
        if self.secao_dict is not None and self.capitulo_dict is not None:
            self.secao_dict.pop("_direto", None)
            self.capitulo_dict["secoes"].append(self.secao_dict)
        self.secao_dict = None

    
    # Subseção
    def abrir_subsecao(self, subsecao: Dict):
        self.fechar_subsecao()
        self.subsecao_dict = subsecao

    def fechar_subsecao(self):
        self.fechar_artigo()
        if self.subsecao_dict is not None and self.secao_dict is not None:
            self.subsecao_dict.pop("_direto", None)
            self.secao_dict["subsecoes"].append(self.subsecao_dict)
        self.subsecao_dict = None


    # Artigo 
    def abrir_artigo(self, artigo: Dict):
        self.fechar_artigo()
        self.artigo_dict = artigo

    def fechar_artigo(self):
        self.fechar_paragrafo()
        if self.artigo_dict is None:
            return
        destino = self.subsecao_dict or self.secao_dict or self.capitulo_dict or self._capitulo_direto()
        if destino is not None:
            destino["artigos"].append(self.artigo_dict)
        self.artigo_dict = None

    def _capitulo_direto(self) -> Optional[Dict]:
        """Capítulo auxiliar para artigos sem capítulo definido."""
        if self.titulo_dict is None:
            return None
        caps = self.titulo_dict["capitulos"]
        if caps and caps[0].get("_direto"):
            return caps[0]
        cap = make_capitulo(capitulo="", descricao="")
        cap["_direto"] = True
        caps.insert(0, cap)
        return cap


    # Parágrafo 
    def abrir_paragrafo(self, paragrafo: Dict):
        self.fechar_paragrafo()
        self.paragrafo_dict = paragrafo

    def fechar_paragrafo(self):
        self.fechar_inciso()
        if self.paragrafo_dict is not None and self.artigo_dict is not None:
            self.artigo_dict["paragrafos"].append(self.paragrafo_dict)
        self.paragrafo_dict = None


    # Inciso
    def abrir_inciso(self, inciso: Dict):
        self.fechar_inciso()
        self.inciso_dict = inciso

    def fechar_inciso(self):
        if self.inciso_dict is None:
            return
        if self.paragrafo_dict is not None:
            self.paragrafo_dict["incisos"].append(self.inciso_dict)
        elif self.artigo_dict is not None:
            if "incisos_caput" not in self.artigo_dict:
                self.artigo_dict["incisos_caput"] = []
            self.artigo_dict["incisos_caput"].append(self.inciso_dict)
        self.inciso_dict = None


# PARSER PRINCIPAL
def parsear_constituicao(html: str) -> List[Dict]:
    """
    Faz o parsing do HTML e retorna lista de títulos
    no formato exato do schema estrutura_constituicao.json.
    """
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    body = soup.find("body")
    if not body:
        print("[!] Body não encontrado.")
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
        texto = re.sub(r'\s{2,}', ' ', texto)
        texto = _normalizar_texto_para_json(texto)
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
            coletando_preambulo = False
            titulo_fechado = estado.fechar_titulo()
            if titulo_fechado:
                titulos_resultado.append(titulo_fechado)

            num, desc = split_num_nome(texto, r'^(TÍTULO\s+[IVXLCDM]+)(.*)')
            novo_titulo = make_titulo(titulo=num, descricao=desc)
            estado.abrir_titulo(novo_titulo)
            if not desc.strip():
                aguardando_desc_titulo = True
            continue

        # Capítulo
        if detectar_capitulo(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(CAPÍTULO\s+[IVXLCDM]+)(.*)')
            estado.abrir_capitulo(make_capitulo(capitulo=num, descricao=desc))
            if not desc.strip():
                 aguardando_desc_capitulo = True
            continue

        # Seção
        if detectar_secao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)')
            estado.abrir_secao(make_secao(secao=num, descricao=desc))
            if not desc.strip():
                 aguardando_desc_secao = True
            continue

        # Subseção
        if detectar_subsecao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)')
            estado.abrir_subsecao(make_subsecao(subsecao=num, descricao=desc))
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
            partes = re.split(r'\s*[–\-]\s*', texto, maxsplit=1)
            num_i  = partes[0].strip()
            corpo  = partes[1].strip() if len(partes) > 1 else ""
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
            partes = re.split(r'(?<!\w)([a-z]\s*\))\s+', corpo)
            alineas_para_inserir = [(num_al, partes[0].strip())]
            for letra, seg in zip(partes[1::2], partes[2::2]):
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
            if alvo is not None:
                # Se estamos anexando a um dispositivo já aberto, o status do dispositivo tem prioridade para o status das referências.
                status_alvo = (
                    alvo.get("status_da_alinea")
                    or alvo.get("status_do_inciso")
                    or alvo.get("status_do_paragrafo")
                    or alvo.get("status_do_artigo")
                )
                if refs_no_elem:
                    alvo["referenciais_legislativos"].extend(
                        _forcar_status_em_referencias(refs_no_elem, status_alvo)
                    )
                if mods_no_elem:
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
    print(f"JSON salvo em: {caminho}")


# MAIN
def main():
    print("=" * 50)
    print("  Parser — Constituição Federal do Brasil")
    print("  Output: constituicao_schema.json")
    print("=" * 50)

    driver = criar_driver(headless=True)

    try:
        html = carregar_pagina(driver, BASE_URL)

        print("\n[+] Parsing estruturado...")
        dados = parsear_constituicao(html)

        salvar_json(dados, OUTPUT_JSON)

        print(f"\n Arquivo: {OUTPUT_JSON.resolve()}")

    finally:
        driver.quit()
        print("[+] Driver encerrado.")

    
if __name__ == "__main__":
    main()

