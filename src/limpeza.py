import re

def limpar_texto(texto: str) -> str:
    """
    Remove espaços extras, quebras de linha excessivas e caracteres especiais indesejados do texto.
    """
    if not isinstance(texto, str):
        return ""

    # Remove quebras de linha duplicadas e espaços em excesso
    texto_limpo = re.sub(r'\s+', ' ', texto)

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

    for interacao in dadosbrutos.get("interacoes", []):
        # Valida se os campos essenciais existem e limpa o texto
        autor = limpar_texto(interacao.get("autor", "Desconhecido"))
        canal = limpar_texto(interacao.get("canal", "#geral"))
        tipo = limpar_texto(interacao.get("tipo", "interacao_geral"))
        texto = limpar_texto(interacao.get("texto", ""))

        # Ignora interações que estejam com o texto totalmente vazio
        if texto:
            interacao_limpa = {}

            # Preserva o id (quando existir) para rastrear a mensagem até o resultado
            id_mensagem = limpar_texto(str(interacao.get("id", "")))
            if id_mensagem:
                interacao_limpa["id"] = id_mensagem

            interacao_limpa.update({
                "autor": autor if autor else "Desconhecido",
                "canal": canal if canal else "#geral",
                "tipo": tipo if tipo else "interacao_geral",
                "texto": texto
            })
            interacoes_limpas.append(interacao_limpa)

    dados_tratados["interacoes"] = interacoes_limpas

    return dados_tratados