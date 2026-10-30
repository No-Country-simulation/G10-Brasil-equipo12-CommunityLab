# tests/test_amostra.py
"""Testes da seleção de amostra por relevância e por tipo. Rodam offline."""
import unittest

from src.relevancia import LIMITE_AMOSTRA_PADRAO, _cotas, selecionar_amostra


def _m(id_, tipo, texto="x"):
    return {"id": id_, "autor": "Ana", "canal": "#c", "tipo": tipo, "texto": texto}


def _lote_grande():
    relatos = [_m(f"R{i}", "depoimento", "Fui contratada " + "x" * i) for i in range(10)]
    duvidas = [_m(f"D{i}", "pergunta_tecnica", "Como fazer? " + "x" * i) for i in range(10)]
    outros = [_m(f"O{i}", "interacao_geral", "Bom dia " + "x" * i) for i in range(10)]
    return relatos + duvidas + outros  # 30 mensagens


class TestSelecionarAmostra(unittest.TestCase):
    def test_limite_padrao_e_10(self):
        self.assertEqual(LIMITE_AMOSTRA_PADRAO, 10)

    def test_lote_pequeno_vai_inteiro_e_ordenado(self):
        lote = [_m("1", "interacao_geral"), _m("2", "depoimento", "fui contratada")]
        r = selecionar_amostra(lote, 15)
        self.assertEqual([i["id"] for i in r], ["2", "1"])

    def test_lote_grande_e_reduzido_ao_limite(self):
        self.assertEqual(len(selecionar_amostra(_lote_grande(), 15)), 15)

    def test_nenhum_tipo_fica_de_fora(self):
        ids = {i["id"][0] for i in selecionar_amostra(_lote_grande(), 15)}
        self.assertEqual(ids, {"R", "D", "O"})

    def test_limite_padrao_divide_5_relatos_3_duvidas_2_outros(self):
        r = selecionar_amostra(_lote_grande())
        contagem = {letra: sum(1 for i in r if i["id"][0] == letra) for letra in "RDO"}
        self.assertEqual(contagem, {"R": 5, "D": 3, "O": 2})

    def test_cotas_somam_o_limite_e_respeitam_os_pesos(self):
        self.assertEqual(_cotas(10), {"relatos": 5, "duvidas": 3, "outros": 2})
        for limite in range(1, 40):
            self.assertEqual(sum(_cotas(limite).values()), limite)
        # com pelo menos 3 vagas, nenhum grupo fica com zero
        for limite in range(3, 40):
            self.assertTrue(all(c >= 1 for c in _cotas(limite).values()), limite)

    def test_sobra_de_grupo_pequeno_vai_para_os_outros_grupos(self):
        lote = [_m("D0", "pergunta_tecnica")] + [_m(f"R{i}", "depoimento") for i in range(20)]
        r = selecionar_amostra(lote)
        self.assertEqual(len(r), 10)
        self.assertEqual(sum(1 for i in r if i["id"].startswith("R")), 9)

    def test_grupo_pequeno_nao_rouba_vaga_dos_outros(self):
        lote = [_m("D0", "pergunta_tecnica")] + [_m(f"R{i}", "depoimento") for i in range(20)]
        r = selecionar_amostra(lote, 10)
        self.assertEqual(len(r), 10)
        self.assertIn("D0", [i["id"] for i in r])

    def test_escolhe_as_mais_relevantes_dentro_do_grupo(self):
        r = selecionar_amostra(_lote_grande())
        ids_relatos = {i["id"] for i in r if i["id"].startswith("R")}
        self.assertEqual(len(ids_relatos), 5)
        # todos os relatos têm a mesma base; os mais longos pontuam mais ou igual: confere a ordem final
        pontos = [i["pontuacao_relevancia"] for i in r]
        self.assertEqual(pontos, sorted(pontos, reverse=True))

    def test_limite_none_ou_zero_manda_tudo(self):
        self.assertEqual(len(selecionar_amostra(_lote_grande(), None)), 30)
        self.assertEqual(len(selecionar_amostra(_lote_grande(), 0)), 30)

    def test_e_deterministico(self):
        a = [i["id"] for i in selecionar_amostra(_lote_grande(), 15)]
        b = [i["id"] for i in selecionar_amostra(_lote_grande(), 15)]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
