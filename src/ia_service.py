# src/ia_service.py
"""Chamada à LLM (Groq) com nova tentativa quando a resposta vem fora do formato."""
import os
from typing import Optional, Sequence

from dotenv import load_dotenv

from src.prompts import construir_prompt_usuario, montar_system_prompt_analise
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


# Canal de cada ativo: nome do guia em /prompts e título dele no system prompt
_GUIAS = {
    "post_linkedin": ("linkedin", "[GUIA LINKEDIN]"),
    "destaque_newsletter_semanal": ("newsletter", "[GUIA NEWSLETTER]"),
    "sugestao_conteudo_faq": ("faq", "[GUIA FAQ]"),
}


def montar_system_prompt(ativos: Optional[Sequence[str]] = None) -> str:
    """System prompt completo: regras gerais, guias de tom só dos ativos pedidos e lembrete final.
    ativos=None pede os três. Sem nenhum ativo, não há guia: a LLM só devolve sentimento e tópicos."""
    base = montar_system_prompt_analise(ativos)
    pedidos = [a for a in _GUIAS if ativos is None or a in set(ativos)]

    # Carrega dinamicamente os guias de tom de voz salvos na pasta /prompts
    blocos = "".join(f"\n{titulo}\n{carregar_guia_prompt(canal)}\n" for canal, titulo in (_GUIAS[a] for a in pedidos))
    if not pedidos:
        return f"\n{base}"  # sem guias, o lembrete sobre eles não tem o que lembrar; valem as REGRAS GERAIS
    guias = f"\n\n---\nDIRETRIZES DE TOM DE VOZ POR CANAL (USE-AS PARA GERAR OS ATIVOS):\n{blocos}"
    return f"\n{base}{guias}\n---\n{LEMBRETE_FINAL}\n"


def analisar_lote(dados_limpos: dict, tentativas: int = 3, cliente=None, ativos: Optional[Sequence[str]] = None) -> AnaliseLLM:
    """Envia o lote limpo à LLM e devolve a análise validada.

    ativos: quais ativos pedir (src/roteamento.py -> ativos_com_material). None pede os três.
    Os que não forem pedidos não entram no prompt e vêm `null` na análise."""
    if cliente is None:
        cliente = _criar_cliente()

    system_prompt_consolidado = montar_system_prompt(ativos)

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