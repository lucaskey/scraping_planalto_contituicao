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


URL = "https://www.planalto.gov.br/ccivil_03/Constituicao/Constituicao.htm"
OUTPUT_DIR = Path("output_constituicao")
OUTPUT_DIR.mkdir(exist_ok=True)

# STATUS DA MODIFICAÇÃO
STATUS_VIGENTE        = "VIGENTE"
STATUS_REVOGADO       = "REVOGADO"
STATUS_SUSPENSO       = "SUSPENSO"
STATUS_REDACAO_ANTIGA = "REDACAO_ANTIGA"

# TIPO DE MODIFICAÇÃO
TIPO_INCLUSAO  = "INCLUSAO"
TIPO_ALTERACAO = "ALTERACAO"
TIPO_REVOGACAO = "REVOGACAO"
TIPO_ADICAO    = "ADICAO"

# TIPO DE REFERÊNCIA
TIPO_REF_LEI       = "LEI"
TIPO_REF_DECRETO   = "DECRETO"
TIPO_REF_RESOLUCAO = "RESOLUCAO"
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
        "tipo_de_modificacao": "INCLUSAO | ALTERACAO | REVOGACAO | ADICAO",
        "descricao_da_modificacao": "...",
        "texto_antigo_descontinuado": "...",
        "status_da_modificacao": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA"
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
        "tipo_de_referencia": "LEI | DECRETO | RESOLUCAO | OUTRO",
        "texto_da_referencia": "...",
        "status_da_modificacao": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA"
    }
    """
    return {
        "id_referencia": gerar_id(),
        "numero_referencia": numero,
        "tipo_de_referencia": tipo,
        "texto_da_referencia": texto,
        "status_da_referencia": status,
    }


# TITULOS
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
        "artigos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "capitulo": capitulo,
        "descricao_do_capitulo": descricao.upper(),
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
        "status_do_artigo": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA",
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


# PARAGRAFOS
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
        "status_do_paragrafo": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA",
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
        "status_do_inciso": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA",
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
        "status_da_alinea": "VIGENTE | REVOGADO | SUSPENSO | REDACAO_ANTIGA",
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
    return bool(re.match(r'^[IVXLCDM]{1,5}\s*[–\-]\s+', t.strip()))

def detectar_alinea(t: str) -> bool:    
    return bool(re.match(r'^[a-zA-Z]\)', t.strip()))  

def split_num_nome(t: str, pattern: str) -> tuple[str, str]:
    match = re.match(pattern, t.strip(), re.IGNORECASE)
    if match:
        num = match.group(1).strip()
        nome = t.strip()[len(match.group(0)):].strip()
        nome = re.sub(r'^[-–:\s]+', '', nome)
        return num, nome
    return t.strip(), ""


# CRIAR DRIVER
def criar_driver (headless: bool = False) -> webdriver.Crhome:
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


# PARSER DE CONTEÚDO
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
        self.fechar_artigo()
        if self.capitulo_dict is not None and self.titulo_dict is not None:
            self.capitulo_dict.pop("_direto", None)
            self.titulo_dict["capitulos"].append(self.capitulo_dict)
        self.capitulo_dict = None
    

    # Seção
    def abrir_secao(self, secao: Dict):
        self.fechar_secao()
        self.capitulo_dict = secao

    def fechar_secao(self):
        self.fechar_artigo()
        if self.capitulo_dict is not None and self.titulo_dict is not None:
            self.capitulo_dict.pop("_direto", None)
            self.titulo_dict["capitulos"].append(self.capitulo_dict)
        self.capitulo_dict = None

    
    # Subseção
    def abrir_subsecao(self, subsecao: Dict):
        self.fechar_subsecao()
        self.capitulo_dict = subsecao

    def fechar_subsecao(self):
        self.fechar_artigo()
        if self.capitulo_dict is not None and self.titulo_dict is not None:
            self.capitulo_dict.pop("_direto", None)
            self.titulo_dict["capitulos"].append(self.capitulo_dict)
        self.capitulo_dict = None


    # Artigo 
    def abrir_artigo(self, artigo: Dict):
        self.fechar_artigo()
        self.artigo_dict = artigo

    def fechar_artigo(self):
        self.fechar_paragrafo()
        if self.artigo_dict is None:
            return
        destino = self.capitulo_dict or self._capitulo_direto()
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
        if not texto or len(texto) < 2:
            continue

        texto_upper = texto.upper().strip()

        # ── Marcador de preâmbulo
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
            if estado.capitulo_dict is not None:
                estado.capitulo_dict["descricao_da_secao"] = texto.upper()
            continue    

        if aguardando_desc_subsecao:
            aguardando_desc_subsecao = False
            if estado.capitulo_dict is not None:
                estado.capitulo_dict["descricao_da_subsecao"] = texto.upper()
            continue

        # TÍTULO
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
            print(f"  [TÍTULO]   {num} — {desc[:55]}")
            continue

        # CAPÍTULO
        if detectar_capitulo(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(CAPÍTULO\s+[IVXLCDM]+)(.*)')
            estado.abrir_capitulo(make_capitulo(capitulo=num, descricao=desc))
            if not desc.strip():
                 aguardando_desc_capitulo = True
            print(f"    [CAP]    {num} — {desc[:50]}")
            continue

        # SEÇÃO
        if detectar_secao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)')
            estado.abrir_secao(make_secao(secao=num, descricao=desc))
            if not desc.strip():
                 aguardando_desc_secao = True
            print(f"      [SEC]  {num} — {desc[:48]}")
            continue

        # SUBSEÇÃO
        if detectar_subsecao(texto):
            coletando_preambulo = False
            num, desc = split_num_nome(texto, r'^(SUBSE[CÇ][AÃ]O\s+[IVXLCDM]+)(.*)')
            estado.abrir_subsecao(make_subsecao(subsecao=num, descricao=desc))
            if not desc.strip():
                 aguardando_desc_subsecao = True
            print(f"        [SUBSEC]  {num} — {desc[:45]}")
            continue

        # ARTIGO
        if detectar_artigo(texto):
            coletando_preambulo = False
            match = re.match(r'^(Art\.\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*)', texto, re.IGNORECASE)
            num_a  = match.group(1).strip() if match else texto[:25]
            caput  = texto[len(num_a):].strip() if match else texto
            estado.abrir_artigo(make_artigo(numero=num_a, caput=caput))
            continue

        # PARÁGRAFO 
        if detectar_paragrafo(texto) and estado.artigo_dict:
            # match = re.match(r'^(§\s*\d+\s*?\.?[ºo]?\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)', texto, re.IGNORECASE)
            match = re.match(r'^(§\s*\d+[ºo°]?(?:[–\-][A-Z])?\s*\.?\s*[-–]?\s*|Parágrafo\s+único\.?\s*[-–]?\s*)', texto, re.IGNORECASE)

            num_p  = match.group(1).strip() if match else "§"
            corpo  = texto[len(num_p):].strip() if match else texto
            estado.abrir_paragrafo(make_paragrafo(numero=num_p, texto=corpo))
            continue

        # INCISO
        if detectar_inciso(texto) and estado.artigo_dict:
            partes = re.split(r'\s*[–\-]\s*', texto, maxsplit=1)
            num_i  = partes[0].strip()
            corpo  = partes[1].strip() if len(partes) > 1 else ""
            estado.abrir_inciso(make_inciso(numero=num_i, texto=corpo))
            continue

        # ALÍNEA 
        if detectar_alinea(texto) and estado.inciso_dict:
            match  = re.match(r'^([a-z]\))\s*', texto)
            num_al = match.group(1).strip() if match else "a)"
            corpo  = texto[len(num_al):].strip() if match else texto
            estado.inciso_dict["alineas"].append(
                make_alinea(numero=num_al, texto=corpo)
            )
            continue

        # Texto livre / preâmbulo → ignora
        if coletando_preambulo:
            continue

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
    print("  Output: formato constituicao_schema.json")
    print("=" * 50)

    driver = criar_driver(headless=True)

    try:
        html = carregar_pagina(driver, URL)

        with open(OUTPUT_DIR / "constituicao_bruto.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("[+] HTML bruto salvo.")

        print("\n[+] Parsing estruturado...")
        dados = parsear_constituicao(html)

        salvar_json(dados, OUTPUT_DIR / "constituicao_schema7.json")

        print(f"\n Arquivo: {(OUTPUT_DIR / 'constituicao_schema7.json').resolve()}")

    finally:
        driver.quit()
        print("[+] Driver encerrado.")

    
if __name__ == "__main__":
    main()

