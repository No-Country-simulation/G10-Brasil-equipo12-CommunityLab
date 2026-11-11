# tests/test_anonimizar_pessoas.py
"""Testes de quem não autorizou o nome (src/interface_logica.py). Rodam offline, sem Streamlit e sem chave de API."""
import copy
import json
import unittest

from src import interface_logica as il
from tests.test_ia_service import ClienteFalso
from tests.test_interface_logica import _EmPastaTemporaria

LOTE = {
    "origem_comunidade": "Teste",
    "periodo_referencia": "Semana_Teste_B",
    "interacoes": [
        {"id": "1", "autor": "Mariana Souza", "canal": "#c", "tipo": "depoimento", "texto": "Fui aprovada! Obrigada, Rafael Lima."},
        {"id": "2", "autor": "Rafael Lima", "canal": "#p", "tipo": "entrega_projeto", "texto": "Mariana me ajudou no deploy. Mariana é demais."},
        {"id": "3", "autor": "Rafael Tavares", "canal": "#d", "tipo": "pergunta_tecnica", "texto": "Como faço o retry no LangGraph?"},
    ],
}


def _autores(lote):
    return [i["autor"] for i in lote["interacoes"]]


class TestAutoresDoLote(unittest.TestCase):
    def test_sem_repetir_e_sem_participante(self):
        lote = {"interacoes": [{"autor": "Ana Teste"}, {"autor": "Ana Teste"}, {"autor": "Participante"}, {"autor": ""}, {"autor": "Bia Teste"}]}
        self.assertEqual(il.autores_do_lote(lote), ["Ana Teste", "Bia Teste"])


class TestAnonimizar(unittest.TestCase):
    def test_sem_ninguem_marcado_nada_muda(self):
        novo, relatorio = il.anonimizar_pessoas(LOTE, [])
        self.assertEqual(novo, LOTE)
        self.assertEqual(relatorio, [])

    def test_nome_que_nao_esta_no_lote_e_ignorado(self):
        novo, relatorio = il.anonimizar_pessoas(LOTE, ["Fulana de Tal"])
        self.assertEqual(novo, LOTE)
        self.assertEqual(relatorio, [])

    def test_nao_altera_o_lote_recebido(self):
        original = copy.deepcopy(LOTE)
        il.anonimizar_pessoas(LOTE, ["Mariana Souza"])
        self.assertEqual(LOTE, original)

    def test_troca_autor_e_nome_nos_textos_de_todos(self):
        novo, relatorio = il.anonimizar_pessoas(LOTE, ["Mariana Souza"])
        self.assertEqual(novo["interacoes"][0]["autor"], "uma pessoa da comunidade")
        self.assertEqual(novo["interacoes"][1]["texto"], "Uma pessoa da comunidade me ajudou no deploy. Uma pessoa da comunidade é demais.")
        self.assertEqual(relatorio[0]["mensagens"], 1)
        self.assertEqual(relatorio[0]["citacoes"], 2)

    def test_quem_autorizou_nao_e_tocado(self):
        novo, _ = il.anonimizar_pessoas(LOTE, ["Mariana Souza"])
        self.assertEqual(novo["interacoes"][1]["autor"], "Rafael Lima")
        self.assertIn("Rafael Lima", novo["interacoes"][0]["texto"])

    def test_sem_acento_e_sem_maiuscula(self):
        lote = {"interacoes": [{"autor": "José Álvaro", "tipo": "depoimento", "texto": "obrigado, JOSE ALVARO!"}, {"autor": "Bia Teste", "tipo": "depoimento", "texto": "Parabéns José Álvaro"}]}
        novo, _ = il.anonimizar_pessoas(lote, ["José Álvaro"])
        self.assertNotIn("lvaro", novo["interacoes"][0]["texto"])
        self.assertNotIn("lvaro", novo["interacoes"][1]["texto"])

    def test_palavra_inteira(self):
        lote = {"interacoes": [{"autor": "Ana Souza", "tipo": "depoimento", "texto": "Comi banana. Ana chegou."}]}
        novo, _ = il.anonimizar_pessoas(lote, ["Ana Souza"])
        self.assertIn("banana", novo["interacoes"][0]["texto"])
        self.assertNotIn("Ana chegou", novo["interacoes"][0]["texto"])

    def test_maiuscula_so_no_comeco_da_frase(self):
        lote = {"interacoes": [{"autor": "Ana Souza", "tipo": "depoimento", "texto": "Obrigada à Ana Souza! Ana Souza ajudou."}]}
        novo, _ = il.anonimizar_pessoas(lote, ["Ana Souza"])
        self.assertEqual(novo["interacoes"][0]["texto"], "Obrigada à uma pessoa da comunidade! Uma pessoa da comunidade ajudou.")

    def test_duas_pessoas_com_rotulos_diferentes(self):
        novo, relatorio = il.anonimizar_pessoas(LOTE, ["Mariana Souza", "Rafael Lima"])
        self.assertEqual(_autores(novo)[:2], ["uma pessoa da comunidade", "outra pessoa da comunidade"])
        self.assertEqual([r["rotulo"] for r in relatorio], ["uma pessoa da comunidade", "outra pessoa da comunidade"])

    def test_quem_so_fez_pergunta_vira_participante(self):
        # O motor ignora "Participante" na checagem de nomes protegidos. Um rótulo como "uma pessoa da
        # comunidade" viraria o "primeiro nome" 'uma' e derrubaria os textos.
        novo, _ = il.anonimizar_pessoas(LOTE, ["Rafael Tavares"])
        self.assertEqual(novo["interacoes"][2]["autor"], "Participante")

    def test_primeiro_nome_repetido_so_troca_o_nome_completo(self):
        lote = {"interacoes": [
            {"autor": "Rafael Lima", "tipo": "depoimento", "texto": "Oi, sou o Rafael."},
            {"autor": "Rafael Tavares", "tipo": "depoimento", "texto": "Oi, sou o Rafael Tavares. Rafael aqui."},
        ]}
        novo, relatorio = il.anonimizar_pessoas(lote, ["Rafael Tavares"])
        self.assertEqual(novo["interacoes"][0]["texto"], "Oi, sou o Rafael.")
        self.assertEqual(novo["interacoes"][1]["texto"], "Oi, sou o uma pessoa da comunidade. Rafael aqui.")
        self.assertTrue(relatorio[0]["so_nome_completo"])

    def test_apelido_sem_espaco_so_troca_o_nome_inteiro(self):
        lote = {"interacoes": [{"autor": "luan_dev22", "tipo": "depoimento", "texto": "Valeu, luan_dev22!"}]}
        novo, relatorio = il.anonimizar_pessoas(lote, ["luan_dev22"])
        self.assertEqual(novo["interacoes"][0]["texto"], "Valeu, uma pessoa da comunidade!")
        self.assertFalse(relatorio[0]["so_nome_completo"])


class TestComOMotor(_EmPastaTemporaria):
    RESPOSTA = {
        "sentimento_predominante": "Positivo",
        "topicos_principais": ["estágio"],
        "ativos_distribuicao_gerados": {
            "post_linkedin": {"titulo": "Conquista", "copy": "Uma pessoa da comunidade foi aprovada. Parabéns!", "potencial_engajamento": "Alto"},
            "destaque_newsletter_semanal": {"secao": "Vitória da Semana", "chamada": "Aprovação", "resumo": "Uma pessoa da comunidade foi aprovada."},
            "sugestao_conteudo_faq": {"tema": "Retry no LangGraph", "origem": "Dúvida de um participante"},
        },
    }

    def test_nenhum_nome_marcado_chega_a_llm_e_o_motor_nao_descarta_o_texto(self):
        novo, _ = il.anonimizar_pessoas(LOTE, ["Mariana Souza", "Rafael Tavares"])
        cliente = ClienteFalso([json.dumps(self.RESPOSTA)])
        resultado = il.executar(novo, cliente_llm=cliente)
        # O prompt do sistema tem exemplos fixos com nomes fictícios (guias de tom). O que importa é o lote enviado.
        enviado = cliente.chamadas[0]["messages"][1]["content"]
        self.assertNotIn("Mariana", enviado)
        self.assertNotIn("Souza", enviado)
        self.assertNotIn("Tavares", enviado)
        self.assertIn("Rafael Lima", enviado)  # quem autorizou continua com o nome
        ativos = resultado.resposta["ativos_distribuicao_gerados"]
        self.assertIsNotNone(ativos["post_linkedin"])
        self.assertIsNotNone(ativos["destaque_newsletter_semanal"])
        self.assertEqual(resultado.avisos, [])


if __name__ == "__main__":
    unittest.main()
