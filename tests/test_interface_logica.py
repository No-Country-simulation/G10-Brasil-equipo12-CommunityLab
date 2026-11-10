# tests/test_interface_logica.py
"""Testes da lógica da interface (src/interface_logica.py). Rodam offline, sem Streamlit e sem chave de API."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import interface_logica as il
from tests.test_ia_service import ClienteFalso

LOTE = {
    "origem_comunidade": "Teste",
    "periodo_referencia": "Semana_Teste_Interface",
    "interacoes": [
        {"id": "T1", "autor": "Ana Teste", "canal": "#conquistas", "tipo": "depoimento", "texto": "Fui aprovada no estágio!"},
        {"id": "T2", "autor": "Bia Teste", "canal": "#duvidas", "tipo": "pergunta_tecnica", "texto": "Como configurar o retry no LangGraph?"},
    ],
}

RESPOSTA_LLM = {
    "sentimento_predominante": "Positivo",
    "topicos_principais": ["estágio", "LangGraph"],
    "ativos_distribuicao_gerados": {
        "post_linkedin": {"titulo": "Conquista", "copy": "Parabéns, Ana!\n\n#Carreira", "potencial_engajamento": "Alto"},
        "destaque_newsletter_semanal": {"secao": "Vitória da Semana", "chamada": "Ana é aprovada", "resumo": "Ana foi aprovada."},
        "sugestao_conteudo_faq": {"tema": "Dica Rápida: retry no LangGraph", "origem": "Dúvida de Bia"},
    },
}


class _EmPastaTemporaria(unittest.TestCase):
    """Roda cada teste numa pasta temporária, para a cópia local (saida/) não sujar o projeto."""

    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self._anterior = os.getcwd()
        os.chdir(self._pasta.name)

    def tearDown(self):
        os.chdir(self._anterior)
        self._pasta.cleanup()


class TestCarregarLote(unittest.TestCase):
    def test_json_enviado_vira_lote_validado(self):
        lote = il.carregar_lote_enviado("lote.json", json.dumps(LOTE).encode("utf-8"))
        self.assertEqual(lote["periodo_referencia"], "Semana_Teste_Interface")
        self.assertEqual(len(lote["interacoes"]), 2)

    def test_csv_enviado_usa_o_periodo_informado(self):
        csv = "id,autor,canal,tipo,texto\nA1,Ana,#c,depoimento,Passei no estágio\n".encode("utf-8")
        lote = il.carregar_lote_enviado("lote.csv", csv, periodo_csv="Semana_Teste_Csv")
        self.assertEqual(lote["periodo_referencia"], "Semana_Teste_Csv")
        self.assertEqual(lote["interacoes"][0]["autor"], "Ana")

    def test_csv_salvo_pelo_excel_com_bom_funciona(self):
        csv = "id,autor,canal,tipo,texto\nA1,Ana,#c,depoimento,Passei no estágio\n".encode("utf-8-sig")
        lote = il.carregar_lote_enviado("lote.csv", csv)
        self.assertEqual(lote["interacoes"][0]["texto"], "Passei no estágio")

    def test_formato_nao_suportado_da_erro_legivel(self):
        with self.assertRaisesRegex(ValueError, "não suportado"):
            il.carregar_lote_enviado("lote.txt", b"oi")

    def test_json_quebrado_da_erro_legivel(self):
        with self.assertRaisesRegex(ValueError, "Arquivo inválido"):
            il.carregar_lote_enviado("lote.json", b"{ isto nao e json")

    def test_json_fora_do_formato_diz_qual_campo(self):
        ruim = json.dumps({"origem_comunidade": "T", "periodo_referencia": "S", "interacoes": [{"autor": "A"}]}).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "interacoes"):
            il.carregar_lote_enviado("lote.json", ruim)

    def test_arquivo_que_nao_e_utf8_da_erro_legivel(self):
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            il.carregar_lote_enviado("lote.json", "{\"a\": \"é\"}".encode("latin-1"))


class TestExemplosDoProjeto(unittest.TestCase):
    def test_todos_os_arquivos_de_dados_carregam(self):
        exemplos = il.listar_exemplos()
        self.assertGreaterEqual(len(exemplos), 3)
        for caminho in exemplos:
            with self.subTest(arquivo=caminho.name):
                lote = il.carregar_lote_de_exemplo(caminho)
                self.assertTrue(lote["interacoes"])

    def test_lista_so_json_e_csv_em_ordem(self):
        with tempfile.TemporaryDirectory() as pasta:
            for nome in ("b.json", "a.csv", "c.md", "d.txt"):
                (Path(pasta) / nome).write_text("x", encoding="utf-8")
            self.assertEqual([p.name for p in il.listar_exemplos(pasta)], ["a.csv", "b.json"])

    def test_pasta_inexistente_devolve_lista_vazia(self):
        self.assertEqual(il.listar_exemplos("pasta-que-nao-existe"), [])

    def test_tabela_de_mensagens(self):
        tabela = il.tabela_de_mensagens(LOTE)
        self.assertEqual(tabela[0], {"id": "T1", "autor": "Ana Teste", "canal": "#conquistas", "tipo": "depoimento", "texto": "Fui aprovada no estágio!"})
        sem_id = {"interacoes": [{"autor": "A", "canal": "#c", "tipo": "depoimento", "texto": "x"}]}
        self.assertEqual(il.tabela_de_mensagens(sem_id)[0]["id"], "")


class TestExecutar(_EmPastaTemporaria):
    def _executar(self, lote=LOTE, **kwargs):
        cliente = ClienteFalso([json.dumps(RESPOSTA_LLM)])
        return il.executar(lote, cliente_llm=cliente, **kwargs), cliente

    def test_devolve_resposta_e_nao_envia_ao_oci(self):
        resultado, _ = self._executar()
        self.assertEqual(resultado.resposta["status"], "sucesso")
        self.assertEqual(resultado.resposta["armazenamento_oci"]["status"], "pendente_upload")

    def test_nunca_pede_envio_ao_oci(self):
        with mock.patch("src.interface_logica.processar_lote") as pipeline:
            pipeline.return_value.para_dict.return_value = {}
            il.executar(LOTE)
        self.assertIs(pipeline.call_args.kwargs["salvar_oci"], False)

    def test_periodo_informado_substitui_o_do_arquivo(self):
        resultado, _ = self._executar(periodo="Semana_Teste_Outra")
        self.assertIn("semana-teste-outra", resultado.caminho_local)
        self.assertIn("semana-teste-outra", resultado.resposta["armazenamento_oci"]["caminho_objeto"])
        self.assertTrue(Path(resultado.caminho_local).exists())

    def test_nao_altera_o_lote_recebido(self):
        copia = json.loads(json.dumps(LOTE))
        self._executar(periodo="Semana_Teste_Outra")
        self.assertEqual(LOTE, copia)

    def test_avisos_do_pipeline_chegam_a_tela(self):
        grande = dict(LOTE, interacoes=[
            {"id": f"R{i}", "autor": f"Autor {i}", "canal": "#c", "tipo": "depoimento", "texto": f"Relato {i}"} for i in range(14)
        ])
        resultado, _ = self._executar(grande)
        self.assertTrue(any("amostra de 10" in aviso for aviso in resultado.avisos))

    def test_lote_pequeno_nao_gera_aviso_de_amostra(self):
        resultado, _ = self._executar()
        self.assertFalse(any("amostra" in aviso for aviso in resultado.avisos))

    def test_coletor_de_avisos_e_removido_no_fim(self):
        import logging

        antes = list(logging.getLogger("src").handlers)
        self._executar()
        self.assertEqual(logging.getLogger("src").handlers, antes)

    def test_coletor_e_removido_mesmo_com_erro(self):
        import logging

        from src.ia_service import ErroServicoLLM

        antes = list(logging.getLogger("src").handlers)
        cliente = ClienteFalso([RuntimeError("sem rede")])
        with self.assertRaises(ErroServicoLLM):
            il.executar(LOTE, cliente_llm=cliente)
        self.assertEqual(logging.getLogger("src").handlers, antes)

    def test_lote_sem_texto_sobe_como_erro_de_valor(self):
        vazio = dict(LOTE, interacoes=[{"id": "V1", "autor": "A", "canal": "#c", "tipo": "depoimento", "texto": "  "}])
        with self.assertRaises(ValueError):
            il.executar(vazio, cliente_llm=ClienteFalso([]))


class TestExibicao(_EmPastaTemporaria):
    def test_ativos_na_ordem_da_tela_com_rotulos(self):
        resultado = il.executar(LOTE, cliente_llm=ClienteFalso([json.dumps(RESPOSTA_LLM)]))
        ativos = il.ativos_para_exibir(resultado.resposta)
        self.assertEqual([a["chave"] for a in ativos], ["post_linkedin", "destaque_newsletter_semanal", "sugestao_conteudo_faq"])
        self.assertTrue(all(a["existe"] for a in ativos))
        post = dict(ativos[0]["campos"])
        self.assertEqual(post["Título"], "Conquista")
        self.assertEqual(post["Texto do post"], "Parabéns, Ana!\n\n#Carreira")
        self.assertEqual(dict(ativos[2]["campos"])["Tema"], "Dica Rápida: retry no LangGraph")

    def test_ativo_nulo_vem_como_sem_material(self):
        resposta = {"ativos_distribuicao_gerados": {"post_linkedin": None, "destaque_newsletter_semanal": None, "sugestao_conteudo_faq": None}}
        for ativo in il.ativos_para_exibir(resposta):
            self.assertFalse(ativo["existe"])
            self.assertEqual(ativo["campos"], [])

    def test_resposta_sem_bloco_de_ativos_nao_quebra(self):
        self.assertEqual(len(il.ativos_para_exibir({})), 3)

    def test_nomes_de_marketing_e_frase_de_cartao_vazio(self):
        ativos = il.ativos_para_exibir({})
        self.assertEqual(
            [a["nome"] for a in ativos],
            ["Post para o LinkedIn", "Destaque para a newsletter", "Pergunta frequente sugerida"],
        )
        self.assertEqual(ativos[2]["sem_material"], "Nenhuma dúvida técnica neste período, então não há sugestão de FAQ.")
        self.assertTrue(all(a["sem_material"] for a in ativos))


class TestClimaEFrase(unittest.TestCase):
    def test_todos_os_sentimentos_do_motor_tem_frase(self):
        from src.schemas import SENTIMENTOS

        self.assertEqual(set(il.CLIMA_DA_COMUNIDADE), set(SENTIMENTOS))
        for valor in SENTIMENTOS:
            self.assertTrue(il.clima_da_comunidade(valor))

    def test_valor_desconhecido_nao_quebra(self):
        self.assertEqual(il.clima_da_comunidade("Misto"), "Misto")
        self.assertEqual(il.clima_da_comunidade(""), "Não informado")

    def test_frase_do_lote_no_singular_e_no_plural(self):
        lote = {"origem_comunidade": "Discord_X", "periodo_referencia": "Semana_01", "interacoes": [{}]}
        self.assertEqual(il.frase_do_lote(lote), "Encontramos 1 mensagem da comunidade Discord_X.")
        lote["interacoes"] = [{}, {}]
        self.assertEqual(il.frase_do_lote(lote), "Encontramos 2 mensagens da comunidade Discord_X.")


class TestExemplosDeDemonstracao(unittest.TestCase):
    def test_so_aparecem_os_que_existem_com_nome_simples_e_na_ordem(self):
        with tempfile.TemporaryDirectory() as pasta:
            for arquivo in ("caso_duvida_tecnica.json", "caso_conquista.json", "dataset_simulado.json"):
                (Path(pasta) / arquivo).write_text("{}", encoding="utf-8")
            exemplos = il.exemplos_de_demonstracao(Path(pasta))
        self.assertEqual([nome for _, nome in exemplos], ["Conquistas da comunidade", "Dúvida técnica"])
        self.assertEqual([c.name for c, _ in exemplos], ["caso_conquista.json", "caso_duvida_tecnica.json"])

    def test_pasta_vazia_ou_inexistente_devolve_lista_vazia(self):
        self.assertEqual(il.exemplos_de_demonstracao(Path("pasta_que_nao_existe_xyz")), [])

    def test_os_exemplos_do_projeto_que_existem_carregam(self):
        for caminho, nome in il.exemplos_de_demonstracao():
            with self.subTest(nome=nome):
                self.assertTrue(il.carregar_lote_de_exemplo(caminho)["interacoes"])


class TestOrigens(_EmPastaTemporaria):
    LOTE_MISTO = {
        "origem_comunidade": "Teste",
        "periodo_referencia": "Semana_Teste_Interface",
        "interacoes": [
            {"id": "A1", "autor": "Ana", "canal": "#conquistas", "tipo": "depoimento", "texto": "Passei no estágio!"},
            {"id": "B1", "autor": "Bia", "canal": "#duvidas", "tipo": "pergunta_tecnica", "texto": "Como faço o retry?"},
            {"id": "C1", "autor": "Caio", "canal": "#feedbacks", "tipo": "feedback", "texto": "A aula foi ótima."},
            {"id": "D1", "autor": "Duda", "canal": "#geral", "tipo": "interacao_geral", "texto": "Bom dia, pessoal!"},
        ],
    }

    def test_origem_de_cada_ativo_segue_o_tipo_da_mensagem(self):
        o = il.origens_possiveis(self.LOTE_MISTO)
        self.assertEqual([m["id"] for m in o["post_linkedin"]], ["A1"])
        self.assertEqual([m["id"] for m in o["destaque_newsletter_semanal"]], ["A1", "C1"])
        self.assertEqual([m["id"] for m in o["sugestao_conteudo_faq"]], ["B1"])

    def test_conversa_geral_nao_aparece_como_origem(self):
        o = il.origens_possiveis(self.LOTE_MISTO)
        for mensagens in o.values():
            self.assertNotIn("D1", [m["id"] for m in mensagens])

    def test_traz_autor_e_canal(self):
        post = il.origens_possiveis(self.LOTE_MISTO)["post_linkedin"][0]
        self.assertEqual((post["autor"], post["canal"], post["tipo"]), ("Ana", "#conquistas", "depoimento"))

    def test_respeita_a_amostra_enviada_a_llm(self):
        lote = dict(self.LOTE_MISTO, interacoes=[
            {"id": f"R{i}", "autor": f"Autor {i}", "canal": "#c", "tipo": "depoimento", "texto": f"Relato {i}"} for i in range(14)
        ])
        self.assertLessEqual(len(il.origens_possiveis(lote, 10)["post_linkedin"]), 10)
        self.assertEqual(len(il.origens_possiveis(lote, None)["post_linkedin"]), 14)

    def test_mensagem_repetida_conta_uma_vez(self):
        repetida = dict(self.LOTE_MISTO, interacoes=[
            {"id": "A1", "autor": "Ana", "canal": "#c", "tipo": "depoimento", "texto": "Passei no estágio!"},
            {"id": "A2", "autor": "Ana", "canal": "#c", "tipo": "depoimento", "texto": "Passei no estágio!"},
        ])
        self.assertEqual([m["id"] for m in il.origens_possiveis(repetida)["post_linkedin"]], ["A1"])

    def test_executar_ja_devolve_as_origens(self):
        resultado = il.executar(LOTE, cliente_llm=ClienteFalso([json.dumps(RESPOSTA_LLM)]))
        self.assertEqual([m["id"] for m in resultado.origens["post_linkedin"]], ["T1"])
        self.assertEqual([m["id"] for m in resultado.origens["sugestao_conteudo_faq"]], ["T2"])


class TestStatusOci(unittest.TestCase):
    def test_pendente(self):
        texto = il.texto_status_oci({"armazenamento_oci": {"status": "pendente_upload"}})
        self.assertIn("Não enviado", texto)

    def test_falha_mostra_o_motivo(self):
        texto = il.texto_status_oci({"armazenamento_oci": {"status": "falha_ao_salvar", "detalhe_erro": "sem permissão"}})
        self.assertIn("Falha", texto)
        self.assertIn("sem permissão", texto)

    def test_status_desconhecido_ou_ausente(self):
        self.assertIn("xyz", il.texto_status_oci({"armazenamento_oci": {"status": "xyz"}}))
        self.assertIn("desconhecido", il.texto_status_oci({}))


if __name__ == "__main__":
    unittest.main()
