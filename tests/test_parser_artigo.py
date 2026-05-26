import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.constituicao_app import parsear_constituicao


HTML_MINIMO = """
<html>
  <body>
    <p>TÍTULO I</p>
    <p>DOS PRINCÍPIOS</p>
    <p>Art. 1º A República Federativa do Brasil.</p>
    <p>§ 1º Todo poder emana do povo.</p>
    <p>I - será exercido por representantes.</p>
    <p>a) na forma desta Constituição.</p>
  </body>
</html>
"""


class ParserArtigoTest(unittest.TestCase):
    def test_parsear_artigo_com_paragrafo_inciso_e_alinea(self) -> None:
        titulos = parsear_constituicao(HTML_MINIMO)
        self.assertGreaterEqual(len(titulos), 1)

        titulo = titulos[0]
        self.assertEqual(titulo["titulo"], "TÍTULO I")

        artigos = titulo.get("artigos", [])
        self.assertEqual(len(artigos), 1)

        artigo = artigos[0]
        self.assertTrue(artigo["numero_artigo"].startswith("Art."))
        self.assertEqual(len(artigo["paragrafos"]), 1)

        paragrafo = artigo["paragrafos"][0]
        self.assertEqual(len(paragrafo["incisos"]), 1)

        inciso = paragrafo["incisos"][0]
        self.assertEqual(len(inciso["alineas"]), 1)
        self.assertEqual(inciso["alineas"][0]["numero_alinea"], "a)")


if __name__ == "__main__":
    unittest.main()
