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

    def test_guias_de_linkedin_e_newsletter_trazem_a_regra_de_nao_trocar_o_que_foi_compartilhado(self):
        for canal in ("linkedin", "newsletter"):
            with self.subTest(canal=canal):
                guia = carregar_guia_prompt(canal)
                self.assertIn("Não troque o que foi compartilhado por algo maior", guia)
                self.assertIn("Use verbos fiéis ao resultado", guia)

    def test_guias_proibem_atribuir_causas_que_a_pessoa_nao_disse(self):
        for canal in ("linkedin", "newsletter"):
            with self.subTest(canal=canal):
                self.assertIn("Não atribua à pessoa", carregar_guia_prompt(canal))

    def test_guia_da_newsletter_pede_chamada_com_uma_so_vitoria(self):
        self.assertIn("A chamada trata de uma só vitória", carregar_guia_prompt("newsletter"))

    def test_nome_invalido_e_recusado(self):
        for nome in ("../README", "", None, "Linkedin", "a/b"):
            with self.subTest(nome=nome):
                with self.assertRaises(ValueError):
                    carregar_guia_prompt(nome)


if __name__ == "__main__":
    unittest.main()
