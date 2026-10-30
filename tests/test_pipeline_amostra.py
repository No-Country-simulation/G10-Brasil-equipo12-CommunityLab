# tests/test_pipeline_amostra.py
"""Testa o pipeline com um cliente de LLM falso: nenhuma chamada real, nenhuma chave."""
import json
import unittest

from src.pipeline import processar_lote
from src.relevancia import LIMITE_AMOSTRA_PADRAO
from tests.test_ia_service import ANALISE_VALIDA, ClienteFalso


def _lote(n_relatos, n_duvidas, n_outros):
    ints = []
    for i in range(n_relatos):
        ints.append({"id": f"R{i}", "autor": f"Autor R{i}", "canal": "#c", "tipo": "depoimento", "texto": f"Relato {i} fui contratada"})
    for i in range(n_duvidas):
        ints.append({"id": f"D{i}", "autor": f"Autor D{i}", "canal": "#c", "tipo": "pergunta_tecnica", "texto": f"Dúvida {i}?"})
    for i in range(n_outros):
        ints.append({"id": f"O{i}", "autor": f"Autor O{i}", "canal": "#c", "tipo": "interacao_geral", "texto": f"Conversa {i}"})
    return {"origem_comunidade": "Teste", "periodo_referencia": "Semana_Teste", "interacoes": ints}


def _ids_enviados(cliente):
    prompt_usuario = cliente.chamadas[0]["messages"][1]["content"]
    dados = json.loads(prompt_usuario.split("\n", 1)[1])
    return [i["id"] for i in dados["interacoes"]]


class TestPipelineAmostra(unittest.TestCase):
    def test_lote_pequeno_envia_tudo(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        r = processar_lote(_lote(2, 2, 2), pasta_saida=None, cliente_llm=cliente)
        self.assertEqual(len(_ids_enviados(cliente)), 6)
        self.assertEqual(r.resumo_comunidade.total_interacoes_processadas, 6)

    def test_lote_grande_envia_so_o_limite_padrao_mas_conta_o_lote_inteiro(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        r = processar_lote(_lote(12, 12, 6), pasta_saida=None, cliente_llm=cliente)
        enviados = _ids_enviados(cliente)
        self.assertEqual(len(enviados), LIMITE_AMOSTRA_PADRAO)
        self.assertEqual(r.resumo_comunidade.total_interacoes_processadas, 30)

    def test_duvidas_continuam_chegando_a_llm(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        processar_lote(_lote(25, 3, 0), pasta_saida=None, cliente_llm=cliente)
        self.assertTrue(any(i.startswith("D") for i in _ids_enviados(cliente)))

    def test_limite_personalizado(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        r = processar_lote(_lote(10, 10, 10), pasta_saida=None, limite_amostra=6, cliente_llm=cliente)
        self.assertEqual(len(_ids_enviados(cliente)), 6)
        self.assertEqual(r.resumo_comunidade.total_interacoes_processadas, 30)

    def test_sem_limite_envia_tudo(self):
        cliente = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        processar_lote(_lote(10, 10, 10), pasta_saida=None, limite_amostra=None, cliente_llm=cliente)
        self.assertEqual(len(_ids_enviados(cliente)), 30)

    def test_aviso_de_amostra_so_aparece_quando_reduz(self):
        with self.assertLogs("src.pipeline", level="WARNING") as ctx:
            processar_lote(_lote(12, 12, 6), pasta_saida=None, cliente_llm=ClienteFalso([json.dumps(ANALISE_VALIDA)]))
        self.assertIn(f"amostra de {LIMITE_AMOSTRA_PADRAO}", ctx.output[0])
        with self.assertNoLogs("src.pipeline", level="WARNING"):
            processar_lote(_lote(2, 2, 2), pasta_saida=None, cliente_llm=ClienteFalso([json.dumps(ANALISE_VALIDA)]))


if __name__ == "__main__":
    unittest.main()
