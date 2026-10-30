# src/pipeline.py
"""Ponto de entrada único do CommunityLab.

    from src.pipeline import processar_lote
    resposta = processar_lote(lote)          # lote = dict no formato de entrada do PDF
    resposta.para_dict()                     # dict no formato de saída do PDF

Linha de comando:
    python -m src.pipeline                              # analisa dados/mensagens_exemplo.json
    python -m src.pipeline dados/dataset_simulado.json  # outro arquivo
    python -m src.pipeline --oci --periodo Semana_Teste # também envia ao OCI (use período de teste!)
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from src.ia_service import ErroServicoLLM, analisar_lote
from src.ingestao import ler_mensagens_comunidade, validar_lote
from src.limpeza import limpar_dados_comunidade
from src.relevancia import LIMITE_AMOSTRA_PADRAO, selecionar_amostra
from src.oracle_storage import BUCKET_PADRAO, montar_caminho, salvar_no_oci
from src.schemas import ArmazenamentoOci, LoteEntrada, RespostaCommunityLab, montar_resposta

load_dotenv(override=True)

PASTA_SAIDA_PADRAO = "saida"

logger = logging.getLogger(__name__)


class ErroLoteVazio(ValueError):
    """Depois da limpeza não sobrou nenhuma interação com texto."""


def caminho_local(periodo_referencia: str, pasta_saida: str = PASTA_SAIDA_PADRAO) -> Path:
    """'Semana_04' -> saida/2026-semana-04_pacote-distribuicao.json"""
    nome = montar_caminho(periodo_referencia).removeprefix("ativos/").replace("/", "_")
    return Path(pasta_saida) / nome


def processar_lote(
    lote: dict,
    salvar_oci: bool = False,
    pasta_saida: Optional[str] = PASTA_SAIDA_PADRAO,
    tentativas: int = 3,
    limite_amostra: Optional[int] = LIMITE_AMOSTRA_PADRAO,
    cliente_llm=None,
    cliente_oci=None,
) -> RespostaCommunityLab:
    """Executa o fluxo completo: valida, limpa, pontua relevância, analisa com a LLM,
    monta a resposta, (opcionalmente) envia ao OCI e grava uma cópia local em UTF-8.

    salvar_oci=False por padrão de propósito: enviar sobrescreve o objeto do período
    no bucket. Para testar, use um período de teste (ex.: "Semana_Teste").
    Em caso de falha da LLM levanta ErroAnaliseLLM ou ErroServicoLLM; lote inválido
    levanta ValueError; falha ao salvar no OCI NÃO levanta erro: o motivo vai em
    armazenamento_oci (status "falha_ao_salvar").

    limite_amostra: máximo de mensagens enviadas à LLM (padrão 10, por causa do limite de
    tokens do plano gratuito). Lotes maiores são reduzidos por relevância e por tipo; o total
    informado na resposta continua sendo o do lote inteiro, mas o sentimento e os tópicos
    refletem a amostra. Use None ou 0 para enviar tudo.

    cliente_llm e cliente_oci existem para testes (clientes falsos).
    """
    dados = validar_lote(lote)
    dados_limpos = limpar_dados_comunidade(dados)

    if not dados_limpos.get("interacoes"):
        raise ErroLoteVazio("Nenhuma interação com texto sobrou depois da limpeza.")

    # A contagem oficial é a do lote inteiro, mesmo que a LLM analise só uma amostra
    total_lote = len(dados_limpos["interacoes"])
    dados_limpos["interacoes"] = selecionar_amostra(dados_limpos["interacoes"], limite_amostra)
    if len(dados_limpos["interacoes"]) < total_lote:
        logger.warning(
            "Lote com %d mensagens: a LLM analisou uma amostra de %d (por relevância e tipo). "
            "Sentimento e tópicos refletem a amostra.",
            total_lote,
            len(dados_limpos["interacoes"]),
        )
    
    lote_valido = LoteEntrada.model_validate(dados_limpos)
    periodo = lote_valido.periodo_referencia

    analise = analisar_lote(dados_limpos, tentativas=tentativas, cliente=cliente_llm)

    oci = ArmazenamentoOci(
        bucket=os.getenv("OCI_BUCKET", BUCKET_PADRAO),
        caminho_objeto=montar_caminho(periodo),
        status="pendente_upload",
    )
    resposta = montar_resposta(lote_valido, analise, oci, total_interacoes=total_lote)

    if salvar_oci:
        # O arquivo guardado no bucket não carrega o próprio status de envio
        pacote = resposta.para_dict()
        pacote.pop("armazenamento_oci", None)
        resultado = salvar_no_oci(pacote, periodo, cliente=cliente_oci)
        resposta = resposta.model_copy(update={"armazenamento_oci": ArmazenamentoOci(**resultado)})

    if pasta_saida:
        destino = caminho_local(periodo, pasta_saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(resposta.para_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    return resposta


def _garantir_saida_utf8() -> None:
    """Força a saída do terminal em UTF-8.

    No Windows, quando a saída é redirecionada (arquivo, pipe, Measure-Command),
    o Python usa cp1252 e quebra ao imprimir emojis como 🎉 (UnicodeEncodeError).
    """
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass  # fluxo sem suporte a reconfigure: segue como está


def main(argv=None) -> int:
    _garantir_saida_utf8()
    parser = argparse.ArgumentParser(description="CommunityLab: transforma interações em ativos de distribuição.")
    parser.add_argument("arquivo", nargs="?", default="dados/mensagens_exemplo.json", help="arquivo .json ou .csv")
    parser.add_argument("--oci", action="store_true", help="envia o pacote ao OCI Object Storage")
    parser.add_argument("--periodo", help="substitui o periodo_referencia do arquivo (ex.: Semana_Teste)")
    parser.add_argument(
        "--limite",
        type=int,
        default=LIMITE_AMOSTRA_PADRAO,
        help="máximo de mensagens enviadas à LLM (padrão %(default)s; 0 = sem limite)",
    )
    args = parser.parse_args(argv)

    try:
        lote = ler_mensagens_comunidade(args.arquivo)
        if args.periodo:
            lote["periodo_referencia"] = args.periodo
        resposta = processar_lote(lote, salvar_oci=args.oci, limite_amostra=args.limite)
    except (ValueError, FileNotFoundError, ErroServicoLLM) as erro:
        print(f"❌ {erro}")
        return 1

    print(json.dumps(resposta.para_dict(), indent=2, ensure_ascii=False))
    print(f"\nCópia local: {caminho_local(lote['periodo_referencia'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())