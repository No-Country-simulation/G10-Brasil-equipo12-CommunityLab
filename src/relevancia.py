# src/relevancia.py
"""Módulo de cálculo de pontuação de relevância para interações da comunidade."""

def calcular_pontuacao_interacao(interacao: dict) -> int:
    """
    Calcula a pontuação de relevância de uma interação individual com base em critérios
    como tipo, presença de palavras-chave de impacto (vagas, conquistas, projetos) e engajamento.
    """
    pontos = 0
    texto = interacao.get("texto", "").lower()
    tipo = interacao.get("tipo", "").lower()

    # 1. Pontuação base por tipo de interação
    if "depoimento" in tipo or "conquista" in tipo or "vaga" in tipo:
        pontos += 40
    elif "pergunta" in tipo or "duvida" in tipo:
        pontos += 25
    else:
        pontos += 10

    # 2. Pesos por palavras-chave de alto valor para o marketing da comunidade
    palavras_chave_altas = ["contratada", "emprego", "estágio", "vaga", "aprovado", "aprovada", "freela", "projeto", "deploy"]
    for palavra in palavras_chave_altas:
        if palavra in texto:
            pontos += 15

    # 3. Bonificação por tamanho substancial do texto (relatos mais detalhados geram melhores histórias)
    if len(texto) > 100:
        pontos += 20

    return min(pontos, 100)  # Teto máximo de 100 pontos


def filtrar_e_ordenar_por_relevancia(interacoes: list[dict], limite: int = 5) -> list[dict]:
    """
    Atribui pontuação a cada interação, ordena do mais relevante para o menos relevante
    e retorna as principais interações filtradas pelo limite desejado.
    """
    interacoes_pontuadas = []
    
    for interacao in interacoes:
        score = calcular_pontuacao_interacao(interacao)
        # Cria uma cópia incluindo o campo de pontuação
        interacao_com_score = {**interacao, "pontuacao_relevancia": score}
        interacoes_pontuadas.append(interacao_com_score)

    # Ordena de forma decrescente pela pontuação (maior relevância primeiro)
    ordenadas = sorted(interacoes_pontuadas, key=lambda x: x["pontuacao_relevancia"], reverse=True)

    return ordenadas[:limite]