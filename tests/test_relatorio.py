"""Testa o relatório da semana (src/relatorio.py): conteúdo, ausência de dados pessoais e envio ao OCI."""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from src.oracle_storage import montar_caminho, montar_caminho_relatorio, salvar_relatorio_no_oci
from src.pipeline import caminho_local_relatorio, processar_lote
from src.relatorio import MOTIVO_SEM_MATERIAL, MOTIVO_SEM_TEXTO, montar_relatorio, topicos_sem_nomes
from src.schemas import ArmazenamentoOci, AtivosDistribuicao, PostLinkedin, RespostaCommunityLab, ResumoComunidade
from tests.test_ia_service import ClienteFalso

AUTORES = ["Mariana Souza", "Lucas Albuquerque", "luan_dev22"]
AGORA = datetime(2026, 11, 12, 14, 30)


def _resposta(post=True, newsletter=False, oci=None, topicos=None):
    ativos = AtivosDistribuicao(
        post_linkedin=PostLinkedin(titulo="T", copy="Texto do post", potencial_engajamento="Alto") if post else None,
        destaque_newsletter_semanal=None,
    )
    return RespostaCommunityLab(
        status="sucesso",
        resumo_comunidade=ResumoComunidade(
            total_interacoes_processadas=12,
            sentimento_predominante="Positivo",
            topicos_principais=topicos or ["Contratação / Conquistas"],
        ),
        ativos_distribuicao_gerados=ativos,
        armazenamento_oci=oci,
    )


class ClienteOciGravador:
    """Cliente OCI falso: guarda o que seria enviado ao bucket."""

    def __init__(self):
        self.enviados = []

    def get_namespace(self):
        return SimpleNamespace(data="namespace_simulado")

    def put_object(self, namespace, bucket, nome, corpo, **kwargs):
        self.enviados.append({"nome": nome, "corpo": corpo, "kwargs": kwargs})


class TopicosSemNomesTest(unittest.TestCase):
    def test_omite_topico_com_nome_completo_ou_primeiro_nome(self):
        mantidos, omitidos = topicos_sem_nomes(
            ["LangGraph", "Dúvida da Lucas Albuquerque", "Parabéns, Mariana!", "Estágio"], AUTORES
        )
        self.assertEqual(mantidos, ["LangGraph", "Estágio"])
        self.assertEqual(omitidos, 2)

    def test_so_palavra_inteira_e_sem_acento_ou_maiuscula(self):
        # 'mariana' não casa com 'Marianas' (palavra inteira), mas casa com 'MARIANA'
        mantidos, omitidos = topicos_sem_nomes(["Marianas do mundo", "MARIANA em destaque"], AUTORES)
        self.assertEqual(mantidos, ["Marianas do mundo"])
        self.assertEqual(omitidos, 1)

    def test_apelido_sem_espaco_so_vale_inteiro(self):
        mantidos, omitidos = topicos_sem_nomes(["luan_dev22 perguntou", "luan"], AUTORES)
        self.assertEqual(mantidos, ["luan"])
        self.assertEqual(omitidos, 1)

    def test_topico_vira_uma_linha_e_vazio_some(self):
        mantidos, omitidos = topicos_sem_nomes(["Contratação\n  e   vagas", "   "], AUTORES)
        self.assertEqual(mantidos, ["Contratação e vagas"])
        self.assertEqual(omitidos, 0)


class MontarRelatorioTest(unittest.TestCase):
    def _relatorio(self, **kw):
        resposta = kw.pop("resposta", _resposta())
        padrao = dict(periodo="Semana_04", total_amostra=10, ativos_pedidos=("post_linkedin", "destaque_newsletter_semanal"), autores=AUTORES, agora=AGORA)
        padrao.update(kw)
        return montar_relatorio(resposta, **padrao)

    def test_traz_os_campos_combinados(self):
        texto = self._relatorio()
        for esperado in (
            "# Relatório da semana: Semana_04",
            "Gerado em 12/11/2026 14:30.",
            "| Mensagens processadas (depois da limpeza) | 12 |",
            "| Mensagens analisadas pela IA (amostra) | 10 |",
            "| Sentimento predominante | Positivo |",
            "- Contratação / Conquistas",
            "| Post para o LinkedIn | Gerado |",
            "| Destaque da newsletter | Sem texto | " + MOTIVO_SEM_TEXTO,
            "| Sugestão de FAQ | Sem material | " + MOTIVO_SEM_MATERIAL,
            "Pacote: não enviado ao OCI nesta execução.",
        ):
            self.assertIn(esperado, texto)

    def test_avisa_quando_a_ia_viu_so_uma_amostra(self):
        self.assertIn("amostra de 10 entre 12 mensagens", self._relatorio(total_amostra=10))
        self.assertNotIn("amostra de 12 entre 12", self._relatorio(total_amostra=12))

    def test_nao_tem_nome_de_autor_nem_texto_de_mensagem(self):
        resposta = _resposta(topicos=["Parabéns à Mariana", "Dúvida do Lucas", "LangGraph"])
        texto = self._relatorio(resposta=resposta).lower()
        for nome in ("mariana", "lucas", "albuquerque", "souza", "luan_dev22"):
            self.assertNotIn(nome, texto)
        self.assertIn("- langgraph", texto)
        self.assertIn("2 tópico(s) omitido(s)", texto)

    def test_sem_nenhum_topico_disponivel(self):
        texto = self._relatorio(resposta=_resposta(topicos=["Mariana"]))
        self.assertIn("- Nenhum tópico disponível.", texto)

    def test_envio_com_sucesso_mostra_bucket_e_caminhos(self):
        oci = ArmazenamentoOci(bucket="bucket-teste", caminho_objeto="ativos/2026-semana-04/pacote-distribuicao.json", status="salvo_com_sucesso")
        texto = self._relatorio(resposta=_resposta(oci=oci), caminho_relatorio="ativos/2026-semana-04/relatorio-comunidade.md")
        self.assertIn("Pacote: Enviado ao OCI. (status: `salvo_com_sucesso`)", texto)
        self.assertIn("`bucket-teste`", texto)
        self.assertIn("Objeto do pacote: `ativos/2026-semana-04/pacote-distribuicao.json`", texto)
        self.assertIn("Objeto deste relatório: `ativos/2026-semana-04/relatorio-comunidade.md`", texto)

    def test_falha_de_envio_mostra_so_o_tipo_do_erro(self):
        oci = ArmazenamentoOci(bucket="b", caminho_objeto="c", status="falha_ao_salvar", detalhe_erro="RuntimeError")
        texto = self._relatorio(resposta=_resposta(oci=oci))
        self.assertIn("Falha ao enviar ao OCI.", texto)
        self.assertIn("Tipo do erro: `RuntimeError`", texto)


class CaminhoERelatorioNoOciTest(unittest.TestCase):
    def test_relatorio_fica_ao_lado_do_pacote(self):
        pacote = montar_caminho("Semana_04", ano=2026)
        relatorio = montar_caminho_relatorio("Semana_04", ano=2026)
        self.assertEqual(pacote, "ativos/2026-semana-04/pacote-distribuicao.json")
        self.assertEqual(relatorio, "ativos/2026-semana-04/relatorio-comunidade.md")

    def test_envia_markdown_em_utf8_com_content_type(self):
        cliente = ClienteOciGravador()
        resultado = salvar_relatorio_no_oci("# Relatório\n\nParabéns 🎉", "Semana_04", cliente=cliente)
        self.assertEqual(resultado["status"], "salvo_com_sucesso")
        enviado = cliente.enviados[0]
        self.assertTrue(enviado["nome"].endswith("/relatorio-comunidade.md"))
        self.assertEqual(enviado["corpo"].decode("utf-8"), "# Relatório\n\nParabéns 🎉")
        self.assertEqual(enviado["kwargs"]["content_type"], "text/markdown; charset=utf-8")

    def test_falha_no_envio_nao_levanta_erro(self):
        class Quebrado(ClienteOciGravador):
            def put_object(self, *a, **k):
                raise RuntimeError("erro simulado")

        resultado = salvar_relatorio_no_oci("x", "Semana_04", cliente=Quebrado())
        self.assertEqual(resultado["status"], "falha_ao_salvar")
        self.assertEqual(resultado["detalhe_erro"], "RuntimeError")


LOTE = {
    "origem_comunidade": "Discord_Teste",
    "periodo_referencia": "Semana_Teste_Relatorio",
    "interacoes": [
        {"id": "1", "autor": "Mariana Souza", "canal": "#conquistas", "tipo": "depoimento", "texto": "Passei no processo seletivo!"},
        {"id": "2", "autor": "Lucas Albuquerque", "canal": "#duvidas", "tipo": "pergunta_tecnica", "texto": "Como faço um retry no LangGraph?"},
    ],
}
ANALISE = {
    "sentimento_predominante": "Positivo",
    "topicos_principais": ["Parabéns à Mariana", "LangGraph / retry"],
    "ativos_distribuicao_gerados": {
        "post_linkedin": {"titulo": "Conquista", "copy": "A Mariana Souza foi aprovada.", "potencial_engajamento": "Alto"},
        "destaque_newsletter_semanal": None,
        "sugestao_conteudo_faq": None,
    },
}


class PipelineGeraRelatorioTest(unittest.TestCase):
    def _rodar(self, salvar_oci):
        cliente_oci = ClienteOciGravador()
        with tempfile.TemporaryDirectory() as pasta:
            resposta = processar_lote(
                LOTE,
                salvar_oci=salvar_oci,
                pasta_saida=pasta,
                cliente_llm=ClienteFalso([json.dumps(ANALISE)]),
                cliente_oci=cliente_oci,
            )
            arquivo = caminho_local_relatorio(LOTE["periodo_referencia"], pasta)
            local = arquivo.read_text(encoding="utf-8") if arquivo.exists() else None
        return resposta, cliente_oci, local

    def test_sem_oci_grava_so_a_copia_local(self):
        _, oci, local = self._rodar(salvar_oci=False)
        self.assertEqual(oci.enviados, [])
        self.assertIn("# Relatório da semana: Semana_Teste_Relatorio", local)
        self.assertIn("Pacote: não enviado ao OCI nesta execução.", local)
        self.assertNotIn("Objeto do pacote", local)  # sem envio, não mostra caminho que ainda não existe

    def test_com_oci_envia_pacote_e_relatorio_lado_a_lado(self):
        resposta, oci, local = self._rodar(salvar_oci=True)
        nomes = [e["nome"] for e in oci.enviados]
        self.assertEqual(len(nomes), 2)
        self.assertTrue(nomes[0].endswith("/pacote-distribuicao.json"))
        self.assertTrue(nomes[1].endswith("/relatorio-comunidade.md"))
        self.assertEqual(nomes[0].rsplit("/", 1)[0], nomes[1].rsplit("/", 1)[0])
        self.assertEqual(resposta.armazenamento_oci.status, "salvo_com_sucesso")
        self.assertIn("Pacote: Enviado ao OCI.", local)
        self.assertIn("Objeto deste relatório:", local)
        # o que foi ao bucket é o mesmo texto da cópia local
        self.assertEqual(oci.enviados[1]["corpo"].decode("utf-8"), local)

    def test_relatorio_do_pipeline_nao_tem_nomes_nem_mensagens(self):
        _, _, local = self._rodar(salvar_oci=False)
        minusculo = local.lower()
        for proibido in ("mariana", "lucas", "albuquerque", "souza", "processo seletivo", "retry no langgraph"):
            self.assertNotIn(proibido, minusculo)
        self.assertIn("- langgraph / retry", minusculo)
        self.assertIn("1 tópico(s) omitido(s)", minusculo)
        # newsletter foi pedida à IA e voltou vazia; FAQ ficou sem material? (há pergunta técnica: foi pedida)
        self.assertIn("| Destaque da newsletter | Sem texto |", local)
        self.assertIn("| Sugestão de FAQ | Sem texto |", local)


if __name__ == "__main__":
    unittest.main()
