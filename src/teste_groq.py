import os

from dotenv import load_dotenv
from groq import Groq

MODELO = "openai/gpt-oss-120b"


def testar_groq() -> int:
    load_dotenv()
    chave = os.getenv("GROQ_API_KEY")
    if not chave:
        print("GROQ_API_KEY não encontrada. Crie o arquivo .env (veja .env.example).")
        return 1

    client = Groq(api_key=chave)

    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {
                    "role": "user",
                    "content": "Olá! Se você está funcionando, responda apenas: Funcionando com sucesso!",
                }
            ],
        )
        print(response.choices[0].message.content)
        return 0
    except Exception as erro:
        print(f"Erro ao chamar a Groq: {erro}")
        return 1


# Só chama a API quando executado direto (python -m src.teste_groq), não ao ser importado
if __name__ == "__main__":
    raise SystemExit(testar_groq())
