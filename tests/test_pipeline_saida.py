# tests/test_pipeline_saida.py
"""Garante que a saída do terminal não quebra com emojis quando é redirecionada (cp1252 no Windows)."""
import io
import sys
import unittest

from src.pipeline import _garantir_saida_utf8


class TestSaidaUtf8(unittest.TestCase):
    def test_imprime_emoji_mesmo_com_saida_em_cp1252(self):
        bruto, bruto_erro = io.BytesIO(), io.BytesIO()
        original = sys.stdout, sys.stderr
        sys.stdout = io.TextIOWrapper(bruto, encoding="cp1252")
        sys.stderr = io.TextIOWrapper(bruto_erro, encoding="cp1252")
        try:
            # sem a correção, esta linha levantaria UnicodeEncodeError
            _garantir_saida_utf8()
            print("Parabéns 🎉")
            print("❌ erro", file=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()
            self.assertEqual(bruto.getvalue().decode("utf-8").strip(), "Parabéns 🎉")
            self.assertIn("❌", bruto_erro.getvalue().decode("utf-8"))
        finally:
            sys.stdout, sys.stderr = original


if __name__ == "__main__":
    unittest.main()
