# tests/test_ramificacoes.py
"""Testes do roteamento ANTES da LLM: rota por mensagem e prompt só com os ativos que têm material.
Rodam offline (cliente falso, sem chave e sem internet)."""
import itertools
import json
import unittest

from src.ia_service import LEMBRETE_FINAL, analisar_lote, montar_system_prompt
from src.pipeline import processar_lote
from src.prompts import ATIVOS_POSSIVEIS, SYSTEM_PROMPT_ANALISE, montar_system_prompt_analise
from src.roteamento import ATIVOS, ativos_com_material, rota_da_mensagem, rotear_interacoes
from src.schemas import TIPOS_INTERACAO
from tests.test_ia_service import ClienteFalso

POST, NEWS, FAQ = ATIVOS
GUIAS = {POST: "[GUIA LINKEDIN]", NEWS: "[GUIA NEWSLETTER]", FAQ: "[GUIA FAQ]"}


_contador = itertools.count(1)


def _m(tipo, autor="Ana Lima", texto="x"):
    # o id não leva o nome do autor: alguns testes conferem que o nome não chega à LLM
    return {"id": f"MSG_{next(_contador):03d}", "autor": autor, "canal": "#c", "tipo": tipo, "texto": texto}


class TestRotaDaMensagem(unittest.TestCase):
    def test_tabela_da_secao_1_de_regras_roteamento(self):
        esperado = {
            "depoimento": (POST, NEWS),
            "entrega_projeto": (POST, NEWS),
            "feedback": (NEWS,),
            "pergunta_tecnica": (FAQ,),
            "interacao_geral": (),
        }
        for tipo, rota in esperado.items():
            with self.subTest(tipo=tipo):
                self.assertEqual(rota_da_mensagem(tipo), rota)

    def test_todo_tipo_aceito_pelo_motor_tem_rota_definida(self):
        for tipo in TIPOS_INTERACAO:
            with self.subTest(tipo=tipo):
                self.assertIsInstance(rota_da_mensagem(tipo), tuple)

    def test_tipo_desconhecido_ou_vazio_nao_gera_ativo(self):
        for tipo in ("", "outro", None):
            with self.subTest(tipo=tipo):
                self.assertEqual(rota_da_mensagem(tipo), ())

    def test_maiuscula_e_espaco_nao_mudam_a_rota(self):
        self.assertEqual(rota_da_mensagem(" Depoimento "), (POST, NEWS))

    def test_ordem_dos_ativos_e_sempre_a_mesma(self):
        self.assertEqual(ATIVOS, ("post_linkedin", "destaque_newsletter_semanal", "sugestao_conteudo_faq"))
        self.assertEqual(ATIVOS, ATIVOS_POSSIVEIS)  # roteamento e prompt falam dos mesmos ativos


class TestRotearInteracoes(unittest.TestCase):
    def test_cada_ramo_traz_as_mensagens_do_tipo_certo(self):
        lote = [_m("depoimento"), _m("feedback", "Caio Reis"), _m("pergunta_tecnica", "Bia Souza"), _m("interacao_geral")]
        ramos = rotear_interacoes(lote)
        self.assertEqual([i["tipo"] for i in ramos[POST]], ["depoimento"])
        self.assertEqual([i["tipo"] for i in ramos[NEWS]], ["depoimento", "feedback"])
        self.assertEqual([i["tipo"] for i in ramos[FAQ]], ["pergunta_tecnica"])

    def test_conversa_geral_nao_entra_em_nenhum_ramo(self):
        ramos = rotear_interacoes([_m("interacao_geral")])
        self.assertEqual(ramos, {POST: [], NEWS: [], FAQ: []})

    def test_ativos_com_material_por_composicao_do_lote(self):
        casos = [
            ([_m("depoimento"), _m("pergunta_tecnica", "Bia Souza")], (POST, NEWS, FAQ)),
            ([_m("depoimento")], (POST, NEWS)),
            ([_m("entrega_projeto")], (POST, NEWS)),
            ([_m("feedback")], (NEWS,)),
            ([_m("pergunta_tecnica")], (FAQ,)),
            ([_m("interacao_geral")], ()),
        ]
        for lote, esperado in casos:
            with self.subTest(tipos=[i["tipo"] for i in lote]):
                self.assertEqual(ativos_com_material(lote), esperado)

    def test_ativo_sem_material_vai_para_o_log(self):
        with self.assertLogs("src.roteamento", level="INFO") as log:
            ativos_com_material([_m("pergunta_tecnica")])
        texto = "\n".join(log.output)
        self.assertIn(POST, texto)
        self.assertIn(NEWS, texto)
        self.assertNotIn(FAQ, texto)  # o FAQ tem material: não aparece como "sem material"

    def test_log_nao_traz_nome_de_pessoa(self):
        with self.assertLogs("src.roteamento", level="INFO") as log:
            ativos_com_material([_m("interacao_geral", "Bia Souza")])
        self.assertNotIn("Bia", "\n".join(log.output))


class TestPromptSoComOsAtivosPedidos(unittest.TestCase):
    def test_sem_argumento_pede_os_tres_ativos(self):
        self.assertEqual(montar_system_prompt_analise(), SYSTEM_PROMPT_ANALISE)
        self.assertEqual(montar_system_prompt_analise(ATIVOS), SYSTEM_PROMPT_ANALISE)
        for ativo in ATIVOS:
            self.assertIn(f"- {ativo}:", SYSTEM_PROMPT_ANALISE)
            self.assertIn(f'"{ativo}": {{', SYSTEM_PROMPT_ANALISE)

    def test_so_o_faq_tira_post_e_newsletter_das_instrucoes_e_do_formato(self):
        texto = montar_system_prompt_analise([FAQ])
        self.assertIn(f"- {FAQ}:", texto)
        self.assertIn(f'"{FAQ}": {{', texto)
        for fora in (POST, NEWS):
            self.assertNotIn(fora, texto)

    def test_regras_gerais_valem_em_qualquer_combinacao(self):
        for r in range(len(ATIVOS) + 1):
            for combinacao in itertools.combinations(ATIVOS, r):
                with self.subTest(ativos=combinacao):
                    texto = montar_system_prompt_analise(combinacao)
                    self.assertIn("REGRAS GERAIS", texto)
                    self.assertIn("Nunca cite o nome do autor desses relatos", texto)  # regra 5
                    self.assertIn("sentimento_predominante", texto)

    def test_formato_de_saida_e_json_valido_em_todas_as_combinacoes(self):
        for r in range(len(ATIVOS) + 1):
            for combinacao in itertools.combinations(ATIVOS, r):
                with self.subTest(ativos=combinacao):
                    texto = montar_system_prompt_analise(combinacao)
                    exemplo = json.loads(texto[texto.index('{\n  "sentimento'):])
                    self.assertEqual(tuple(exemplo["ativos_distribuicao_gerados"]), combinacao)

    def test_sem_nenhum_ativo_pede_so_sentimento_e_topicos(self):
        texto = montar_system_prompt_analise([])
        self.assertIn('"ativos_distribuicao_gerados": {}', texto)
        for ativo in ATIVOS:
            self.assertNotIn(ativo, texto)

    def test_ordem_pedida_nao_muda_o_prompt(self):
        self.assertEqual(montar_system_prompt_analise([FAQ, POST]), montar_system_prompt_analise([POST, FAQ]))

    def test_ativo_desconhecido_da_erro_claro(self):
        with self.assertRaises(ValueError):
            montar_system_prompt_analise(["post_instagram"])

    def test_prompt_menor_quando_ha_menos_ativos(self):
        completo = len(montar_system_prompt())
        self.assertLess(len(montar_system_prompt([POST, NEWS])), completo)
        self.assertLess(len(montar_system_prompt([FAQ])), len(montar_system_prompt([POST, NEWS])))
        self.assertLess(len(montar_system_prompt([])), len(montar_system_prompt([FAQ])))


class TestGuiasNoSystemPrompt(unittest.TestCase):
    def test_sem_argumento_leva_os_tres_guias_e_o_lembrete_final(self):
        system = montar_system_prompt()
        for marca in GUIAS.values():
            self.assertIn(marca, system)
        self.assertTrue(system.rstrip().endswith(LEMBRETE_FINAL))

    def test_so_os_guias_dos_ativos_pedidos(self):
        for pedidos in ([FAQ], [NEWS], [POST, NEWS], [POST, NEWS, FAQ]):
            with self.subTest(pedidos=pedidos):
                system = montar_system_prompt(pedidos)
                for ativo, marca in GUIAS.items():
                    if ativo in pedidos:
                        self.assertIn(marca, system)
                    else:
                        self.assertNotIn(marca, system)
                self.assertTrue(system.rstrip().endswith(LEMBRETE_FINAL))

    def test_sem_ativos_nao_leva_guia_nenhum(self):
        system = montar_system_prompt([])
        for marca in GUIAS.values():
            self.assertNotIn(marca, system)
        self.assertNotIn("DIRETRIZES DE TOM DE VOZ", system)

    def test_analisar_lote_envia_o_prompt_reduzido(self):
        analise = {"sentimento_predominante": "Positivo", "topicos_principais": ["x"], "ativos_distribuicao_gerados": {}}
        cliente = ClienteFalso([json.dumps(analise)])
        analisar_lote({"interacoes": [_m("pergunta_tecnica")]}, cliente=cliente, ativos=[FAQ])
        system = cliente.chamadas[0]["messages"][0]["content"]
        self.assertIn(GUIAS[FAQ], system)
        self.assertNotIn(GUIAS[POST], system)
        self.assertNotIn(GUIAS[NEWS], system)

    def test_analisar_lote_sem_ativos_continua_pedindo_os_tres(self):
        analise = {"sentimento_predominante": "Positivo", "topicos_principais": ["x"], "ativos_distribuicao_gerados": {}}
        cliente = ClienteFalso([json.dumps(analise)])
        analisar_lote({"interacoes": [_m("depoimento")]}, cliente=cliente)
        system = cliente.chamadas[0]["messages"][0]["content"]
        for marca in GUIAS.values():
            self.assertIn(marca, system)


class TestNoPipeline(unittest.TestCase):
    """O pipeline decide pela composição do lote que sobra depois da limpeza e da amostra."""

    def _lote(self, *interacoes):
        return {"origem_comunidade": "Teste", "periodo_referencia": "Semana_Teste", "interacoes": list(interacoes)}

    def _llm(self, post=False, newsletter=False, faq=False):
        """Resposta da LLM. Os ativos com True vêm preenchidos (mesmo os não pedidos: pior caso)."""
        ativos = {
            POST: {"titulo": "T", "copy": "Parabéns pela conquista", "potencial_engajamento": "Alto"} if post else None,
            NEWS: {"secao": "Vitória da Semana", "chamada": "C", "resumo": "Resumo"} if newsletter else None,
            FAQ: {"tema": "Dica Rápida: logs", "origem": "dúvida"} if faq else None,
        }
        return json.dumps({"sentimento_predominante": "Positivo", "topicos_principais": ["x"], "ativos_distribuicao_gerados": ativos})

    def _rodar(self, lote, resposta):
        cliente = ClienteFalso([resposta])
        r = processar_lote(lote, pasta_saida=None, cliente_llm=cliente)
        return r, cliente.chamadas[0]["messages"][0]["content"]

    def _ativos(self, r):
        a = r.ativos_distribuicao_gerados
        return (a.post_linkedin is not None, a.destaque_newsletter_semanal is not None, a.sugestao_conteudo_faq is not None)

    def test_lote_so_com_duvidas_pede_so_o_faq(self):
        lote = self._lote(_m("pergunta_tecnica", "Bia Souza", "Como configuro o retry?"))
        r, system = self._rodar(lote, self._llm(faq=True))
        self.assertIn(GUIAS[FAQ], system)
        self.assertNotIn(GUIAS[POST], system)
        self.assertNotIn(GUIAS[NEWS], system)
        self.assertEqual(self._ativos(r), (False, False, True))

    def test_lote_so_com_conquista_nao_pede_faq(self):
        lote = self._lote(_m("depoimento", "Ana Lima", "Passei no processo seletivo!"))
        r, system = self._rodar(lote, self._llm(post=True, newsletter=True))
        self.assertNotIn(GUIAS[FAQ], system)
        self.assertIn(GUIAS[POST], system)
        self.assertIn(GUIAS[NEWS], system)
        self.assertEqual(self._ativos(r), (True, True, False))

    def test_lote_so_com_feedback_pede_so_a_newsletter(self):
        lote = self._lote(_m("feedback", "Caio Reis", "Sugiro mais exemplos nas aulas de OCI."))
        r, system = self._rodar(lote, self._llm(newsletter=True))
        self.assertIn(GUIAS[NEWS], system)
        self.assertNotIn(GUIAS[POST], system)
        self.assertNotIn(GUIAS[FAQ], system)
        self.assertEqual(self._ativos(r), (False, True, False))

    def test_lote_so_com_conversa_geral_chama_a_llm_sem_nenhum_guia_e_sem_ativos(self):
        lote = self._lote(_m("interacao_geral", "Dora Melo", "Bom dia, pessoal!"))
        cliente = ClienteFalso([self._llm()])
        r = processar_lote(lote, pasta_saida=None, cliente_llm=cliente)
        self.assertEqual(len(cliente.chamadas), 1)  # a LLM ainda calcula sentimento e tópicos
        system = cliente.chamadas[0]["messages"][0]["content"]
        for marca in GUIAS.values():
            self.assertNotIn(marca, system)
        self.assertEqual(self._ativos(r), (False, False, False))
        self.assertEqual(r.resumo_comunidade.sentimento_predominante, "Positivo")

    def test_lote_completo_pede_os_tres_ativos(self):
        lote = self._lote(
            _m("depoimento", "Ana Lima", "Passei no processo seletivo!"),
            _m("pergunta_tecnica", "Bia Souza", "Como configuro o retry?"),
        )
        r, system = self._rodar(lote, self._llm(post=True, newsletter=True, faq=True))
        for marca in GUIAS.values():
            self.assertIn(marca, system)
        self.assertEqual(self._ativos(r), (True, True, True))

    def test_se_a_llm_devolver_ativo_nao_pedido_a_segunda_checagem_descarta(self):
        # defesa em duas camadas: mesmo pedindo só o FAQ, se vier um post ele não passa
        lote = self._lote(_m("pergunta_tecnica", "Bia Souza", "Como configuro o retry?"))
        with self.assertLogs("src.roteamento", level="WARNING"):
            r, _ = self._rodar(lote, self._llm(post=True, newsletter=True, faq=True))
        self.assertEqual(self._ativos(r), (False, False, True))

    def test_o_nome_do_autor_de_conversa_geral_continua_nao_chegando_a_llm(self):
        lote = self._lote(_m("interacao_geral", "Dora Melo", "Bom dia, pessoal!"))
        cliente = ClienteFalso([self._llm()])
        processar_lote(lote, pasta_saida=None, cliente_llm=cliente)
        enviado = cliente.chamadas[0]["messages"][1]["content"]
        self.assertNotIn("Dora Melo", enviado)


if __name__ == "__main__":
    unittest.main()
