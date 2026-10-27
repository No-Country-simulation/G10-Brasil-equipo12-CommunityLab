# tests/test_relevancia.py
"""Testes da pontuação de relevância. Rodam offline, sem chave de API."""
import unittest

from src.relevancia import calcular_pontuacao_interacao, filtrar_e_ordenar_por_relevancia


class TestPontuacao(unittest.TestCase):
    def test_conversa_comum_recebe_so_a_base(self):
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "interacao_geral", "texto": "bom dia, pessoal"}), 10)

    def test_palavra_chave_nao_casa_dentro_de_outra_palavra(self):
        # "devagar" contém "vaga", mas não é a palavra "vaga"
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "interacao_geral", "texto": "vou devagar"}), 10)

    def test_acento_nao_muda_a_pontuacao(self):
        com = calcular_pontuacao_interacao({"tipo": "interacao_geral", "texto": "consegui um estágio"})
        sem = calcular_pontuacao_interacao({"tipo": "interacao_geral", "texto": "consegui um estagio"})
        self.assertEqual(com, sem)
        self.assertEqual(com, 25)

    def test_maiusculas_nao_mudam_a_pontuacao(self):
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "interacao_geral", "texto": "ESTÁGIO"}), 25)

    def test_entrega_de_projeto_e_tratada_como_relato_de_valor(self):
        self.assertEqual(
            calcular_pontuacao_interacao({"tipo": "entrega_projeto", "texto": "Fiz o deploy do projeto"}), 70
        )

    def test_texto_longo_so_bonifica_relato(self):
        longo = "x" * 150
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "pergunta_tecnica", "texto": longo}), 25)
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "depoimento", "texto": longo}), 60)

    def test_teto_de_100(self):
        texto = "contratada estágio vaga aprovada freela projeto deploy emprego " + "x" * 150
        self.assertEqual(calcular_pontuacao_interacao({"tipo": "depoimento", "texto": texto}), 100)

    def test_campos_ausentes_ou_nulos_nao_quebram(self):
        self.assertEqual(calcular_pontuacao_interacao({}), 10)
        self.assertEqual(calcular_pontuacao_interacao({"tipo": None, "texto": None}), 10)


class TestOrdenacao(unittest.TestCase):
    def setUp(self):
        self.lote = [
            {"id": "A", "tipo": "interacao_geral", "texto": "oi"},
            {"id": "B", "tipo": "depoimento", "texto": "fui contratada"},
            {"id": "C", "tipo": "interacao_geral", "texto": "olá"},
        ]

    def test_devolve_todas_por_padrao_e_ordena(self):
        r = filtrar_e_ordenar_por_relevancia(self.lote)
        self.assertEqual(len(r), 3)
        self.assertEqual(r[0]["id"], "B")

    def test_empate_mantem_a_ordem_original(self):
        r = filtrar_e_ordenar_por_relevancia(self.lote)
        self.assertEqual([x["id"] for x in r], ["B", "A", "C"])

    def test_limite_so_corta_quando_pedido(self):
        self.assertEqual(len(filtrar_e_ordenar_por_relevancia(self.lote, limite=2)), 2)

    def test_nao_altera_a_lista_original(self):
        filtrar_e_ordenar_por_relevancia(self.lote)
        self.assertNotIn("pontuacao_relevancia", self.lote[0])


if __name__ == "__main__":
    unittest.main()
