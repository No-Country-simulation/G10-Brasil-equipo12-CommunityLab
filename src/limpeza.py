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

def _chave_duplicata(autor: str, canal: str, texto: str) -> tuple:
    """Duas mensagens são duplicadas quando têm o mesmo autor, o mesmo canal e o mesmo texto.
    Maiúsculas e minúsculas não contam (os espaços já foram padronizados por limpar_texto).
    Mesmo texto de autores diferentes NÃO é duplicata: são pessoas diferentes participando."""
    return (autor.casefold(), canal.casefold(), texto.casefold())


def limpar_dados_comunidade(dadosbrutos: dict) -> dict:
    """
    Recebe o dicionário bruto lido do JSON/CSV e aplica regras de limpeza
    em todas as interações da comunidade: padroniza o texto, descarta mensagens
    vazias e descarta duplicatas (fica a primeira ocorrência, na ordem original).
    """
    # Cria uma cópia para não alterar o dicionário original diretamente
    dados_tratados = dadosbrutos.copy()
    interacoes_limpas = []
    vistas = set()

    for interacao in dadosbrutos.get("interacoes", []):
        # Valida se os campos essenciais existem e limpa o texto
        autor = limpar_texto(interacao.get("autor", "Desconhecido"))
        canal = limpar_texto(interacao.get("canal", "#geral"))
        tipo = limpar_texto(interacao.get("tipo", "interacao_geral"))
        texto = limpar_texto(interacao.get("texto", ""))

        # Ignora interações que estejam com o texto totalmente vazio
        if texto:
            # Ignora duplicatas: mantém só a primeira vez que a mensagem aparece
            chave = _chave_duplicata(autor, canal, texto)
            if chave in vistas:
                continue
            vistas.add(chave)

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


AUTOR_ANONIMO = "Participante"


def anonimizar_conversas_gerais(interacoes: list[dict]) -> list[dict]:
    """
    Troca o autor por "Participante" nas mensagens do tipo interacao_geral.

    Conversa geral não gera nenhum ativo (regras_roteamento.md), então o nome de quem
    escreveu não precisa chegar à LLM. Isso protege relatos pessoais classificados como
    conversa geral, sem depender só do prompt. Roda depois da limpeza (que usa o autor para
    achar duplicatas) e da amostra. Devolve cópias: a lista original não é alterada.

    Limite conhecido: um nome escrito dentro do próprio texto da mensagem não é removido.
    """
    return [
        {**i, "autor": AUTOR_ANONIMO} if (i.get("tipo") or "").strip().casefold() == "interacao_geral" else dict(i)
        for i in interacoes
    ]
