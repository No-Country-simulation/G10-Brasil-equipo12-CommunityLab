# src/relevancia.py
"""Módulo de cálculo de pontuação de relevância para interações da comunidade."""
import re
import unicodedata

# Quantas mensagens, no máximo, vão para a LLM. Existe por causa do limite de tokens por
# minuto do plano gratuito da Groq (8.000 no modelo atual): prompt + mensagens precisam caber.
# Com os guias atuais (~20 mil caracteres), 10 mensagens deixam alguma folga; 15 estouram.
LIMITE_AMOSTRA_PADRAO = 10

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


def _grupo(interacao: dict) -> str:
    """Relatos de valor, dúvidas ou outros: usado para a amostra não esquecer nenhum tipo."""
    tipo = _normalizar(interacao.get("tipo", "") or "")
    if any(t in tipo for t in TIPOS_ALTO_VALOR):
        return "relatos"
    if any(t in tipo for t in TIPOS_DUVIDA):
        return "duvidas"
    return "outros"


# Peso de cada grupo na amostra: relatos alimentam o marketing, uma dúvida basta para o FAQ
# e as conversas gerais ajudam o sentimento a refletir a comunidade. Com limite 10: 5, 3 e 2.
PESOS_AMOSTRA = {"relatos": 5, "duvidas": 3, "outros": 2}


def _cotas(limite: int) -> dict:
    """Divide `limite` vagas entre os grupos, proporcional aos pesos (maiores restos ficam com as sobras)."""
    total_pesos = sum(PESOS_AMOSTRA.values())
    cotas = {g: limite * peso // total_pesos for g, peso in PESOS_AMOSTRA.items()}
    restos = sorted(
        PESOS_AMOSTRA,
        key=lambda g: (-(limite * PESOS_AMOSTRA[g] % total_pesos), -PESOS_AMOSTRA[g]),
    )
    for g in restos[: limite - sum(cotas.values())]:
        cotas[g] += 1
    return cotas


def selecionar_amostra(interacoes: list[dict], limite: int | None = LIMITE_AMOSTRA_PADRAO) -> list[dict]:
    """
    Escolhe até `limite` mensagens para a LLM, sem deixar nenhum tipo de fora.

    1. Pontua e ordena todas por relevância.
    2. Se o lote cabe no limite (ou limite é None/0), devolve tudo, só ordenado.
    3. Se não cabe, divide as vagas entre relatos, dúvidas e outros conforme PESOS_AMOSTRA
       (com limite 10: 5, 3 e 2) e pega as melhores de cada grupo. Se um grupo tem menos
       mensagens que a sua cota, a sobra vai para os outros, na ordem relatos, dúvidas, outros.
    4. O resultado fica ordenado por relevância. Empates mantêm a ordem original.

    Quem chama deve guardar o total do lote antes: a contagem oficial é a do lote inteiro.
    """
    pontuadas = filtrar_e_ordenar_por_relevancia(interacoes)
    if not limite or limite <= 0 or len(pontuadas) <= limite:
        return pontuadas

    filas = {g: [] for g in PESOS_AMOSTRA}
    for interacao in pontuadas:
        filas[_grupo(interacao)].append(interacao)

    escolhidas = []
    for grupo, cota in _cotas(limite).items():
        escolhidas.extend(filas[grupo][:cota])
        filas[grupo] = filas[grupo][cota:]

    # Sobras de grupos pequenos vão para quem ainda tem mensagens, por ordem de prioridade
    while len(escolhidas) < limite and any(filas.values()):
        for grupo in PESOS_AMOSTRA:
            if filas[grupo] and len(escolhidas) < limite:
                escolhidas.append(filas[grupo].pop(0))

    ids = {id(i) for i in escolhidas}
    return [i for i in pontuadas if id(i) in ids]
