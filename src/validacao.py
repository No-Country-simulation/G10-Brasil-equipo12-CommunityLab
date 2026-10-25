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
        dados = json.loads(_remover_cercas_markdown(texto_resposta))
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