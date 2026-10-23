# src/pipeline.py
import json

from src.limpeza import limpar_dados_comunidade
from src.llm import chamar_llm as chamar_llm_configurada
from src.prompts import SYSTEM_PROMPT_ANALISE, construir_prompt_usuario
from src.validacao import validar_e_tratar_json


def executar_pipeline(dados_brutos: dict, chamar_llm=None) -> dict:
    """
    Limpa as interações, envia para a LLM e devolve o JSON validado.
    `chamar_llm(system_prompt, prompt_usuario) -> str` pode ser trocada (ex.: nos testes).
    Falhas não levantam exceção: voltam com status "erro" e o motivo em "avisos".
    """
    dados_limpos = limpar_dados_comunidade(dados_brutos)
    if not dados_limpos["interacoes"]:
        resultado = validar_e_tratar_json({}, dados_limpos)
        resultado["avisos"] = ["nenhuma interação com texto após a limpeza"]
        return resultado

    chamar_llm = chamar_llm or chamar_llm_configurada
    try:
        resposta_texto = chamar_llm(SYSTEM_PROMPT_ANALISE, construir_prompt_usuario(dados_limpos))
    except Exception as erro:
        resultado = validar_e_tratar_json({}, dados_limpos)
        resultado["avisos"] = [f"falha ao chamar a LLM: {erro}"]
        return resultado

    try:
        dados_llm = json.loads(resposta_texto)
    except (json.JSONDecodeError, TypeError):
        dados_llm = None

    resultado = validar_e_tratar_json(dados_llm, dados_limpos)
    if dados_llm is None:
        resultado["avisos"] = ["a LLM não retornou um JSON válido"]
    return resultado
