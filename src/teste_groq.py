import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODELO = "openai/gpt-oss-120b"

chave = os.getenv("GROQ_API_KEY")
if not chave:
    raise SystemExit("GROQ_API_KEY não encontrada. Crie o arquivo .env (veja .env.example).")

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
except Exception as erro:
    print(f"Erro ao chamar a Groq: {erro}")