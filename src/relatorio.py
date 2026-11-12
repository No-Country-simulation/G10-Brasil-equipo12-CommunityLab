"""Relatório da semana em Markdown: números e resumos, SEM nomes de pessoas e SEM trechos de mensagens.

O manual do hackathon pede que o OCI guarde "textos formatados, relatórios e JSONs". O pacote JSON já
guarda os textos; este relatório é o resumo legível para pessoas, guardado ao lado dele no bucket
(`ativos/<ano>-<período>/relatorio-comunidade.md`).

O que entra (e só isto): período, total de mensagens, quantas foram analisadas pela IA, sentimento
predominante, tópicos principais, situação de cada ativo (gerado ou sem texto, com o motivo) e o resultado
do envio. Os tópicos vêm da LLM e podem citar uma pessoa: por isso qualquer tópico com o nome (completo ou
primeiro nome) de um autor do lote é omitido.
"""
from datetime import datetime
from typing import Iterable, Optional

from src.roteamento import ATIVOS, _cita, _normalizar, _primeiro_nome
from src.schemas import RespostaCommunityLab

NOMES_DOS_ATIVOS = {
    "post_linkedin": "Post para o LinkedIn",
    "destaque_newsletter_semanal": "Destaque da newsletter",
    "sugestao_conteudo_faq": "Sugestão de FAQ",
}

# Por que um ativo não foi gerado. A rota (docs/regras_roteamento.md) decide se ele chega a ser pedido à IA.
MOTIVO_SEM_MATERIAL = "Nenhuma mensagem do tipo necessário neste lote."
MOTIVO_SEM_TEXTO = (
    "Pedido à IA, mas sem texto no final: a IA não gerou ou a checagem do código o descartou "
    "(por exemplo, por citar um nome que não pode aparecer)."
)

TEXTO_ENVIO = {
    "salvo_com_sucesso": "Enviado ao OCI.",
    "falha_ao_salvar": "Falha ao enviar ao OCI.",
}

AVISO_SEM_DADOS_PESSOAIS = (
    "Este relatório traz só números e resumos: não inclui nomes nem trechos de mensagens. "
    "Os textos prontos estão no pacote (`pacote-distribuicao.json`) e passam por revisão humana antes de publicar."
)


def _nomes_a_omitir(autores: Iterable[str]) -> list:
    """Nome completo e primeiro nome (normalizados) de todos os autores do lote."""
    nomes = []
    for autor in autores:
        completo = _normalizar(autor or "")
        if not completo:
            continue
        nomes.append(completo)
        primeiro = _primeiro_nome(autor)
        if primeiro:
            nomes.append(primeiro)
    return nomes


def topicos_sem_nomes(topicos: Iterable[str], autores: Iterable[str]) -> tuple:
    """Devolve (tópicos que não citam nenhum autor, quantos foram omitidos). Tópico vira uma linha só."""
    nomes = _nomes_a_omitir(autores)
    mantidos, omitidos = [], 0
    for topico in topicos:
        linha = " ".join(str(topico).split())
        if not linha:
            continue
        texto = _normalizar(linha)
        if any(_cita(texto, nome) for nome in nomes):
            omitidos += 1
        else:
            mantidos.append(linha)
    return mantidos, omitidos


def montar_relatorio(
    resposta: RespostaCommunityLab,
    periodo: str,
    total_amostra: int,
    ativos_pedidos: Iterable[str],
    autores: Iterable[str],
    agora: Optional[datetime] = None,
    caminho_relatorio: str = "",
) -> str:
    """Monta o relatório em Markdown a partir da resposta do pipeline.

    - total do lote: `resposta.resumo_comunidade.total_interacoes_processadas` (depois da limpeza);
    - `total_amostra`: quantas mensagens a IA realmente analisou;
    - `ativos_pedidos`: os ativos que o roteamento pediu à IA (os demais não tinham material);
    - `autores`: autores de TODO o lote, só para omitir tópicos que os citem.
    """
    resumo = resposta.resumo_comunidade
    ativos = resposta.ativos_distribuicao_gerados
    pedidos = set(ativos_pedidos)
    momento = (agora or datetime.now()).strftime("%d/%m/%Y %H:%M")
    total = resumo.total_interacoes_processadas

    linhas = [
        f"# Relatório da semana: {periodo}",
        "",
        f"Gerado em {momento}.",
        "",
        "## Resumo",
        "",
        "| Item | Valor |",
        "| :--- | :--- |",
        f"| Período | {periodo} |",
        f"| Mensagens processadas (depois da limpeza) | {total} |",
        f"| Mensagens analisadas pela IA (amostra) | {total_amostra} |",
        f"| Sentimento predominante | {resumo.sentimento_predominante} |",
        "",
    ]
    if total_amostra < total:
        linhas += [
            f"> A IA analisou uma amostra de {total_amostra} entre {total} mensagens, escolhida por relevância e "
            "tipo: o sentimento e os tópicos refletem a amostra.",
            "",
        ]

    topicos, omitidos = topicos_sem_nomes(resumo.topicos_principais, autores)
    linhas += ["## Tópicos principais", ""]
    linhas += [f"- {t}" for t in topicos] or ["- Nenhum tópico disponível."]
    if omitidos:
        linhas += ["", f"{omitidos} tópico(s) omitido(s) por citar o nome de uma pessoa."]
    linhas += ["", "## Ativos de distribuição", "", "| Ativo | Situação | Observação |", "| :--- | :--- | :--- |"]
    for chave in ATIVOS:
        if getattr(ativos, chave) is not None:
            situacao, obs = "Gerado", "Texto no pacote, para revisão humana."
        elif chave in pedidos:
            situacao, obs = "Sem texto", MOTIVO_SEM_TEXTO
        else:
            situacao, obs = "Sem material", MOTIVO_SEM_MATERIAL
        linhas.append(f"| {NOMES_DOS_ATIVOS[chave]} | {situacao} | {obs} |")

    linhas += ["", "## Envio ao OCI", ""]
    oci = resposta.armazenamento_oci
    if oci is None or oci.status == "pendente_upload":
        # Sem envio não há objeto no bucket: não mostramos um caminho que ainda não existe
        linhas.append("- Pacote: não enviado ao OCI nesta execução.")
    else:
        linhas.append(f"- Pacote: {TEXTO_ENVIO.get(oci.status, oci.status)} (status: `{oci.status}`)")
        linhas.append(f"- Bucket: `{oci.bucket}`")
        linhas.append(f"- Objeto do pacote: `{oci.caminho_objeto}`")
        if oci.detalhe_erro:
            linhas.append(f"- Tipo do erro: `{oci.detalhe_erro}`")
    if caminho_relatorio:
        linhas.append(f"- Objeto deste relatório: `{caminho_relatorio}`")
    linhas += ["", "---", "", AVISO_SEM_DADOS_PESSOAIS, ""]
    return "\n".join(linhas)
