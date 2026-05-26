import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parsers.detectores import (
    detectar_alinea,
    detectar_artigo,
    detectar_capitulo,
    detectar_inciso,
    detectar_paragrafo,
    detectar_secao,
    detectar_subsecao,
    detectar_titulo,
)


class DetectoresTest(unittest.TestCase):
    def test_detectores_estrutura(self) -> None:
        self.assertTrue(detectar_titulo("TÍTULO I"))
        self.assertTrue(detectar_capitulo("CAPÍTULO II"))
        self.assertTrue(detectar_secao("SEÇÃO I"))
        self.assertTrue(detectar_subsecao("SUBSEÇÃO I"))
        self.assertTrue(detectar_artigo("Art. 5º Todos são iguais"))
        self.assertTrue(detectar_paragrafo("§ 1º É livre"))
        self.assertTrue(detectar_inciso("I - fazer algo"))
        self.assertTrue(detectar_alinea("a) detalhe"))

    def test_detectores_negativos(self) -> None:
        self.assertFalse(detectar_titulo("PREÂMBULO"))
        self.assertFalse(detectar_artigo("Artigo sem padrão"))


if __name__ == "__main__":
    unittest.main()
