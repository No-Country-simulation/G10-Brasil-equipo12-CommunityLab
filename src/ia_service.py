# src/ia_service.py
"""Chamada à LLM (Groq) com nova tentativa quando a resposta vem fora do formato."""
import os

from dotenv import load_dotenv

from src.prompts import SYSTEM_PROMPT_ANALISE, construir_prompt_usuario
from src.schemas import AnaliseLLM
from src.validacao import ErroAnaliseLLM, validar_analise_llm

MODELO = "openai/gpt-oss-120b"
TEMPERATURA = 0.2


class ErroServicoLLM(RuntimeError):
    """Falha ao falar com a API da LLM (chave ausente ou inválida, rede, limite de uso)."""


def _criar_cliente():
    load_dotenv(override=True)  # o .env do projeto vence variáveis já definidas no terminal
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ErroServicoLLM("A variável GROQ_API_KEY não foi encontrada. Confira o arquivo .env.")
    from groq import Groq  # importado aqui para o resto do projeto rodar sem a biblioteca

    return Groq(api_key=api_key)


def analisar_lote(dados_limpos: dict, tentativas: int = 3, cliente=None) -> AnaliseLLM:
    """Envia o lote limpo à LLM e devolve a análise validada.

    Se a resposta vier fora do formato, tenta de novo (até `tentativas`), contando à LLM
    qual foi o erro. Se continuar falhando, levanta ErroAnaliseLLM.
    Erros da API (chave, rede, limite) levantam ErroServicoLLM e não são repetidos aqui:
    a biblioteca da Groq já faz as próprias tentativas para falhas de conexão.

    `cliente` existe para testes (permite passar um cliente falso).
    """
    if cliente is None:
        cliente = _criar_cliente()

    prompt_base = construir_prompt_usuario(dados_limpos)
    ultimo_erro = None

    for _ in range(max(1, tentativas)):
        prompt = prompt_base
        if ultimo_erro is not None:
            prompt += (
                "\n\nATENÇÃO: a sua resposta anterior foi recusada. Responda de novo, "
                "apenas com o JSON no formato definido. Motivo da recusa:\n" + str(ultimo_erro)
            )
        try:
            resposta = cliente.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ANALISE},
                    {"role": "user", "content": prompt},
                ],
                model=MODELO,
                temperature=TEMPERATURA,
                response_format={"type": "json_object"},
            )
            texto = resposta.choices[0].message.content
        except Exception as erro:
            raise ErroServicoLLM(f"Falha ao chamar a API da Groq ({type(erro).__name__}): {erro}") from erro

        try:
            return validar_analise_llm(texto)
        except ErroAnaliseLLM as erro:
            ultimo_erro = erro

    raise ErroAnaliseLLM(
        f"A LLM não devolveu um formato válido em {max(1, tentativas)} tentativa(s). Último erro: {ultimo_erro}"
    )
