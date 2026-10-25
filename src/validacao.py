# src/validacao.py
import json
import re

from pydantic import ValidationError

from src.schemas import AnaliseLLM


class ErroAnaliseLLM(ValueError):
    """A resposta da LLM não pôde ser usada (JSON quebrado ou fora do formato).

    Não existe mais valor de segurança (fallback): conteúdo inventado com
    status "sucesso" esconde o erro. Quem chama decide: tentar de novo ou registrar a falha.
    """


# Caracteres invisíveis ou "especiais" que a LLM às vezes usa no lugar dos comuns.
# A troca é feita DEPOIS de decodificar o JSON, porque a LLM pode devolvê-los
# tanto como caractere quanto como escape (\u2011).
_TROCAS_DE_CARACTERES = {
    0x2011: "-",   # hífen sem quebra
    0x00A0: " ",   # espaço sem quebra
    0x202F: " ",   # espaço fino sem quebra
    0x200B: None,  # espaço de largura zero (remove)
}


def _normalizar_caracteres(valor):
    """Percorre o JSON já decodificado e troca os caracteres especiais em todos os textos."""
    if isinstance(valor, str):
        return valor.translate(_TROCAS_DE_CARACTERES)
    if isinstance(valor, list):
        return [_normalizar_caracteres(item) for item in valor]
    if isinstance(valor, dict):
        return {chave: _normalizar_caracteres(item) for chave, item in valor.items()}
    return valor


def _remover_cercas_markdown(texto: str) -> str:
    """Aceita a resposta embrulhada em ```json ... ``` (a LLM às vezes faz isso)."""
    limpo = texto.strip()
    achado = re.match(r"^```(?:json)?\s*(.*?)\s*```$", limpo, flags=re.DOTALL | re.IGNORECASE)
    return achado.group(1) if achado else limpo


def validar_analise_llm(texto_resposta: str) -> AnaliseLLM:
    """Converte o texto devolvido pela LLM em AnaliseLLM ou levanta ErroAnaliseLLM."""
    if not isinstance(texto_resposta, str) or not texto_resposta.strip():
        raise ErroAnaliseLLM("A LLM devolveu uma resposta vazia.")

    try:
        dados = _normalizar_caracteres(json.loads(_remover_cercas_markdown(texto_resposta)))
    except json.JSONDecodeError as erro:
        raise ErroAnaliseLLM(
            f"A resposta da LLM não é um JSON válido ({erro.msg}, linha {erro.lineno}, coluna {erro.colno})."
        ) from erro

    try:
        return AnaliseLLM.model_validate(dados)
    except ValidationError as erro:
        linhas = []
        for e in erro.errors():
            campo = ".".join(str(parte) for parte in e["loc"]) or "(resposta inteira)"
            linhas.append(f"  - {campo}: {e['msg']}")
        raise ErroAnaliseLLM("A resposta da LLM está fora do formato esperado:\n" + "\n".join(linhas)) from erro
