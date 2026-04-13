import time
import json
import uuid
from pathlib import Path
from typing import Any, Dict

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
    tipo: str = None,
    descricao: str = "",
    texto_antigo: str = "",
    status: str = None,
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
        "texto_antigo_ddescontinuado": texto_antigo,
        "status_da_modificacao": status,
    }


# REFERENCIAIS LEGISLATIVOS
def make_referencial_legislativo(
    numero: str = "",
    tipo: str = None,
    texto: str = "",
    status: str = None,
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
        "descricao_do_titulo": descricao,
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
        "descricao_titulo": "...",
        "artigos": [...]
    }
    """
    return{
        "id_dispositivo_legislativo": gerar_id(),
        "capitulo": capitulo,
        "descricao_capitulo": descricao,
        "artigos": [],
    }

# ARTIGOS
def make_artigo(
    numero: str = "",
    caput: str = "",
    status: str = None,
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
        "id_dispositivo_leislativo": gerar_id(),
        "numero_referencia": numero,
        "caput": caput,
        "status_do_artigo": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "paragrafos": [],
    }


# PARAGRAFOS
def make_paragrafo(
    numero: str = "",
    texto: str = "",
    status: str = None,
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
        "texto_paragrafo": texto,
        "status_paragrafo": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "incisos": [],
    }


# INCISO
def make_inciso(
    numero: str = "",
    texto: str = "",
    status: str = None,
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
        "texto_inciso": texto,
        "status_do_inciso": status,
        "referenciais_legislativos": [],
        "modificacoes_historicas": [],
        "alineas": [],
    }


# ALINEA
def make_alinea(
    numero: str = "",
    texto: str = "",
    status: str = None,
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
        print("Timeout ao aguarrdar o carregamento da página.")
    time.sleep(2)
    print(f"Página carregada: {driver.title}")
    return driver.page_source


# SALVAR DADOS EM JSON
def salvar_json(dados: dict, caminho: Path) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"JSON salvo em: {caminho}")


# MAIN
def main():
    driver = criar_driver(headless=True)
    try:
        html = carregar_pagina(driver, URL)
        # dados = parsear_conteudo(html)
        salvar_json(dados, OUTPUT_DIR / "constituicao.json")
        print(f"Concluído! Arquivo em: {OUTPUT_DIR.resolve()}")
    finally:
        driver.quit()
        print("Driver encerrado.")
    
if __name__ == "__main__":
    main()

