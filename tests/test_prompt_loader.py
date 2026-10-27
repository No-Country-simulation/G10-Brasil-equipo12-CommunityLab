# tests/test_prompt_loader.py
"""Testes do carregador de guias de tom de voz (pasta /prompts)."""
import unittest

from src.utils.prompt_loader import carregar_guia_prompt


class TestPromptLoader(unittest.TestCase):
    def test_carrega_os_tres_guias_reais(self):
        for canal in ("linkedin", "newsletter", "faq"):
            with self.subTest(canal=canal):
                texto = carregar_guia_prompt(canal)
                self.assertIn("Regras de Fidelidade", texto)

    def test_nome_invalido_e_recusado(self):
        for nome in ("../README", "", None, "Linkedin", "a/b"):
            with self.subTest(nome=nome):
                with self.assertRaises(ValueError):
                    carregar_guia_prompt(nome)


if __name__ == "__main__":
    unittest.main()
