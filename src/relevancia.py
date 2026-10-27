# src/relevancia.py
"""Módulo de cálculo de pontuação de relevância para interações da comunidade."""
import re
import unicodedata

# Tipos de relato com maior valor para o marketing da comunidade
TIPOS_ALTO_VALOR = ("depoimento", "entrega_projeto", "conquista", "vaga")
TIPOS_DUVIDA = ("pergunta", "duvida")

# Palavras-chave de alto valor. São comparadas SEM acento e como palavra inteira,
# para não casar "vaga" dentro de "devagar" nem perder "estagio" escrito sem acento.
PALAVRAS_CHAVE_ALTAS = [
    r"contratad[oa]s?", r"empregos?", r"est[aá]gios?", r"vagas?",
    r"aprovad[oa]s?", r"freelas?", r"freelances?", r"projetos?", r"deploys?",
    r"passei", r"processo seletivo",
]


def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos: 'Estágio' e 'estagio' viram a mesma coisa."""
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


_REGEX_CHAVES = [re.compile(r"\b" + _normalizar(p) + r"\b") for p in PALAVRAS_CHAVE_ALTAS]


def calcular_pontuacao_interacao(interacao: dict) -> int:
    """
    Calcula a pontuação de relevância (0 a 100) de uma interação individual com base
    no tipo, na presença de palavras-chave de impacto (vagas, conquistas, projetos)
    e, para relatos, no nível de detalhe do texto.
    """
    pontos = 0
    texto_original = interacao.get("texto", "") or ""
    texto = _normalizar(texto_original)
    tipo = _normalizar(interacao.get("tipo", "") or "")

    # 1. Pontuação base por tipo de interação
    relato_de_valor = any(t in tipo for t in TIPOS_ALTO_VALOR)
    if relato_de_valor:
        pontos += 40
    elif any(t in tipo for t in TIPOS_DUVIDA):
        pontos += 25
    else:
        pontos += 10

    # 2. Pesos por palavras-chave de alto valor para o marketing da comunidade
    for regex in _REGEX_CHAVES:
        if regex.search(texto):
            pontos += 15

    # 3. Bonificação por tamanho: só vale para relatos (depoimentos e entregas),
    #    onde um texto mais detalhado rende uma história melhor. Em dúvidas e
    #    conversas, texto longo não significa mais valor para o marketing.
    if relato_de_valor and len(texto_original) > 100:
        pontos += 20

    return min(pontos, 100)  # Teto máximo de 100 pontos


def filtrar_e_ordenar_por_relevancia(interacoes: list[dict], limite: int | None = None) -> list[dict]:
    """
    Atribui pontuação a cada interação e ordena da mais relevante para a menos relevante.

    Por padrão (limite=None) devolve TODAS as interações, só reordenadas. Cortar o lote
    mudaria a contagem de interações processadas e o sentimento da comunidade, e deixaria
    de fora tipos inteiros (por exemplo, as dúvidas técnicas que alimentam o FAQ).
    Use `limite` apenas quando houver um motivo explícito, como o limite de tokens da API.
    """
    interacoes_pontuadas = []

    for interacao in interacoes:
        score = calcular_pontuacao_interacao(interacao)
        # Cria uma cópia incluindo o campo de pontuação
        interacao_com_score = {**interacao, "pontuacao_relevancia": score}
        interacoes_pontuadas.append(interacao_com_score)

    # Ordena de forma decrescente pela pontuação (maior relevância primeiro).
    # sorted() é estável: em empate, mantém a ordem original do lote.
    ordenadas = sorted(interacoes_pontuadas, key=lambda x: x["pontuacao_relevancia"], reverse=True)

    return ordenadas if limite is None else ordenadas[:limite]
