# tests/test_ia_service.py
"""Testes do serviço de LLM com um cliente falso: nenhuma chamada real, nenhuma chave."""
import json
import unittest
from types import SimpleNamespace

from src.ia_service import LEMBRETE_FINAL, ErroServicoLLM, analisar_lote
from src.validacao import ErroAnaliseLLM

ANALISE_VALIDA = {
    "sentimento_predominante": "Positivo",
    "topicos_principais": ["estágio"],
    "ativos_distribuicao_gerados": {"post_linkedin": None, "destaque_newsletter": None, "sugestao_faq": None},
}


class ClienteFalso:
    """Devolve as respostas da lista, uma por chamada, e guarda as mensagens recebidas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        item = self.respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=item))])


DADOS = {"interacoes": [{"id": "1", "texto": "oi", "tipo": "interacao_geral"}]}


class TestAnalisarLote(unittest.TestCase):
    def test_resposta_valida(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        analise = analisar_lote(DADOS, cliente=cliente)
        self.assertEqual(analise.sentimento_predominante, "Positivo")

    def test_system_prompt_leva_os_guias_e_o_lembrete_final(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        analisar_lote(DADOS, cliente=cliente)
        system = cliente.chamadas[0]["messages"][0]["content"]
        for marca in ("[GUIA LINKEDIN]", "[GUIA NEWSLETTER]", "[GUIA FAQ]", "Regras de Fidelidade"):
            self.assertIn(marca, system)
        self.assertTrue(system.rstrip().endswith(LEMBRETE_FINAL))

    def test_tenta_de_novo_e_informa_o_motivo(self):
        cliente = ClienteFalso(["isto não é json", json.dumps(ANALISE_VALIDA)])
        analisar_lote(DADOS, cliente=cliente)
        self.assertEqual(len(cliente.chamadas), 2)
        self.assertIn("Motivo da recusa", cliente.chamadas[1]["messages"][1]["content"])

    def test_esgota_as_tentativas_sem_inventar_resultado(self):
        cliente = ClienteFalso(["lixo", "lixo", "lixo"])
        with self.assertRaises(ErroAnaliseLLM):
            analisar_lote(DADOS, tentativas=3, cliente=cliente)
        self.assertEqual(len(cliente.chamadas), 3)

    def test_erro_da_api_vira_erro_do_servico(self):
        cliente = ClienteFalso([RuntimeError("sem rede")])
        with self.assertRaises(ErroServicoLLM):
            analisar_lote(DADOS, cliente=cliente)


if __name__ == "__main__":
    unittest.main()
