# tests/test_exemplos_demo.py
"""Garante que as entradas dos 3 exemplos de demonstração continuam congeladas.

Rodam offline (sem LLM). Se um destes testes falhar, as saídas registradas em
docs/exemplos_transformacao.md deixaram de corresponder às entradas.
"""
import json
import unittest
from pathlib import Path

from src.ingestao import ler_mensagens_comunidade
from src.roteamento import ativos_com_material

DADOS = Path(__file__).resolve().parent.parent / "dados"

# arquivo -> (ativos esperados pela rota, arquivo de origem dos textos)
EXEMPLOS = {
    "caso_conquista.json": (("post_linkedin", "destaque_newsletter_semanal"), "mensagens_exemplo.json"),
    "caso_proposta_estagio.json": (("post_linkedin", "destaque_newsletter_semanal"), "dataset_simulado.json"),
    "caso_duvida_tecnica.json": (("sugestao_conteudo_faq",), "dataset_simulado.json"),
}


def _carregar(nome: str) -> dict:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


class TestExemplosDemo(unittest.TestCase):
    def test_cada_exemplo_gera_so_os_ativos_esperados(self):
        for arquivo, (esperados, _) in EXEMPLOS.items():
            with self.subTest(arquivo=arquivo):
                lote = ler_mensagens_comunidade(str(DADOS / arquivo))
                self.assertEqual(ativos_com_material(lote["interacoes"]), esperados)

    def test_periodo_de_teste_nao_sobrescreve_semana_real(self):
        for arquivo in EXEMPLOS:
            with self.subTest(arquivo=arquivo):
                self.assertTrue(_carregar(arquivo)["periodo_referencia"].startswith("Semana_Teste"))

    def test_textos_sao_copias_exatas_da_origem(self):
        """Nenhuma mensagem do exemplo foi reescrita: o texto é igual ao do arquivo de origem."""
        for arquivo, (_, origem) in EXEMPLOS.items():
            textos_origem = {(i["autor"], i["texto"]) for i in _carregar(origem)["interacoes"]}
            for interacao in _carregar(arquivo)["interacoes"]:
                with self.subTest(arquivo=arquivo, autor=interacao["autor"]):
                    self.assertIn((interacao["autor"], interacao["texto"]), textos_origem)


if __name__ == "__main__":
    unittest.main()
