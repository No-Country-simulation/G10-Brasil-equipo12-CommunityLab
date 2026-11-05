# tests/test_roteamento.py
"""Testes da segunda checagem depois da LLM (src/roteamento.py). Rodam offline."""
import json
import unittest

from src.pipeline import processar_lote
from src.roteamento import aplicar_regras_de_roteamento
from src.schemas import AnaliseLLM
from tests.test_ia_service import ClienteFalso


def _analise(post="Parabéns pela conquista", newsletter="Resumo da semana", faq=True, secao="Vitória da Semana"):
    """Resposta da LLM com os três ativos preenchidos (o pior caso para a checagem)."""
    return AnaliseLLM.model_validate({
        "sentimento_predominante": "Positivo",
        "topicos_principais": ["carreira"],
        "ativos_distribuicao_gerados": {
            "post_linkedin": None if post is None else {
                "titulo": "Título", "copy": post, "potencial_engajamento": "Alto"},
            "destaque_newsletter_semanal": None if newsletter is None else {
                "secao": secao, "chamada": "Chamada", "resumo": newsletter},
            "sugestao_conteudo_faq": {"tema": "Dica Rápida: logs", "origem": "dúvida"} if faq else None,
        },
    })


def _m(autor, tipo, texto="x"):
    return {"id": autor, "autor": autor, "canal": "#c", "tipo": tipo, "texto": texto}


def _ativos(analise):
    a = analise.ativos_distribuicao_gerados
    return (a.post_linkedin is not None, a.destaque_newsletter_semanal is not None, a.sugestao_conteudo_faq is not None)


class TestTipoCertoParaCadaAtivo(unittest.TestCase):
    def test_lote_completo_mantem_os_tres_ativos(self):
        lote = [_m("Ana Lima", "depoimento"), _m("Bia Souza", "pergunta_tecnica")]
        self.assertEqual(_ativos(aplicar_regras_de_roteamento(_analise(), lote)), (True, True, True))

    def test_so_pergunta_tecnica_deixa_so_o_faq(self):
        r = aplicar_regras_de_roteamento(_analise(), [_m("Bia Souza", "pergunta_tecnica")])
        self.assertEqual(_ativos(r), (False, False, True))

    def test_so_feedback_deixa_so_a_newsletter(self):
        r = aplicar_regras_de_roteamento(_analise(), [_m("Caio Reis", "feedback")])
        self.assertEqual(_ativos(r), (False, True, False))

    def test_so_depoimento_deixa_post_e_newsletter(self):
        r = aplicar_regras_de_roteamento(_analise(), [_m("Ana Lima", "depoimento")])
        self.assertEqual(_ativos(r), (True, True, False))

    def test_entrega_projeto_libera_post_e_newsletter(self):
        r = aplicar_regras_de_roteamento(_analise(), [_m("Ana Lima", "entrega_projeto")])
        self.assertEqual(_ativos(r), (True, True, False))

    def test_so_conversa_geral_nao_gera_nada(self):
        r = aplicar_regras_de_roteamento(_analise(), [_m("Participante", "interacao_geral")])
        self.assertEqual(_ativos(r), (False, False, False))

    def test_ativo_que_a_llm_ja_deixou_null_continua_null(self):
        r = aplicar_regras_de_roteamento(_analise(post=None, faq=False), [_m("Ana Lima", "depoimento")])
        self.assertEqual(_ativos(r), (False, True, False))

    def test_descarte_vai_para_o_log(self):
        with self.assertLogs("src.roteamento", level="WARNING") as log:
            aplicar_regras_de_roteamento(_analise(), [_m("Bia Souza", "pergunta_tecnica")])
        texto = "\n".join(log.output)
        self.assertIn("post_linkedin", texto)
        self.assertIn("destaque_newsletter_semanal", texto)
        self.assertNotIn("Bia", texto)  # o log não traz nome de pessoa

    def test_nao_altera_a_analise_recebida(self):
        original = _analise()
        aplicar_regras_de_roteamento(original, [_m("Bia Souza", "pergunta_tecnica")])
        self.assertEqual(_ativos(original), (True, True, True))


class TestNomeDeQuemSoFezPergunta(unittest.TestCase):
    def setUp(self):
        self.lote = [
            _m("Ana Lima", "depoimento"),
            _m("Rafael Tavares", "pergunta_tecnica"),
            _m("Participante", "interacao_geral"),
        ]

    def test_post_com_nome_completo_do_autor_da_duvida_e_descartado(self):
        r = aplicar_regras_de_roteamento(_analise(post="A Ana e o Rafael Tavares lançaram o projeto"), self.lote)
        self.assertEqual(_ativos(r), (False, True, True))

    def test_post_com_so_o_primeiro_nome_tambem_e_descartado(self):
        r = aplicar_regras_de_roteamento(_analise(post="O Rafael pediu ajuda e a comunidade respondeu"), self.lote)
        self.assertEqual(_ativos(r), (False, True, True))

    def test_newsletter_com_o_nome_e_descartada(self):
        r = aplicar_regras_de_roteamento(_analise(newsletter="Destaque: o RAFAEL resolveu o erro"), self.lote)
        self.assertEqual(_ativos(r), (True, False, True))

    def test_ignora_acento_e_maiuscula(self):
        lote = [_m("Ana Lima", "depoimento"), _m("Vinícius Araújo", "pergunta_tecnica")]
        r = aplicar_regras_de_roteamento(_analise(post="vinicius araujo participou"), lote)
        self.assertEqual(_ativos(r), (False, True, True))

    def test_citar_quem_fez_depoimento_e_permitido(self):
        r = aplicar_regras_de_roteamento(_analise(post="A Ana Lima conseguiu a vaga"), self.lote)
        self.assertEqual(_ativos(r), (True, True, True))

    def test_autor_com_depoimento_e_pergunta_pode_ser_citado(self):
        lote = [_m("Rafael Tavares", "depoimento"), _m("Rafael Tavares", "pergunta_tecnica")]
        r = aplicar_regras_de_roteamento(_analise(post="O Rafael Tavares conseguiu"), lote)
        self.assertEqual(_ativos(r), (True, True, True))

    def test_autor_com_feedback_pode_ser_citado(self):
        lote = [_m("Rafael Tavares", "feedback"), _m("Ana Lima", "depoimento")]
        r = aplicar_regras_de_roteamento(_analise(post="O Rafael elogiou"), lote)
        self.assertEqual(_ativos(r), (True, True, False))  # sem pergunta técnica, o FAQ cai

    def test_primeiro_nome_igual_ao_de_pessoa_liberada_so_vale_o_nome_completo(self):
        lote = [_m("Rafael Souza", "depoimento"), _m("Rafael Tavares", "pergunta_tecnica")]
        permitido = aplicar_regras_de_roteamento(_analise(post="O Rafael conseguiu a vaga"), lote)
        self.assertEqual(_ativos(permitido), (True, True, True))
        barrado = aplicar_regras_de_roteamento(_analise(post="O Rafael Tavares conseguiu a vaga"), lote)
        self.assertEqual(_ativos(barrado), (False, True, True))

    def test_palavra_inteira_ana_nao_casa_com_banana(self):
        lote = [_m("Ivo Dias", "depoimento"), _m("Ana Lima", "pergunta_tecnica")]
        r = aplicar_regras_de_roteamento(_analise(post="Foi uma conquista de dar água na banana"), lote)
        self.assertEqual(_ativos(r), (True, True, True))

    def test_apelido_sem_espaco_vale_so_inteiro(self):
        lote = [_m("Ivo Dias", "depoimento"), _m("luan_dev22", "pergunta_tecnica")]
        self.assertEqual(_ativos(aplicar_regras_de_roteamento(_analise(post="Valeu luan"), lote)), (True, True, True))
        self.assertEqual(_ativos(aplicar_regras_de_roteamento(_analise(post="Valeu luan_dev22"), lote)), (False, True, True))

    def test_secao_da_newsletter_nao_e_conferida(self):
        # uma pessoa chamada Vitória não pode derrubar toda newsletter "Vitória da Semana"
        lote = [_m("Ivo Dias", "depoimento"), _m("Vitória Alves", "pergunta_tecnica")]
        r = aplicar_regras_de_roteamento(_analise(secao="Vitória da Semana"), lote)
        self.assertEqual(_ativos(r), (True, True, True))

    def test_faq_pode_citar_o_autor_da_duvida(self):
        # a "origem" do FAQ é interna (vai para a mentoria), então não entra na checagem
        lote = [_m("Rafael Tavares", "pergunta_tecnica")]
        r = aplicar_regras_de_roteamento(_analise(), lote)
        self.assertEqual(_ativos(r)[2], True)

    def test_autor_anonimo_nao_vira_nome_protegido(self):
        lote = [_m("Ana Lima", "depoimento"), _m("Participante", "interacao_geral")]
        r = aplicar_regras_de_roteamento(_analise(post="Um participante da comunidade conquistou"), lote)
        self.assertEqual(_ativos(r), (True, True, False))  # sem pergunta técnica, o FAQ cai


class TestNoPipeline(unittest.TestCase):
    def _lote(self, *interacoes):
        return {"origem_comunidade": "Teste", "periodo_referencia": "Semana_Teste", "interacoes": list(interacoes)}

    def _json_llm(self, **kw):
        a = _analise(**kw).ativos_distribuicao_gerados.model_dump(by_alias=True)
        return json.dumps({"sentimento_predominante": "Positivo", "topicos_principais": ["x"], "ativos_distribuicao_gerados": a})

    def test_llm_gera_post_sem_depoimento_e_o_pipeline_descarta(self):
        lote = self._lote({"id": "1", "autor": "Bia Souza", "canal": "#c", "tipo": "pergunta_tecnica", "texto": "Como faço?"})
        r = processar_lote(lote, pasta_saida=None, cliente_llm=ClienteFalso([self._json_llm()]))
        ativos = r.ativos_distribuicao_gerados
        self.assertIsNone(ativos.post_linkedin)
        self.assertIsNone(ativos.destaque_newsletter_semanal)
        self.assertIsNotNone(ativos.sugestao_conteudo_faq)

    def test_llm_cita_o_autor_da_duvida_no_post_e_o_pipeline_descarta(self):
        lote = self._lote(
            {"id": "1", "autor": "Ana Lima", "canal": "#c", "tipo": "depoimento", "texto": "Passei no processo seletivo!"},
            {"id": "2", "autor": "Rafael Tavares", "canal": "#c", "tipo": "pergunta_tecnica", "texto": "Como faço?"},
        )
        r = processar_lote(lote, pasta_saida=None, cliente_llm=ClienteFalso([self._json_llm(post="O Rafael Tavares também aprendeu")]))
        self.assertIsNone(r.ativos_distribuicao_gerados.post_linkedin)
        self.assertIsNotNone(r.ativos_distribuicao_gerados.destaque_newsletter_semanal)

    def test_resposta_correta_passa_inteira(self):
        lote = self._lote(
            {"id": "1", "autor": "Ana Lima", "canal": "#c", "tipo": "depoimento", "texto": "Passei no processo seletivo!"},
            {"id": "2", "autor": "Rafael Tavares", "canal": "#c", "tipo": "pergunta_tecnica", "texto": "Como faço?"},
        )
        r = processar_lote(lote, pasta_saida=None, cliente_llm=ClienteFalso([self._json_llm(post="A Ana passou no processo seletivo")]))
        a = r.ativos_distribuicao_gerados
        self.assertTrue(a.post_linkedin and a.destaque_newsletter_semanal and a.sugestao_conteudo_faq)


if __name__ == "__main__":
    unittest.main()
