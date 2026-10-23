import re


def limpar_texto(texto: str) -> str:
    """
    Remove espaços extras, quebras de linha excessivas e caracteres especiais indesejados do texto.
    """
    if not isinstance(texto, str):
        return ""

    # Remove quebras de linha duplicadas e espaços em excesso
    texto_limpo = re.sub(r"\s+", " ", texto)

    # Remove espaços no início e no fim
    return texto_limpo.strip()


def limpar_dados_comunidade(dadosbrutos: dict) -> dict:
    """
    Recebe o dicionário bruto lido do JSON/CSV e aplica regras de limpeza
    em todas as interações da comunidade.
    """
    # Cria uma cópia para não alterar o dicionário original diretamente
    dados_tratados = dadosbrutos.copy()
    interacoes_limpas = []
    ids_usados = set()

    for posicao, interacao in enumerate(dadosbrutos.get("interacoes") or [], start=1):
        if not isinstance(interacao, dict):
            continue
        # Valida se os campos essenciais existem e limpa o texto
        id_interacao = limpar_texto(str(interacao.get("id") or "")) or f"MSG_{posicao:03d}"
        autor = limpar_texto(interacao.get("autor", "Desconhecido"))
        canal = limpar_texto(interacao.get("canal", "#geral"))
        tipo = limpar_texto(interacao.get("tipo", "geral"))
        texto = limpar_texto(interacao.get("texto", ""))

        # Ignora interações que estejam com o texto totalmente vazio
        if texto:
            # O id liga o resultado da LLM de volta à mensagem original, então precisa ser único
            id_base, sufixo = id_interacao, posicao
            while id_interacao in ids_usados:
                id_interacao = f"{id_base}_{sufixo}"
                sufixo += 1
            ids_usados.add(id_interacao)
            interacoes_limpas.append(
                {
                    "id": id_interacao,
                    "autor": autor if autor else "Desconhecido",
                    "canal": canal if canal else "#geral",
                    "tipo": tipo if tipo else "geral",
                    "texto": texto,
                }
            )

    dados_tratados["interacoes"] = interacoes_limpas
    dados_tratados["total_interacoes_validas"] = len(interacoes_limpas)

    return dados_tratados
