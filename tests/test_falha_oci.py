"""Testa a resiliência do pipeline quando o OCI falha."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.pipeline import processar_lote
from tests.test_ia_service import ANALISE_VALIDA, ClienteFalso


class ClienteOciComFalha:
    """Simula um cliente OCI cujo envio (put_object) falha com exceção."""

    def get_namespace(self):
        """Retorna uma resposta simulada para a consulta de namespace."""
        resposta = MagicMock()
        resposta.data = "namespace_simulado"
        return resposta

    def put_object(self, *args, **kwargs):
        """Lança erro simulado na operação de upload para o bucket."""
        raise RuntimeError("Erro simulado: 500 Falha ao salvar objeto no OCI Object Storage")


class TestFalhaOci(unittest.TestCase):
    def test_falha_oci_devolve_status_e_mantem_copia_local(self):
        # 1. Dados de entrada
        lote = {
            "origem_comunidade": "Discord_Grupo_ONE_G10",
            "periodo_referencia": "Semana_Teste_Falha",
            "interacoes": [
                {
                    "id": "T1",
                    "autor": "Participante Teste",
                    "canal": "#conquistas",
                    "tipo": "depoimento",
                    "texto": "Teste de resiliência OCI",
                }
            ],
        }

        cliente_llm = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        cliente_oci_com_erro = ClienteOciComFalha()

        # 2. Usa TemporaryDirectory conforme sugestão de boas práticas
        with tempfile.TemporaryDirectory() as pasta_temp:
            pasta_saida = Path(pasta_temp)

            # Executa o pipeline com OCI ativado e cliente simulado com falha
            resposta = processar_lote(
                lote,
                salvar_oci=True,
                pasta_saida=pasta_saida,
                cliente_llm=cliente_llm,
                cliente_oci=cliente_oci_com_erro,
            )

            # 3. Validações:
            # a) O pipeline não quebrou e devolveu 'falha_ao_salvar'
            self.assertEqual(resposta.armazenamento_oci.status, "falha_ao_salvar")

            # b) Valida o detalhe do erro capturado
            self.assertIn("RuntimeError", resposta.armazenamento_oci.detalhe_erro)

            # c) A cópia local foi gravada com sucesso no diretório temporário
            arquivo_esperado = pasta_saida / "2026-semana-teste-falha_pacote-distribuicao.json"
            self.assertTrue(arquivo_esperado.exists(), "A cópia local deveria existir mesmo com erro no OCI")


if __name__ == "__main__":
    unittest.main()