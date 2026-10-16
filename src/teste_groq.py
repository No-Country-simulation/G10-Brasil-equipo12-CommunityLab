import os
from dotenv import load_dotenv
from groq import Groq

# Carrega as variáveis do arquivo .env
load_dotenv()

# Inicializa o cliente da Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Faz a requisição usando o modelo liberado para sua chave
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Olá! Se você está funcionando, responda apenas: Funcionando com sucesso!",
        }
    ],
)

# Imprime a resposta da IA
print(response.choices[0].message.content)
