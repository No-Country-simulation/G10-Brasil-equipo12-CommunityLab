"""Salva o pacote de ativos gerado no OCI Object Storage (camada Always Free).

Autenticação: arquivo de configuração da OCI (padrão ~/.oci/config), criado fora do
repositório. NUNCA coloque chaves, OCIDs ou o conteúdo desse arquivo no GitHub.

Variáveis opcionais no .env:
    OCI_BUCKET        nome do bucket (padrão: communitylab-ativos-marketing)
    OCI_CONFIG_FILE   caminho do arquivo de configuração (padrão: ~/.oci/config)
    OCI_PROFILE       perfil dentro do arquivo (padrão: DEFAULT)
"""
import json
import os
import re
from datetime import datetime

BUCKET_PADRAO = "communitylab-ativos-marketing"


def montar_caminho(periodo_referencia: str, ano: int | None = None) -> str:
    """'Semana_04' -> 'ativos/2026-semana-04/pacote-distribuicao.json' (padrão do PDF)."""
    ano = ano or datetime.now().year
    pasta = re.sub(r"[^a-z0-9]+", "-", periodo_referencia.lower()).strip("-")
    return f"ativos/{ano}-{pasta}/pacote-distribuicao.json"


def montar_caminho_relatorio(periodo_referencia: str, ano: int | None = None) -> str:
    """'Semana_04' -> 'ativos/2026-semana-04/relatorio-comunidade.md' (ao lado do pacote)."""
    pasta = montar_caminho(periodo_referencia, ano).rsplit("/", 1)[0]
    return f"{pasta}/relatorio-comunidade.md"


def _enviar(conteudo: bytes, caminho: str, cliente=None, content_type: str | None = None) -> dict:
    """Envia os bytes ao bucket e devolve o bloco 'armazenamento_oci' (nunca levanta erro).

    `cliente` existe só para testes (permite passar um cliente falso).
    """
    bucket = os.getenv("OCI_BUCKET", BUCKET_PADRAO)
    resultado = {"bucket": bucket, "caminho_objeto": caminho, "status": "falha_ao_salvar"}

    try:
        if cliente is None:
            import oci  # importado aqui para o resto do projeto rodar sem o SDK

            config = oci.config.from_file(
                os.getenv("OCI_CONFIG_FILE", "~/.oci/config"),
                os.getenv("OCI_PROFILE", "DEFAULT"),
            )
            oci.config.validate_config(config)
            cliente = oci.object_storage.ObjectStorageClient(config)

        namespace = cliente.get_namespace().data
        if content_type:
            cliente.put_object(namespace, bucket, caminho, conteudo, content_type=content_type)
        else:
            cliente.put_object(namespace, bucket, caminho, conteudo)
        resultado["status"] = "salvo_com_sucesso"
    except Exception as erro:  # mostra o tipo do erro, nunca dados da configuração
        resultado["detalhe_erro"] = type(erro).__name__
    return resultado


def salvar_no_oci(pacote: dict, periodo_referencia: str = "Semana_04", cliente=None) -> dict:
    """Envia o pacote (dict) como JSON para o bucket e devolve o bloco 'armazenamento_oci'."""
    corpo = json.dumps(pacote, ensure_ascii=False, indent=2).encode("utf-8")
    return _enviar(corpo, montar_caminho(periodo_referencia), cliente=cliente)


def salvar_relatorio_no_oci(relatorio: str, periodo_referencia: str = "Semana_04", cliente=None) -> dict:
    """Envia o relatório (texto Markdown) para o bucket, ao lado do pacote, e devolve o mesmo bloco de status."""
    return _enviar(
        relatorio.encode("utf-8"),
        montar_caminho_relatorio(periodo_referencia),
        cliente=cliente,
        content_type="text/markdown; charset=utf-8",
    )
