import os
import json
from dotenv import load_dotenv
from groq import Groq

from src.ingestao import ler_mensagens_comunidade 
from src.limpeza import limpar_dados_comunidade
from src.prompts import SYSTEM_PROMPT_ANALISE, construir_prompt_usuario
from src.validacao import validar_e_tratar_json  # Importa a validação

load_dotenv()

def testar_pipeline_com_validacao():
    print("1. Lendo o arquivo JSON...")
    dados_brutos = ler_mensagens_comunidade("dados/mensagens_exemplo.json")
    
    print("2. Aplicando a limpeza nos dados...")
    dados_limpos = limpar_dados_comunidade(dados_brutos)
    
    print("3. Enviando para a API da Groq (Modelo: openai/gpt-oss-120b)...")
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ Erro: A variável GROQ_API_KEY não foi encontrada!")
        return

    try:
        client = Groq(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ANALISE},
                {"role": "user", "content": construir_prompt_usuario(dados_limpos)}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        resposta_texto = chat_completion.choices[0].message.content
        
        # Tenta converter o texto em JSON
        try:
            dados_brutos_llm = json.loads(resposta_texto)
        except json.JSONDecodeError:
            print("⚠️ Aviso: A LLM retornou um formato inválido. Acionando tratamento de fallback...")
            dados_brutos_llm = {}

        # 4. Aplica a validação e tratamento de falhas
        dados_finais = validar_e_tratar_json(dados_brutos_llm)
        
        print("✅ Sucesso! JSON validado e tratado com segurança:")
        print(json.dumps(dados_finais, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Erro crítico ao processar o pipeline: {e}")

if __name__ == "__main__":
    testar_pipeline_com_validacao()