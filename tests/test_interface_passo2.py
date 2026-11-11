# tests/test_interface_passo2.py
"""Testes da revisão humana (passo 2) em src/interface_logica.py. Rodam offline, sem Streamlit e sem chave de API."""
import json
import unittest
from datetime import datetime

from src import interface_logica as il
from tests.test_interface_logica import LOTE, RESPOSTA_LLM, _EmPastaTemporaria

RESPOSTA = {"ativos_distribuicao_gerados": RESPOSTA_LLM["ativos_distribuicao_gerados"]}
AGORA = datetime(2026, 11, 10, 15, 30, 0)


def _aprovar(**extra):
    args = dict(
        chave="post_linkedin", decisao="aprovado", revisor="Revisora Teste",
        texto_original={"titulo": "A", "copy": "B"}, texto_final={"titulo": "A", "copy": "B"},
        pessoas=["Ana Teste"], conferiu_fatos=True, conferiu_autorizacao=True, agora=AGORA,
    )
    args.update(extra)
    return il.registrar_decisao(**args)


class TestCamposEditaveis(unittest.TestCase):
    def test_campos_e_rotulos_de_cada_ativo(self):
        self.assertEqual(il.campos_editaveis("post_linkedin"), [("titulo", "Título"), ("copy", "Texto do post")])
        self.assertEqual(il.campos_editaveis("destaque_newsletter_semanal"), [("chamada", "Chamada"), ("resumo", "Resumo")])
        self.assertEqual(il.campos_editaveis("sugestao_conteudo_faq"), [("tema", "Tema"), ("origem", "Origem")])

    def test_campos_fixos_nao_sao_editaveis(self):
        for chave in il.CAMPOS_EDITAVEIS:
            campos = [c for c, _ in il.campos_editaveis(chave)]
            for fixo in ("canal_recomendado", "potencial_engajamento", "secao", "status"):
                self.assertNotIn(fixo, campos)

    def test_texto_do_ativo_traz_so_os_campos_editaveis(self):
        self.assertEqual(il.texto_do_ativo(RESPOSTA, "post_linkedin"), {"titulo": "Conquista", "copy": "Parabéns, Ana!\n\n#Carreira"})

    def test_ativo_sem_material_devolve_vazio(self):
        resposta = {"ativos_distribuicao_gerados": {"post_linkedin": None}}
        self.assertEqual(il.texto_do_ativo(resposta, "post_linkedin"), {})
        self.assertEqual(il.texto_do_ativo({}, "sugestao_conteudo_faq"), {})


class TestPessoasCitadas(unittest.TestCase):
    def test_acha_primeiro_nome_sem_acento_nem_maiuscula(self):
        self.assertEqual(il.pessoas_citadas("parabéns, ana!", LOTE), ["Ana Teste"])

    def test_acha_nome_completo(self):
        self.assertEqual(il.pessoas_citadas("Quem é Bia Teste?", LOTE), ["Bia Teste"])

    def test_palavra_inteira(self):
        lote = {"interacoes": [{"autor": "Ana Souza"}]}
        self.assertEqual(il.pessoas_citadas("Comi uma banana.", lote), [])

    def test_ninguem_citado(self):
        self.assertEqual(il.pessoas_citadas("A comunidade foi muito bem esta semana.", LOTE), [])

    def test_participante_nunca_aparece(self):
        lote = {"interacoes": [{"autor": "Participante"}]}
        self.assertEqual(il.pessoas_citadas("Participante agradeceu.", lote), [])

    def test_sem_repetir_autor(self):
        lote = {"interacoes": [{"autor": "Ana Teste"}, {"autor": "Ana Teste"}]}
        self.assertEqual(il.pessoas_citadas("Ana Teste e Ana", lote), ["Ana Teste"])

    def test_junta_todos_os_campos_do_ativo(self):
        self.assertEqual(il.pessoas_citadas_no_ativo({"titulo": "Ana", "copy": "e a Bia"}, LOTE), ["Ana Teste", "Bia Teste"])


class TestRegistrarDecisao(unittest.TestCase):
    def test_aprovacao_completa(self):
        r = _aprovar()
        self.assertEqual(r["decisao"], "aprovado")
        self.assertEqual(r["revisor"], "Revisora Teste")
        self.assertEqual(r["data_hora"], "2026-11-10T15:30:00")
        self.assertFalse(r["editado_pela_pessoa"])
        self.assertEqual(r["pessoas_citadas"], ["Ana Teste"])

    def test_marca_quando_a_pessoa_editou(self):
        self.assertTrue(_aprovar(texto_final={"titulo": "A", "copy": "B corrigido"})["editado_pela_pessoa"])

    def test_aprovar_exige_as_duas_conferencias(self):
        with self.assertRaises(ValueError):
            _aprovar(conferiu_fatos=False)
        with self.assertRaises(ValueError):
            _aprovar(conferiu_autorizacao=False)

    def test_aprovar_exige_nome_do_revisor(self):
        for nome in ("", "  ", "B", None):
            with self.assertRaises(ValueError):
                _aprovar(revisor=nome)

    def test_nao_aprova_texto_com_campo_vazio(self):
        with self.assertRaises(ValueError):
            _aprovar(texto_final={"titulo": "A", "copy": "   "})

    def test_decisao_invalida(self):
        with self.assertRaises(ValueError):
            _aprovar(decisao="talvez")

    def test_reprovar_nao_exige_conferencias_nem_motivo(self):
        r = _aprovar(decisao="reprovado", conferiu_fatos=False, conferiu_autorizacao=False)
        self.assertEqual(r["decisao"], "reprovado")
        self.assertEqual(r["motivo"], "")

    def test_reprovar_tambem_exige_nome(self):
        with self.assertRaises(ValueError):
            _aprovar(decisao="reprovado", revisor="")

    def test_motivo_sem_espacos_nas_pontas(self):
        self.assertEqual(_aprovar(decisao="reprovado", motivo="  inventou um fato  ")["motivo"], "inventou um fato")


class TestMotivo(unittest.TestCase):
    def test_motivo_pronto_mais_detalhe(self):
        self.assertEqual(il.montar_motivo("Sem autorização das pessoas citadas", " pediram para não aparecer "),
                         "Sem autorização das pessoas citadas. pediram para não aparecer")

    def test_so_uma_das_partes_ou_nenhuma(self):
        self.assertEqual(il.montar_motivo("Fato incorreto ou exagerado"), "Fato incorreto ou exagerado")
        self.assertEqual(il.montar_motivo(None, "inventou um fato"), "inventou um fato")
        self.assertEqual(il.montar_motivo(None, ""), "")

    def test_motivo_de_autorizacao_esta_na_lista(self):
        self.assertIn("Sem autorização das pessoas citadas", il.MOTIVOS_REPROVACAO)


class TestTextoParaPublicar(unittest.TestCase):
    def test_post_so_o_texto_sem_titulo(self):
        self.assertEqual(il.texto_para_publicar("post_linkedin", {"titulo": "T", "copy": " Texto do post \n"}), "Texto do post")

    def test_newsletter_chamada_e_resumo(self):
        self.assertEqual(il.texto_para_publicar("destaque_newsletter_semanal", {"chamada": "C", "resumo": "R"}), "C\n\nR")

    def test_faq_so_o_tema_e_nao_a_origem(self):
        texto = il.texto_para_publicar("sugestao_conteudo_faq", {"tema": "Dica", "origem": "Dúvida de Ana Teste"})
        self.assertEqual(texto, "Dica")
        self.assertNotIn("Ana", texto)

    def test_ativo_desconhecido(self):
        with self.assertRaises(ValueError):
            il.texto_para_publicar("outro", {})

    def test_link_do_linkedin_e_simples_sem_texto_no_endereco(self):
        self.assertEqual(il.URL_LINKEDIN, "https://www.linkedin.com/feed/")
        self.assertNotIn("?", il.URL_LINKEDIN)


class TestDecisaoVale(unittest.TestCase):
    def test_vale_enquanto_o_texto_nao_muda(self):
        self.assertTrue(il.decisao_vale(_aprovar(), {"titulo": "A", "copy": "B"}))

    def test_deixa_de_valer_se_o_texto_mudar(self):
        self.assertFalse(il.decisao_vale(_aprovar(), {"titulo": "A", "copy": "B!"}))

    def test_sem_decisao_nao_vale(self):
        self.assertFalse(il.decisao_vale(None, {"titulo": "A"}))


class TestSalvar(_EmPastaTemporaria):
    def test_grava_ao_lado_do_pacote_e_nao_mexe_no_oci(self):
        caminho = il.salvar_decisoes({"post_linkedin": _aprovar()}, "Semana_Teste")
        self.assertEqual(caminho.name, "2026-semana-teste_curadoria.json")
        self.assertEqual(caminho.parent.name, "saida")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        self.assertEqual(dados["periodo_referencia"], "Semana_Teste")
        self.assertEqual(dados["decisoes"][0]["revisor"], "Revisora Teste")

    def test_regravar_substitui_o_estado_anterior(self):
        il.salvar_decisoes({"post_linkedin": _aprovar()}, "Semana_Teste")
        caminho = il.salvar_decisoes({"post_linkedin": _aprovar(decisao="reprovado")}, "Semana_Teste")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        self.assertEqual(len(dados["decisoes"]), 1)
        self.assertEqual(dados["decisoes"][0]["decisao"], "reprovado")

    def test_acentos_ficam_legiveis_no_arquivo(self):
        caminho = il.salvar_decisoes({"post_linkedin": _aprovar(texto_final={"titulo": "Estágio", "copy": "ação"})}, "Semana_Teste")
        self.assertIn("Estágio", caminho.read_text(encoding="utf-8"))


class TestPacoteAprovado(unittest.TestCase):
    def test_so_traz_os_aprovados(self):
        decisoes = {"post_linkedin": _aprovar(), "destaque_newsletter_semanal": _aprovar(chave="destaque_newsletter_semanal", decisao="reprovado")}
        pacote = il.pacote_aprovado(decisoes, "Semana_Teste")
        self.assertEqual([d["ativo"] for d in pacote["aprovados"]], ["post_linkedin"])

    def test_nada_aprovado(self):
        self.assertEqual(il.pacote_aprovado({}, "Semana_Teste")["aprovados"], [])


if __name__ == "__main__":
    unittest.main()


class AlturaDoCampoTest(unittest.TestCase):
    def test_texto_curto_usa_o_minimo(self):
        from src.interface_logica import altura_do_campo
        self.assertGreaterEqual(altura_do_campo("Oi", 50), 68)

    def test_texto_maior_fica_mais_alto(self):
        from src.interface_logica import altura_do_campo
        curto = altura_do_campo("a" * 50, 50)
        longo = altura_do_campo("a" * 500, 50)
        self.assertGreater(longo, curto)

    def test_cada_paragrafo_conta_uma_linha_pelo_menos(self):
        from src.interface_logica import altura_do_campo
        self.assertGreater(altura_do_campo("a\n\nb\n\nc\n\nd", 50), altura_do_campo("a b c d", 50))

    def test_respeita_o_maximo(self):
        from src.interface_logica import altura_do_campo
        self.assertEqual(altura_do_campo("a" * 100000, 50, maximo=560), 560)


class OrientacaoSemNomeTest(unittest.TestCase):
    def test_frase_sugerida_nao_tem_marca_de_genero(self):
        from src.interface_logica import EXEMPLO_SEM_NOME
        self.assertEqual(EXEMPLO_SEM_NOME, "uma pessoa da comunidade")
        for marcada in ("aluna", "aluno"):
            self.assertNotIn(marcada, EXEMPLO_SEM_NOME)
