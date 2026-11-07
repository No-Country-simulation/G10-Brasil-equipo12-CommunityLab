# tests/test_faixa_relevancia.py
"""Testes da faixa Alta, Média ou Baixa por mensagem. Rodam offline."""
import json
import unittest
from pathlib import Path

from src.limpeza import limpar_dados_comunidade
from src.relevancia import (
    PISO_FAIXA_ALTA,
    PISO_FAIXA_MEDIA,
    calcular_pontuacao_interacao,
    faixa_da_interacao,
    faixa_relevancia,
)

RAIZ = Path(__file__).resolve().parents[1]


class TestFaixaRelevancia(unittest.TestCase):
    def test_cortes_da_regua(self):
        self.assertEqual(PISO_FAIXA_ALTA, 60)
        self.assertEqual(PISO_FAIXA_MEDIA, 25)

    def test_limites_entre_as_faixas(self):
        self.assertEqual(faixa_relevancia(0), "Baixa")
        self.assertEqual(faixa_relevancia(24), "Baixa")
        self.assertEqual(faixa_relevancia(25), "Média")
        self.assertEqual(faixa_relevancia(59), "Média")
        self.assertEqual(faixa_relevancia(60), "Alta")
        self.assertEqual(faixa_relevancia(100), "Alta")

    def test_faixa_da_interacao_usa_a_nota_da_mensagem(self):
        conversa = {"tipo": "interacao_geral", "texto": "Bom dia, pessoal"}  # 10 pontos
        duvida = {"tipo": "pergunta_tecnica", "texto": "Como faço isso?"}  # 25 pontos
        relato = {"tipo": "depoimento", "texto": "Fui contratada " + "x" * 100}  # 40 + 15 + 20
        self.assertEqual(faixa_da_interacao(conversa), "Baixa")
        self.assertEqual(faixa_da_interacao(duvida), "Média")
        self.assertEqual(faixa_da_interacao(relato), "Alta")

    def test_nao_altera_a_mensagem(self):
        msg = {"tipo": "depoimento", "texto": "Passei no processo seletivo"}
        faixa_da_interacao(msg)
        self.assertEqual(set(msg), {"tipo", "texto"})

    def test_casos_de_demo(self):
        # DEMO_04 (vazia) e DEMO_05 (repetida) saem na limpeza, então sobram 8 casos.
        esperadas = {
            "DEMO_01": "Alta",
            "DEMO_02": "Média",
            "DEMO_06": "Média",
            "DEMO_07": "Média",
            "DEMO_08": "Baixa",
            "DEMO_09": "Alta",
            "DEMO_10": "Média",
            # O gabarito (docs/resultados_esperados.md) diz "Média", mas feedback pontua 10 e cai
            # em "Baixa". Divergência conhecida, listada em "Pontos em aberto" da régua.
            "DEMO_03": "Baixa",
        }
        dados = json.loads((RAIZ / "dados" / "casos_demo.json").read_text(encoding="utf-8"))
        limpos = limpar_dados_comunidade(dados)["interacoes"]
        obtidas = {i["id"]: faixa_da_interacao(i) for i in limpos}
        self.assertEqual(obtidas, esperadas)

    def test_nota_e_faixa_andam_juntas(self):
        msg = {"tipo": "pergunta_tecnica", "texto": "Erro no deploy"}  # 25 + 15
        self.assertEqual(calcular_pontuacao_interacao(msg), 40)
        self.assertEqual(faixa_da_interacao(msg), "Média")


if __name__ == "__main__":
    unittest.main()
