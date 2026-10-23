# src/llm.py
import json
import os
import urllib.error
import urllib.request

MODELO_GROQ_PADRAO = "openai/gpt-oss-120b"
MODELO_NVIDIA_PADRAO = "openai/gpt-oss-20b"
URL_NVIDIA_PADRAO = "https://integrate.api.nvidia.com/v1"


def chamar_llm(system_prompt: str, prompt_usuario: str) -> str:
    """
    Envia o prompt para a LLM configurada no .env e devolve o texto da resposta.
    LLM_PROVIDER=groq (padrão) usa a API da Groq; LLM_PROVIDER=nvidia usa a API da NVIDIA
    (build.nvidia.com); LLM_PROVIDER=ollama usa um modelo local, útil para testar sem chave de API.
    """
    provedor = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if provedor == "groq":
        return _chamar_groq(system_prompt, prompt_usuario)
    if provedor == "nvidia":
        return _chamar_nvidia(system_prompt, prompt_usuario)
    if provedor == "ollama":
        return _chamar_ollama(system_prompt, prompt_usuario)
    raise ValueError(f"LLM_PROVIDER desconhecido: {provedor}. Use 'groq', 'nvidia' ou 'ollama'.")


def _mensagens(system_prompt: str, prompt_usuario: str) -> list:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_usuario},
    ]


def _post_json(url: str, corpo: dict, cabecalhos: dict, timeout: int, segredo: str = "") -> dict:
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json", **cabecalhos},
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        # O corpo do erro explica o motivo (modelo inexistente, chave inválida...).
        # Lê só o começo e mascara a chave, caso o servidor a repita na mensagem.
        detalhe = erro.read(2000).decode("utf-8", "replace")[:300]
        if segredo:
            detalhe = detalhe.replace(segredo, "***")
        raise RuntimeError(f"{url} respondeu {erro.code}: {detalhe}") from erro


def _chamar_groq(system_prompt: str, prompt_usuario: str) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não encontrada. Crie o arquivo .env (veja .env.example).")

    client = Groq(api_key=api_key)
    chat_completion = client.chat.completions.create(
        messages=_mensagens(system_prompt, prompt_usuario),
        model=os.getenv("GROQ_MODEL", MODELO_GROQ_PADRAO),
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return chat_completion.choices[0].message.content


def _chamar_nvidia(system_prompt: str, prompt_usuario: str) -> str:
    # A API da NVIDIA segue o formato de chat da OpenAI
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY não encontrada. Gere uma chave em build.nvidia.com (veja .env.example).")

    url = os.getenv("NVIDIA_URL", URL_NVIDIA_PADRAO).rstrip("/") + "/chat/completions"
    corpo = {
        "model": os.getenv("NVIDIA_MODEL", MODELO_NVIDIA_PADRAO),
        "messages": _mensagens(system_prompt, prompt_usuario),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        # Sem limite explícito, respostas longas podem vir cortadas
        "max_tokens": 4096,
    }
    resposta = _post_json(url, corpo, {"Authorization": f"Bearer {api_key}"}, timeout=180, segredo=api_key)
    return resposta["choices"][0]["message"]["content"]


def _chamar_ollama(system_prompt: str, prompt_usuario: str) -> str:
    modelo = os.getenv("OLLAMA_MODEL")
    if not modelo:
        raise RuntimeError("OLLAMA_MODEL não definido. Informe no .env o modelo local (veja .env.example).")

    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
    corpo = {
        "model": modelo,
        "messages": _mensagens(system_prompt, prompt_usuario),
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2},
    }
    return _post_json(url, corpo, {}, timeout=600)["message"]["content"]
