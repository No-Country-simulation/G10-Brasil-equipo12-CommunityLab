# src/ia_service.py
"""Chamada à LLM (Groq) com nova tentativa quando a resposta vem fora do formato."""
import os

from dotenv import load_dotenv

from src.prompts import SYSTEM_PROMPT_ANALISE, construir_prompt_usuario
from src.schemas import AnaliseLLM
from src.validacao import ErroAnaliseLLM, validar_analise_llm
from src.utils.prompt_loader import carregar_guia_prompt

MODELO = "openai/gpt-oss-120b"
TEMPERATURA = 0.2


# Vem depois dos guias de propósito: o que a LLM lê por último pesa mais.
LEMBRETE_FINAL = (
    "PRECEDÊNCIA: os guias acima definem apenas TOM e ESTRUTURA de cada canal. "
    "Se algum guia conflitar com as REGRAS GERAIS ou com o FORMATO DE SAÍDA definidos no início, "
    "valem as REGRAS GERAIS e o FORMATO DE SAÍDA. Use somente fatos que aparecem nas mensagens, "
    "não aumente conquistas, não invente soluções, números ou nomes, e responda apenas com o JSON "
    "no formato definido (use null no ativo que não tiver material). Os exemplos dos guias mostram apenas "
    "estilo e estrutura: nunca copie nomes, fatos, tecnologias ou resultados deles."
)


class ErroServicoLLM(RuntimeError):
    """Falha ao falar com a API da LLM (chave ausente ou inválida, rede, limite de uso)."""


def _criar_cliente():
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ErroServicoLLM("A variável GROQ_API_KEY não foi encontrada. Confira o arquivo .env.")
    from groq import Groq

    return Groq(api_key=api_key)


def analisar_lote(dados_limpos: dict, tentativas: int = 3, cliente=None) -> AnaliseLLM:
    """Envia o lote limpo à LLM e devolve a análise validada."""
    if cliente is None:
        cliente = _criar_cliente()

    # 1. Carrega dinamicamente os guias de tom de voz salvos na pasta /prompts
    prompt_linkedin = carregar_guia_prompt("linkedin")
    prompt_newsletter = carregar_guia_prompt("newsletter")
    prompt_faq = carregar_guia_prompt("faq")

    # 2. Consolida o system prompt base da aplicação com os guias de canais
    system_prompt_consolidado = f"""
{SYSTEM_PROMPT_ANALISE}

---
DIRETRIZES DE TOM DE VOZ POR CANAL (USE-AS PARA GERAR OS ATIVOS):

[GUIA LINKEDIN]
{prompt_linkedin}

[GUIA NEWSLETTER]
{prompt_newsletter}

[GUIA FAQ]
{prompt_faq}

---
{LEMBRETE_FINAL}
"""

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
                    # 3. Injeta o system prompt consolidado contendo os guias de /prompts
                    {"role": "system", "content": system_prompt_consolidado},
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