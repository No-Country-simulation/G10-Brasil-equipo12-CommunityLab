import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq

from src.ingestao import ler_mensagens_comunidade
from src.limpeza import limpar_dados_comunidade
from src.oracle_storage import BUCKET_PADRAO, montar_caminho
from src.prompts import SYSTEM_PROMPT_ANALISE, construir_prompt_usuario
from src.schemas import ArmazenamentoOci, LoteEntrada, montar_resposta
from src.validacao import ErroAnaliseLLM, validar_analise_llm

# override=True: o .env do projeto vence qualquer variável já definida no terminal
load_dotenv(override=True)

MODELO = "openai/gpt-oss-120b"


def testar_pipeline_com_validacao(caminho_arquivo: str = "dados/mensagens_exemplo.json"):
    print(f"1. Lendo e validando o arquivo: {caminho_arquivo}")
    dados_brutos = ler_mensagens_comunidade(caminho_arquivo)

    print("2. Aplicando a limpeza nos dados...")
    dados_limpos = limpar_dados_comunidade(dados_brutos)
    if not dados_limpos["interacoes"]:
        print("❌ Nenhuma interação com texto sobrou depois da limpeza.")
        return
    lote = LoteEntrada.model_validate(dados_limpos)

    print(f"3. Enviando {len(lote.interacoes)} interações para a API da Groq (Modelo: {MODELO})...")
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ Erro: A variável GROQ_API_KEY não foi encontrada!")
        return

    try:
        client = Groq(api_key=api_key)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ANALISE},
                {"role": "user", "content": construir_prompt_usuario(dados_limpos)},
            ],
            model=MODELO,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        resposta_texto = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Erro ao chamar a API da Groq: {e}")
        return

    # 4. Validação estrita: sem valores inventados quando a LLM erra
    try:
        analise = validar_analise_llm(resposta_texto)
    except ErroAnaliseLLM as e:
        print(f"❌ {e}")
        print("Resposta recebida (primeiros 500 caracteres):")
        print((resposta_texto or "")[:500])
        return

    # 5. Contagem e bloco do OCI vêm do código, não da LLM
    oci = ArmazenamentoOci(
        bucket=os.getenv("OCI_BUCKET", BUCKET_PADRAO),
        caminho_objeto=montar_caminho(lote.periodo_referencia),
        status="pendente_upload",
    )
    resposta = montar_resposta(lote, analise, oci)

    print("✅ Sucesso! Resposta validada no formato do PDF:")
    print(json.dumps(resposta.para_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # Uso: python -m src.teste_execucao [caminho_do_arquivo.json]
    testar_pipeline_com_validacao(*sys.argv[1:2])