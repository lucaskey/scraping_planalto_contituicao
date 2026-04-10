import time
import json
from pathlib import Path

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


def carregar_pagina(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("Timeout ao aguarrdar o carregamento da página.")
    time.sleep(2)
    print(f"Página carregada: {driver.title}")
    return driver.page_source


def parsear_conteudo(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")  



def salvar_json(dados: dict, caminho: Path) -> none:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"JSON salvo em: {caminho}")

    
def main():
    driver = criar_driver(headless=True)
    try:
        html = carregar_pagina(driver, URL)
        dados = parsear_conteudo(html)
        salvar_json(dados, OUTPUT_DIR / "constituicao.json")
        print(f"Concluído! Arquivo em: {OUTPUT_DIR.resolve()}")
    finally:
        driver.quit()
        print("Driver encerrado.")
    
if __name__ == "__main__":
    main()

