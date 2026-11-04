# tests/test_limpeza.py
"""Testes da limpeza dos dados. Rodam offline, sem chave de API."""
import json
import unittest
from pathlib import Path

from src.limpeza import anonimizar_conversas_gerais, limpar_dados_comunidade

RAIZ = Path(__file__).resolve().parents[1]


def _lote(*interacoes):
    return {"origem_comunidade": "Teste", "periodo_referencia": "Semana_Teste", "interacoes": list(interacoes)}


def _msg(id_, autor="Ana", canal="#geral", texto="Oi", tipo="interacao_geral"):
    return {"id": id_, "autor": autor, "canal": canal, "tipo": tipo, "texto": texto}


class TestLimpeza(unittest.TestCase):
    def test_remove_mensagem_vazia(self):
        r = limpar_dados_comunidade(_lote(_msg("1", texto="   "), _msg("2", texto="Olá")))
        self.assertEqual([i["id"] for i in r["interacoes"]], ["2"])

    def test_padroniza_espacos_e_quebras(self):
        r = limpar_dados_comunidade(_lote(_msg("1", texto="  Olá \n\n  pessoal  ")))
        self.assertEqual(r["interacoes"][0]["texto"], "Olá pessoal")


class TestDuplicatas(unittest.TestCase):
    def test_remove_duplicata_e_mantem_a_primeira(self):
        r = limpar_dados_comunidade(_lote(_msg("1", texto="Bom dia!"), _msg("2", texto="Bom dia!")))
        self.assertEqual([i["id"] for i in r["interacoes"]], ["1"])

    def test_diferenca_de_espaco_e_maiuscula_ainda_e_duplicata(self):
        r = limpar_dados_comunidade(_lote(_msg("1", texto="Bom dia!"), _msg("2", texto="  bom   DIA! ")))
        self.assertEqual(len(r["interacoes"]), 1)

    def test_mesmo_texto_de_autores_diferentes_nao_e_duplicata(self):
        r = limpar_dados_comunidade(_lote(_msg("1", autor="Ana"), _msg("2", autor="Bia")))
        self.assertEqual(len(r["interacoes"]), 2)

    def test_mesmo_texto_em_canais_diferentes_nao_e_duplicata(self):
        r = limpar_dados_comunidade(_lote(_msg("1", canal="#geral"), _msg("2", canal="#duvidas")))
        self.assertEqual(len(r["interacoes"]), 2)

    def test_mantem_a_ordem_original(self):
        r = limpar_dados_comunidade(
            _lote(_msg("1", texto="A"), _msg("2", texto="B"), _msg("3", texto="A"), _msg("4", texto="C"))
        )
        self.assertEqual([i["id"] for i in r["interacoes"]], ["1", "2", "4"])

    def test_nao_altera_o_lote_de_entrada(self):
        lote = _lote(_msg("1"), _msg("2"))
        limpar_dados_comunidade(lote)
        self.assertEqual(len(lote["interacoes"]), 2)

    def test_dados_de_demonstracao(self):
        dados = json.loads((RAIZ / "dados" / "casos_demo.json").read_text(encoding="utf-8"))
        ids = [i["id"] for i in limpar_dados_comunidade(dados)["interacoes"]]
        self.assertIn("DEMO_02", ids)       # a original fica
        self.assertNotIn("DEMO_05", ids)    # a repetida sai
        self.assertNotIn("DEMO_04", ids)    # a vazia sai

    def test_dataset_simulado(self):
        dados = json.loads((RAIZ / "dados" / "dataset_simulado.json").read_text(encoding="utf-8"))
        ids = [i["id"] for i in limpar_dados_comunidade(dados)["interacoes"]]
        for mantida in ("MSG_004", "MSG_009"):
            self.assertIn(mantida, ids)
        for removida in ("MSG_020", "MSG_035"):
            self.assertNotIn(removida, ids)


class TestAnonimizarConversasGerais(unittest.TestCase):
    def test_interacao_geral_vira_participante_e_os_outros_tipos_mantem_o_autor(self):
        entrada = [
            _msg("1", autor="Larissa Quintela", tipo="interacao_geral"),
            _msg("2", autor="Paulo Neves", tipo="depoimento"),
            _msg("3", autor="Heitor Salgado", tipo="feedback"),
            _msg("4", autor="Ana Souza", tipo="pergunta_tecnica"),
        ]
        autores = {i["id"]: i["autor"] for i in anonimizar_conversas_gerais(entrada)}
        self.assertEqual(
            autores,
            {"1": "Participante", "2": "Paulo Neves", "3": "Heitor Salgado", "4": "Ana Souza"},
        )

    def test_nao_altera_a_lista_original(self):
        entrada = [_msg("1", autor="Larissa Quintela", tipo="interacao_geral")]
        anonimizar_conversas_gerais(entrada)
        self.assertEqual(entrada[0]["autor"], "Larissa Quintela")

    def test_mantem_os_outros_campos(self):
        entrada = [_msg("1", autor="Larissa Quintela", canal="#geral", texto="Estou desanimada", tipo="interacao_geral")]
        r = anonimizar_conversas_gerais(entrada)[0]
        self.assertEqual((r["id"], r["canal"], r["tipo"], r["texto"]), ("1", "#geral", "interacao_geral", "Estou desanimada"))

    def test_tipo_com_maiuscula_ou_espaco_tambem_e_anonimizado(self):
        r = anonimizar_conversas_gerais([_msg("1", autor="Larissa Quintela", tipo=" Interacao_Geral ")])
        self.assertEqual(r[0]["autor"], "Participante")


if __name__ == "__main__":
    unittest.main()
