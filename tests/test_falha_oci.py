"""Testa a resiliência do pipeline quando o OCI falha."""
import json
import unittest
from pathlib import Path

from src.pipeline import processar_lote
from tests.test_ia_service import ANALISE_VALIDA, ClienteFalso


class ClienteOciComFalha:
    """Simula um cliente OCI que falha com exceção ao tentar salvar."""
    def put_object(self, *args, **kwargs):
        raise RuntimeError("Erro simulado: 500 Conexão recusada com OCI Object Storage")


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

        pasta_temporaria = Path("saida_teste_falha")
        cliente_llm = ClienteFalso([json.dumps(ANALISE_VALIDA)])
        cliente_oci_com_erro = ClienteOciComFalha()

        try:
            # 2. Executa o pipeline com OCI ativado, mas usando o cliente falso que falha
            resposta = processar_lote(
                lote,
                salvar_oci=True,
                pasta_saida=pasta_temporaria,
                cliente_llm=cliente_llm,
                cliente_oci=cliente_oci_com_erro,
            )

            # 3. Critérios de validação da Bruna:
            # a) O pipeline não quebrou e devolveu 'falha_ao_salvar'
            self.assertEqual(resposta.armazenamento_oci.status, "falha_ao_salvar")

            # b) A cópia local foi gravada com sucesso em disco
            arquivo_esperado = pasta_temporaria / "2026-semana-teste-falha_pacote-distribuicao.json"
            self.assertTrue(arquivo_esperado.exists(), "A cópia local deveria existir mesmo com erro no OCI")

        finally:
            # Limpeza dos arquivos temporários de teste
            arquivo_esperado = pasta_temporaria / "2026-semana-teste-falha_pacote-distribuicao.json"
            if arquivo_esperado.exists():
                arquivo_esperado.unlink()
            if pasta_temporaria.exists():
                pasta_temporaria.rmdir()


if __name__ == "__main__":
    unittest.main()