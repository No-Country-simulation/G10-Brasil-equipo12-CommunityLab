# src/llm.py
import os

MODELO_GROQ_PADRAO = "openai/gpt-oss-120b"


def chamar_llm(system_prompt: str, prompt_usuario: str) -> str:
    """Envia o prompt para a LLM (Groq) e devolve o texto da resposta."""
    return _chamar_groq(system_prompt, prompt_usuario)


def _mensagens(system_prompt: str, prompt_usuario: str) -> list:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_usuario},
    ]


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
