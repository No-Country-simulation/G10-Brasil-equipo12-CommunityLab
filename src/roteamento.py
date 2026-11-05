# src/roteamento.py
"""Roteamento em código (docs/regras_roteamento.md, seção 1 e decisões 7 e 8).

A rota é pelo tipo da mensagem. O código age em dois momentos:

ANTES da LLM: cada mensagem recebe uma rota (`rota_da_mensagem`) e o lote ganha a lista dos
ativos que têm material (`ativos_com_material`). Só esses ativos são pedidos à LLM.

DEPOIS da LLM (`aplicar_regras_de_roteamento`): o código confere a resposta e descarta
(deixa `null`) o que não tem mensagem de origem, caso a LLM erre.

1. Cada ativo só existe se o lote tiver uma mensagem do tipo certo:
   post de LinkedIn: depoimento ou entrega_projeto;
   destaque de newsletter: depoimento, entrega_projeto ou feedback;
   sugestão de FAQ: pergunta_tecnica.
2. Post e newsletter não podem citar o nome de quem só escreveu pergunta técnica ou conversa
   geral (esses autores não autorizaram virar destaque público).

Todo descarte vai para o log. O log NÃO traz o nome da pessoa.
"""
import logging
import re
import unicodedata

from src.limpeza import AUTOR_ANONIMO
from src.schemas import AnaliseLLM

logger = logging.getLogger(__name__)

# Tipos de mensagem que permitem cada ativo (tabela da seção 1 de regras_roteamento.md)
TIPOS_POR_ATIVO = {
    "post_linkedin": ("depoimento", "entrega_projeto"),
    "destaque_newsletter_semanal": ("depoimento", "entrega_projeto", "feedback"),
    "sugestao_conteudo_faq": ("pergunta_tecnica",),
}

ATIVOS = tuple(TIPOS_POR_ATIVO)  # ordem canônica: post, newsletter, FAQ


def rota_da_mensagem(tipo: str) -> tuple:
    """Ativos que uma mensagem deste tipo pode alimentar. Tipo desconhecido ou conversa geral: nenhum."""
    tipo = _normalizar(tipo)
    return tuple(a for a in ATIVOS if tipo in TIPOS_POR_ATIVO[a])


def rotear_interacoes(interacoes: list[dict]) -> dict:
    """Ramificações: para cada ativo, as mensagens do lote que podem alimentá-lo (podem ser nenhuma)."""
    return {a: [i for i in interacoes if a in rota_da_mensagem(i.get("tipo", ""))] for a in ATIVOS}


def ativos_com_material(interacoes: list[dict]) -> tuple:
    """Ativos que têm pelo menos uma mensagem do tipo certo, na ordem canônica.
    Os demais não são pedidos à LLM e ficam `null` na resposta."""
    ramos = rotear_interacoes(interacoes)
    pedidos = tuple(a for a in ATIVOS if ramos[a])
    for a in ATIVOS:
        if a not in pedidos:
            logger.info("Sem material para '%s' neste lote: o ativo não será pedido à LLM.", a)
    return pedidos


# Quem escreveu um destes tipos pode ser citado em conteúdo público
TIPOS_QUE_LIBERAM_O_AUTOR = ("depoimento", "entrega_projeto", "feedback")

# Campos de texto livre dos ativos públicos onde um nome poderia aparecer.
# Ficam de fora campos fixos como "secao" ("Vitória da Semana"), para não confundir com um nome.
CAMPOS_PUBLICOS = {
    "post_linkedin": ("titulo", "copy_"),
    "destaque_newsletter_semanal": ("chamada", "resumo"),
}

TAMANHO_MINIMO_PRIMEIRO_NOME = 3


def _normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in decomposto if not unicodedata.combining(c)).strip().casefold()


def _tipos_do_lote(interacoes: list[dict]) -> set:
    return {_normalizar(i.get("tipo", "")) for i in interacoes}


def _primeiro_nome(autor: str):
    """'Rafael Tavares' -> 'rafael'. Apelidos sem espaço (ex.: 'luan_dev22') não têm primeiro nome."""
    partes = _normalizar(autor).split()
    if len(partes) > 1 and len(partes[0]) >= TAMANHO_MINIMO_PRIMEIRO_NOME:
        return partes[0]
    return None


def _nomes_protegidos(interacoes: list[dict]) -> list[str]:
    """
    Nomes (normalizados) que não podem aparecer em post nem newsletter: o nome completo e o
    primeiro nome de quem, no lote, só escreveu pergunta técnica ou conversa geral.

    O primeiro nome só entra se nenhuma pessoa liberada (com depoimento, entrega ou feedback)
    tiver o mesmo primeiro nome: assim, dois "Rafael" não fazem a checagem descartar um post
    legítimo sobre o Rafael que contou uma conquista.
    """
    tipos_por_autor: dict[str, set] = {}
    for i in interacoes:
        autor = (i.get("autor") or "").strip()
        if not autor or autor == AUTOR_ANONIMO:
            continue
        tipos_por_autor.setdefault(autor, set()).add(_normalizar(i.get("tipo", "")))

    liberados = {a for a, t in tipos_por_autor.items() if t & set(TIPOS_QUE_LIBERAM_O_AUTOR)}
    primeiros_liberados = {p for p in (_primeiro_nome(a) for a in liberados) if p}

    protegidos = []
    for autor in tipos_por_autor:
        if autor in liberados:
            continue
        protegidos.append(_normalizar(autor))
        primeiro = _primeiro_nome(autor)
        if primeiro and primeiro not in primeiros_liberados:
            protegidos.append(primeiro)
    return protegidos


def _cita(texto_normalizado: str, nome: str) -> bool:
    """O nome aparece como palavra inteira ('ana' não casa com 'banana')."""
    return re.search(r"(?<!\w)" + re.escape(nome) + r"(?!\w)", texto_normalizado) is not None


def aplicar_regras_de_roteamento(analise: AnaliseLLM, interacoes: list[dict]) -> AnaliseLLM:
    """
    Devolve a análise sem os ativos que não têm mensagem de origem (viram None).

    `interacoes` deve ser exatamente o que foi enviado à LLM (a amostra, já com os autores
    de conversa geral trocados por "Participante"). Não altera a análise recebida.
    """
    ativos = analise.ativos_distribuicao_gerados
    tipos = _tipos_do_lote(interacoes)
    descartes = {}

    # Regra 8: o ativo só existe se houver mensagem do tipo certo
    for nome_ativo, tipos_certos in TIPOS_POR_ATIVO.items():
        if getattr(ativos, nome_ativo) is not None and not (tipos & set(tipos_certos)):
            descartes[nome_ativo] = None
            logger.warning(
                "Ativo '%s' descartado: o lote enviado à LLM não tem mensagem do tipo %s.",
                nome_ativo,
                " ou ".join(tipos_certos),
            )

    # Regra 7: post e newsletter não citam quem só fez pergunta técnica ou conversa geral
    protegidos = _nomes_protegidos(interacoes)
    for nome_ativo, campos in CAMPOS_PUBLICOS.items():
        ativo = getattr(ativos, nome_ativo)
        if ativo is None or nome_ativo in descartes:
            continue
        texto = _normalizar(" ".join(getattr(ativo, c) for c in campos))
        if any(_cita(texto, nome) for nome in protegidos):
            descartes[nome_ativo] = None
            logger.warning(
                "Ativo '%s' descartado: cita o nome de um autor que só tem pergunta técnica "
                "ou conversa geral no lote.",
                nome_ativo,
            )

    if not descartes:
        return analise
    return analise.model_copy(update={"ativos_distribuicao_gerados": ativos.model_copy(update=descartes)})
